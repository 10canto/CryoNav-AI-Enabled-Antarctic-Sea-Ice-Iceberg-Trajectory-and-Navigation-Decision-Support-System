#!/usr/bin/env python3
"""AMA-7: 24-hour evaluation on the 11 approved unseen icebergs.

Compares the existing AMA-8 ML inference, the AMA-6 physics baseline,
and a zero-velocity baseline on identical, leakage-safe evaluation rows.
No model training is performed.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn

# Intended location: iceberg-trajectory-ml/scripts/ama7_evaluate.py
SCRIPT_DIR = Path(__file__).resolve().parent
ML_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from ama8_inference import predict_iceberg_position  # noqa: E402

TEST_ICEBERGS = (
    "A78", "B09I", "B39", "D21B", "D27", "D28",
    "D29A", "D29B", "D29C", "D30A", "D30B",
)
START_DATE = pd.Timestamp("2018-01-01")
END_DATE_EXCLUSIVE = pd.Timestamp("2022-01-01")
HORIZON_HOURS = 24.0
DATA_DIR = ML_DIR / "data" / "validation"
TRAINING_TABLE = DATA_DIR / "training_table.csv"
MANIFEST_PATH = DATA_DIR / "ama6_split_manifest.json"
MODEL_CONFIG_PATH = DATA_DIR / "model_config.json"
MODEL_DIR = DATA_DIR
RESULTS_DIR = ML_DIR / "results"
PAIR_RESULTS_PATH = RESULTS_DIR / "ama7_evaluation_per_pair.csv"
PER_ICEBERG_PATH = RESULTS_DIR / "ama7_evaluation_per_iceberg.csv"
REPORT_PATH = RESULTS_DIR / "ama7_evaluation.md"
FORCING_COLUMNS = ("uo", "vo", "siconc", "usi", "vsi", "u10", "v10")
NUMERIC_COLUMNS = (
    "dt_days", "lat", "lon", "lat_next", "lon_next", *FORCING_COLUMNS
)


def parse_bool(series: pd.Series) -> pd.Series:
    """Parse CSV booleans without treating the text 'False' as True."""
    return series.astype(str).str.strip().str.lower().isin({"true", "1", "yes", "y"})


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres."""
    radius_km = 6371.0088
    lat1_r, lon1_r, lat2_r, lon2_r = map(
        math.radians, (lat1, lon1, lat2, lon2)
    )
    dlat, dlon = lat2_r - lat1_r, lon2_r - lon1_r
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2.0) ** 2
    )
    a = min(1.0, max(0.0, a))
    return radius_km * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def move_from_velocity(
    lat: float, lon: float, east_mps: float, north_mps: float
) -> tuple[float, float]:
    """Integrate east/north velocity for 24h using AMA-8's local conversion."""
    seconds = HORIZON_HOURS * 3600.0
    dx_m, dy_m = east_mps * seconds, north_mps * seconds
    cos_lat = math.cos(math.radians(lat))
    if abs(cos_lat) < 1e-10:
        raise ValueError(f"Cannot convert longitude displacement near pole: lat={lat}")
    predicted_lat = lat + dy_m / 111_000.0
    predicted_lon = lon + dx_m / (111_000.0 * cos_lat)
    predicted_lon = ((predicted_lon + 180.0) % 360.0) - 180.0
    return predicted_lat, predicted_lon


def validate_manifest() -> None:
    """Verify every selected ID is test-only and not spatially held out."""
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Split manifest not found: {MANIFEST_PATH}")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    temporal = manifest.get("temporal_split", {})
    spatial = manifest.get("spatial_split", {})
    test_only = {str(x).strip().upper() for x in temporal.get("test_only_ids", [])}
    train_only = {str(x).strip().upper() for x in temporal.get("train_only_ids", [])}
    both_periods = {str(x).strip().upper() for x in temporal.get("both_periods_ids", [])}
    spatial_held_out = {str(x).strip().upper() for x in spatial.get("held_out_ids", [])}
    selected = set(TEST_ICEBERGS)

    missing = sorted(selected - test_only)
    training_overlap = sorted(selected & (train_only | both_periods))
    spatial_overlap = sorted(selected & spatial_held_out)
    if missing:
        raise ValueError("IDs absent from manifest test_only_ids: " + ", ".join(missing))
    if training_overlap:
        raise ValueError("IDs overlap training/both-period groups: " + ", ".join(training_overlap))
    if spatial_overlap:
        raise ValueError("IDs overlap AMA-6 spatial hold-out: " + ", ".join(spatial_overlap))
    print("Leakage manifest check: PASS (11 test-only IDs; zero spatial hold-out overlap)")


def load_evaluation_rows() -> pd.DataFrame:
    """Load common, complete, non-outlier 24h pairs dated within 2018-2021."""
    for path in (TRAINING_TABLE, MODEL_CONFIG_PATH, MODEL_DIR / "drift_model.pkl"):
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}")

    config = json.loads(MODEL_CONFIG_PATH.read_text(encoding="utf-8"))
    if config.get("model_file") != "drift_model.pkl":
        raise ValueError(f"Unexpected configured model file: {config.get('model_file')!r}")
    if config.get("data_provenance", {}).get("synthetic", False):
        raise ValueError("ABORT: model configuration marks its training data as synthetic")
    if sklearn.__version__ != "1.8.0":
        raise RuntimeError(
            "Run with the isolated AMA-7 environment (scikit-learn 1.8.0); "
            f"current version is {sklearn.__version__}."
        )
    print(f"scikit-learn version: {sklearn.__version__}")

    df = pd.read_csv(TRAINING_TABLE)
    required = {
        "iceberg_id", "date", "date_next", "complete_case", "outlier_flag",
        *NUMERIC_COLUMNS,
    }
    missing_cols = sorted(required - set(df.columns))
    if missing_cols:
        raise ValueError("Missing training-table columns: " + ", ".join(missing_cols))

    df["iceberg_id"] = df["iceberg_id"].astype(str).str.strip().str.upper()
    df["date_parsed"] = pd.to_datetime(df["date"], errors="coerce")
    df["date_next_parsed"] = pd.to_datetime(df["date_next"], errors="coerce")
    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    selected = df["iceberg_id"].isin(TEST_ICEBERGS)
    dates_inside_period = (
        (df["date_parsed"] >= START_DATE)
        & (df["date_parsed"] < END_DATE_EXCLUSIVE)
        & (df["date_next_parsed"] >= START_DATE)
        & (df["date_next_parsed"] < END_DATE_EXCLUSIVE)
    )
    calendar_gap_days = (
        df["date_next_parsed"] - df["date_parsed"]
    ).dt.total_seconds() / 86400.0
    exact_24h = (
        np.isclose(df["dt_days"], 1.0, rtol=0.0, atol=1e-6)
        & np.isclose(calendar_gap_days, 1.0, rtol=0.0, atol=1e-6)
    )
    complete = parse_bool(df["complete_case"])
    outlier_flag_known = df["outlier_flag"].notna()
    is_outlier = parse_bool(df["outlier_flag"])
    forcing_present = df[
        ["lat", "lon", "lat_next", "lon_next", *FORCING_COLUMNS]
    ].notna().all(axis=1)

    evaluation = df.loc[
        selected
        & dates_inside_period
        & exact_24h
        & complete
        & outlier_flag_known
        & ~is_outlier
        & forcing_present
    ].copy()
    if evaluation.empty:
        raise RuntimeError("No eligible evaluation rows remain after filtering.")
    
    # Validate sea-ice concentration with a small numerical tolerance.
    siconc = pd.to_numeric(evaluation["siconc"], errors="coerce")

    if siconc.isna().any():
        raise ValueError("Missing or non-numeric siconc values were found.")

    siconc_tolerance = 0.0001

    outside_tolerance = (
        (siconc < -siconc_tolerance)
        | (siconc > 1.0 + siconc_tolerance)
    )

    if outside_tolerance.any():
        raise ValueError(
            "siconc values exceed the allowed numerical tolerance. "
            f"Minimum={siconc.min()}, Maximum={siconc.max()}"
        )

    # Correct only tiny floating-point boundary overshoots.
    siconc_clipped_count = int(
        ((siconc < 0.0) | (siconc > 1.0)).sum()
    )

    evaluation.loc[:, "siconc"] = siconc.clip(0.0, 1.0)

    print( 
        f"siconc numerical boundary corrections: "
        f"{siconc_clipped_count}"
    )

    if (evaluation["lat"].abs() > 90).any() or (evaluation["lat_next"].abs() > 90).any():
        raise ValueError("Latitude outside [-90, 90] was found in the evaluation rows.")

    found_ids = set(evaluation["iceberg_id"])
    missing_ids = sorted(set(TEST_ICEBERGS) - found_ids)
    if missing_ids:
        raise RuntimeError(
            "Approved icebergs with no eligible complete 24h pairs: " + ", ".join(missing_ids)
        )
    duplicate = evaluation.duplicated(["iceberg_id", "date_parsed", "date_next_parsed"])
    if duplicate.any():
        sample = evaluation.loc[duplicate, ["iceberg_id", "date", "date_next"]].head(10)
        raise RuntimeError("Duplicate iceberg/date pairs detected:\n" + sample.to_string(index=False))

    evaluation = evaluation.sort_values(["iceberg_id", "date_parsed"]).reset_index(drop=True)
    print(f"Training-table rows: {len(df):,}")
    print(f"Eligible 24h evaluation pairs: {len(evaluation):,}")
    print(f"Eligible icebergs: {evaluation['iceberg_id'].nunique()}")
    print(
        "Evaluation span: "
        f"{evaluation['date_parsed'].min().date()} to "
        f"{evaluation['date_next_parsed'].max().date()}"
    )
    return evaluation


def evaluate_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Generate all three predictions on exactly the same rows."""
    records: list[dict] = []
    total = len(df)
    for index, row in df.iterrows():
        iceberg_id = row["iceberg_id"]
        date_text = row["date_parsed"].strftime("%Y-%m-%d")
        lat, lon = float(row["lat"]), float(row["lon"])
        actual_lat, actual_lon = float(row["lat_next"]), float(row["lon_next"])
        ocean_u, ocean_v = float(row["uo"]), float(row["vo"])
        siconc = float(row["siconc"])
        ice_u, ice_v = float(row["usi"]), float(row["vsi"])
        wind_u, wind_v = float(row["u10"]), float(row["v10"])

        # Use the corrected AMA-8 inference interface; date auto-extracts month.
        try:
            ml = predict_iceberg_position(
                lat=lat,
                lon=lon,
                ocean_u=ocean_u,
                ocean_v=ocean_v,
                wind_u=wind_u,
                wind_v=wind_v,
                siconc=siconc,
                ice_u=ice_u,
                ice_v=ice_v,
                dt_hours=HORIZON_HOURS,
                model_dir=str(MODEL_DIR),
                date=date_text,
            )
            ml_lat, ml_lon = float(ml["predicted_lat"]), float(ml["predicted_lon"])
        except Exception as exc:
            raise RuntimeError(
                f"ML inference failed for {iceberg_id} on {date_text}; stopped to keep "
                f"a common evaluation sample. Original error: {exc}"
            ) from exc

        # Exact AMA-6 compute_physics_baseline coefficients.
        ice_weight = float(np.clip((siconc - 0.6) / 0.3, 0.0, 1.0))
        physics_u = 0.9 * ocean_u + 0.2 * ice_u * ice_weight + 0.02 * wind_u
        physics_v = 0.9 * ocean_v + 0.2 * ice_v * ice_weight + 0.02 * wind_v
        physics_lat, physics_lon = move_from_velocity(lat, lon, physics_u, physics_v)

        # Zero-velocity baseline: forecast remains at the initial position.
        zero_lat, zero_lon = lat, lon
        errors = {
            "ml_error_km": haversine_km(actual_lat, actual_lon, ml_lat, ml_lon),
            "physics_error_km": haversine_km(
                actual_lat, actual_lon, physics_lat, physics_lon
            ),
            "zero_velocity_error_km": haversine_km(
                actual_lat, actual_lon, zero_lat, zero_lon
            ),
        }
        if not all(math.isfinite(value) for value in errors.values()):
            raise RuntimeError(f"Non-finite prediction error for {iceberg_id} on {date_text}")

        records.append(
            {
                "iceberg_id": iceberg_id,
                "date": date_text,
                "date_next": row["date_next_parsed"].strftime("%Y-%m-%d"),
                "dt_days": float(row["dt_days"]),
                "lat": lat,
                "lon": lon,
                "actual_lat_next": actual_lat,
                "actual_lon_next": actual_lon,
                "ml_pred_lat": ml_lat,
                "ml_pred_lon": ml_lon,
                "physics_pred_lat": physics_lat,
                "physics_pred_lon": physics_lon,
                "zero_velocity_pred_lat": zero_lat,
                "zero_velocity_pred_lon": zero_lon,
                **errors,
                "ml_uncertainty_radius_p90_km": ml.get("uncertainty_radius_km"),
                "ml_model_version": ml.get("model_version"),
            }
        )
        if (index + 1) % 100 == 0 or index + 1 == total:
            print(f"Predicted {index + 1:,}/{total:,} pairs")
    return pd.DataFrame.from_records(records)


def p75(values: pd.Series) -> float:
    return float(np.percentile(values.to_numpy(dtype=float), 75, method="linear"))


def make_summaries(results: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    models = {
        "ML (AMA-8 inference)": "ml_error_km",
        "Physics (AMA-6 baseline)": "physics_error_km",
        "Zero velocity": "zero_velocity_error_km",
    }
    overall_rows = []
    for model, column in models.items():
        values = results[column]
        overall_rows.append({
            "model": model,
            "n": int(values.count()),
            "mean_km": float(values.mean()),
            "median_km": float(values.median()),
            "p75_km": p75(values),
        })

    per_iceberg_rows = []
    for iceberg_id, group in results.groupby("iceberg_id", sort=True):
        for model, column in models.items():
            values = group[column]
            per_iceberg_rows.append({
                "iceberg_id": iceberg_id,
                "model": model,
                "n": int(values.count()),
                "mean_km": float(values.mean()),
                "median_km": float(values.median()),
                "p75_km": p75(values),
            })
    return pd.DataFrame(overall_rows), pd.DataFrame(per_iceberg_rows)


def write_report(
    results: pd.DataFrame, overall: pd.DataFrame, per_iceberg: pd.DataFrame
) -> None:
    lines = [
        "# AMA-7: 24-hour unseen-iceberg evaluation",
        "",
        "**Evaluation statement:** 11 unseen icebergs, 2018-2021, no training leakage.",
        "",
        "## Evaluation design",
        "",
        f"- Approved test icebergs: {len(TEST_ICEBERGS)}",
        f"- IDs: {', '.join(TEST_ICEBERGS)}",
        "- Evaluation period: 2018-01-01 through 2021-12-31 (both pair dates within period)",
        "- Prediction horizon: 24 hours only",
        "- Models: AMA-8 ML inference, AMA-6 physics baseline, zero-velocity baseline",
        "- Complete cases only; outlier-flagged pairs excluded",
        "- Pair rule: dt_days equals one and calendar difference is exactly one day",
        "- The three models use the same evaluation rows",
        "- Leakage check: IDs verified against AMA-6 manifest test_only_ids",
        "- Spatial check: no overlap with AMA-6 spatial held_out_ids",
        "",
        "## Dataset coverage",
        "",
        f"- Evaluation pairs: {len(results):,}",
        f"- Icebergs represented: {results['iceberg_id'].nunique()}",
        f"- First observation date: {results['date'].min()}",
        f"- Last target date: {results['date_next'].max()}",
        "",
        "## Aggregate error metrics",
        "",
        "Errors are great-circle Haversine distances in kilometres. P75 uses linear interpolation.",
        "",
        "| Model | N | Mean (km) | Median (km) | P75 (km) |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in overall.itertuples(index=False):
        lines.append(
            f"| {row.model} | {row.n} | {row.mean_km:.3f} | "
            f"{row.median_km:.3f} | {row.p75_km:.3f} |"
        )

    lines.extend([
        "",
        "## Per-iceberg metrics",
        "",
        "| Iceberg | Model | N | Mean (km) | Median (km) | P75 (km) |",
        "|---|---|---:|---:|---:|---:|",
    ])
    for row in per_iceberg.itertuples(index=False):
        lines.append(
            f"| {row.iceberg_id} | {row.model} | {row.n} | "
            f"{row.mean_km:.3f} | {row.median_km:.3f} | {row.p75_km:.3f} |"
        )

    lines.extend([
        "",
        "## Method notes and limitations",
        "",
        "- The existing trained AMA-6 model is used through the corrected AMA-8 inference function; no retraining is performed.",
        "- Each ML inference call receives the actual observation date, so the seasonal month feature is date-specific.",
        "- Physics velocities use the AMA-6 coefficients: u = 0.9*uo + 0.2*usi*ice_weight + 0.02*u10; v = 0.9*vo + 0.2*vsi*ice_weight + 0.02*v10; ice_weight = clip((siconc - 0.6)/0.3, 0, 1).",
        "- Physics velocities are integrated for 24 hours using the local coordinate conversion used by the AMA-8 inference module.",
        "- The zero-velocity baseline predicts no displacement from the starting position.",
        "- The inference P90 uncertainty radius is recorded in the pair-level CSV, but is not substituted for the empirical P75 error metric.",
        "- No 48-hour or 72-hour performance claims are reported.",
        "- Results describe this approved 11-iceberg test set, not the full Antarctic iceberg population.",
        "",
        "## Output files",
        "",
        "- Pair-level predictions and errors: `results/ama7_evaluation_per_pair.csv`",
        "- Per-iceberg summary: `results/ama7_evaluation_per_iceberg.csv`",
        "",
    ])
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    print("=" * 72)
    print("AMA-7: 24-HOUR EVALUATION")
    print("=" * 72)
    print("Test icebergs:", ", ".join(TEST_ICEBERGS))
    print("Prediction horizon: 24 hours only\n")

    validate_manifest()
    evaluation_rows = load_evaluation_rows()
    counts = evaluation_rows.groupby("iceberg_id").size().sort_index()
    print("\nEligible pairs per iceberg:")
    for iceberg_id, count in counts.items():
        print(f"  {iceberg_id}: {count}")

    print("\nRunning ML, physics and zero-velocity predictions...")
    results = evaluate_rows(evaluation_rows)
    overall, per_iceberg = make_summaries(results)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results.to_csv(PAIR_RESULTS_PATH, index=False)
    per_iceberg.to_csv(PER_ICEBERG_PATH, index=False)
    write_report(results, overall, per_iceberg)

    print("\nAGGREGATE RESULTS (km):")
    print(overall.to_string(index=False, float_format=lambda value: f"{value:.3f}"))
    print("\nSaved:")
    print(f"  {REPORT_PATH}")
    print(f"  {PAIR_RESULTS_PATH}")
    print(f"  {PER_ICEBERG_PATH}")
    print("\nAMA-7 evaluation completed successfully.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"\nAMA-7 FAILED: {exc}", file=sys.stderr)
        raise
