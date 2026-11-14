#!/usr/bin/env python3
"""
AMA-8 uncertainty handoff generator.

Reads the accepted AMA-7 pair-level predictions and builds a separate
backend handoff directory containing:
  - ama8_uncertainty_config.json
  - ama8_uncertainty_note.md

IMPORTANT:
- Uses predicted_speed_kmd-compatible speed bins, not actual observed speed.
- Reconstructs the exact AMA-8 predicted speed from the saved predicted
  latitude/longitude using the same local 24-hour coordinate conversion
  used in ama8_inference.py.
- Does NOT modify data/validation/model_config.json or the trained model.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
ML_DIR = SCRIPT_DIR.parent
PAIR_CSV = ML_DIR / "results" / "ama7_evaluation_per_pair.csv"
OUT_JSON = SCRIPT_DIR / "ama8_uncertainty_config.json"
OUT_NOTE = SCRIPT_DIR / "ama8_uncertainty_note.md"

EXPECTED_ICEBERGS = {
    "A78", "B09I", "B39", "D21B", "D27", "D28",
    "D29A", "D29B", "D29C", "D30A", "D30B",
}
EXPECTED_PAIRS = 1777

# These thresholds match model_config.json / ama8_inference.py:
# stationary < 2; slow < 5; moderate < 10; otherwise fast.
BANDS = (
    ("stationary", 0.0, 2.0),
    ("slow", 2.0, 5.0),
    ("moderate", 5.0, 10.0),
    ("fast", 10.0, math.inf),
)

MODEL_VERSION = "CryoNav Drift Model v1"


def required_columns() -> set[str]:
    return {
        "iceberg_id",
        "date",
        "date_next",
        "dt_days",
        "lat",
        "lon",
        "ml_pred_lat",
        "ml_pred_lon",
        "ml_error_km",
    }


def reconstruct_predicted_speed_kmd(df: pd.DataFrame) -> pd.Series:
    """
    Reconstruct AMA-8 `predicted_speed_kmd` from its returned coordinates.

    AMA-8 inference uses:
      dlat = v_pred * 86400 / 111000
      dlon = u_pred * 86400 / (111000 * cos(latitude))
      predicted_speed_kmd = hypot(u_pred, v_pred) * 86.4

    For a 24-hour forecast, inverting those coordinate equations gives
    speed (km/day) = hypot(east_displacement_m, north_displacement_m)/1000.
    This is the same local coordinate approximation, not a haversine
    distance to the prediction.
    """
    lat = pd.to_numeric(df["lat"], errors="coerce").to_numpy(dtype=float)
    lon = pd.to_numeric(df["lon"], errors="coerce").to_numpy(dtype=float)
    pred_lat = pd.to_numeric(df["ml_pred_lat"], errors="coerce").to_numpy(dtype=float)
    pred_lon = pd.to_numeric(df["ml_pred_lon"], errors="coerce").to_numpy(dtype=float)
    dt_days = pd.to_numeric(df["dt_days"], errors="coerce").to_numpy(dtype=float)

    if not np.isfinite(np.column_stack([lat, lon, pred_lat, pred_lon, dt_days])).all():
        raise ValueError("Non-finite coordinate or dt_days values found in AMA-7 pair CSV.")
    if np.any(dt_days <= 0):
        raise ValueError("dt_days must be positive.")
    if not np.allclose(dt_days, 1.0, rtol=0.0, atol=1e-6):
        raise ValueError(
            "This handoff is for 24-hour pairs only; found dt_days values other than 1.0."
        )

    # Match the longitude wrapping convention used by ama8_inference.py.
    delta_lon = (pred_lon - lon + 180.0) % 360.0 - 180.0
    east_displacement_m = (
        delta_lon * 111_000.0 * np.cos(np.radians(lat))
    )
    north_displacement_m = (pred_lat - lat) * 111_000.0

    # Exact inverse of the inference module's 24-hour local coordinate transform.
    speed_kmd = np.hypot(east_displacement_m, north_displacement_m) / 1000.0
    return pd.Series(speed_kmd, index=df.index, name="predicted_speed_kmd")


def load_pairs() -> pd.DataFrame:
    if not PAIR_CSV.exists():
        raise FileNotFoundError(
            f"AMA-7 pair CSV not found: {PAIR_CSV}\n"
            "Place this generator in iceberg-trajectory-ml/ama8_handoff/."
        )

    df = pd.read_csv(PAIR_CSV)
    missing = sorted(required_columns() - set(df.columns))
    if missing:
        raise ValueError("AMA-7 pair CSV is missing columns: " + ", ".join(missing))

    df["iceberg_id"] = df["iceberg_id"].astype(str).str.strip().str.upper()
    for col in ("dt_days", "lat", "lon", "ml_pred_lat", "ml_pred_lon", "ml_error_km"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if df[list(required_columns())].isna().any().any():
        bad = df[list(required_columns())].isna().sum()
        bad = bad[bad > 0]
        raise ValueError(f"Missing/non-numeric required pair values:\n{bad.to_string()}")

    if len(df) != EXPECTED_PAIRS:
        raise ValueError(
            f"Expected {EXPECTED_PAIRS} AMA-7 pairs, found {len(df)}. "
            "Check that this is the accepted AMA-7 pair-level CSV."
        )

    found_icebergs = set(df["iceberg_id"].unique())
    if found_icebergs != EXPECTED_ICEBERGS:
        raise ValueError(
            "Approved iceberg ID mismatch. "
            f"Missing={sorted(EXPECTED_ICEBERGS - found_icebergs)}, "
            f"Unexpected={sorted(found_icebergs - EXPECTED_ICEBERGS)}"
        )

    if (df["ml_error_km"] < 0).any():
        raise ValueError("Negative ML error values found.")

    df["predicted_speed_kmd"] = reconstruct_predicted_speed_kmd(df)
    if not np.isfinite(df["predicted_speed_kmd"]).all():
        raise ValueError("Could not calculate finite predicted speeds for every pair.")

    return df


def calculate_bands(df: pd.DataFrame) -> tuple[dict, float]:
    errors = df["ml_error_km"].to_numpy(dtype=float)
    overall_p75 = float(np.percentile(errors, 75))

    bands: dict[str, dict] = {}
    for name, lower, upper in BANDS:
        if math.isinf(upper):
            mask = df["predicted_speed_kmd"] >= lower
        else:
            mask = (
                (df["predicted_speed_kmd"] >= lower)
                & (df["predicted_speed_kmd"] < upper)
            )

        group_errors = df.loc[mask, "ml_error_km"].to_numpy(dtype=float)
        if len(group_errors) == 0:
            raise ValueError(
                f"No AMA-7 predictions fall into runtime speed category '{name}'."
            )

        p75 = float(np.percentile(group_errors, 75))
        band = {
            "sample_count": int(len(group_errors)),
            "p75_km": round(p75, 2),
            "p75_km_unrounded": round(p75, 6),
        }
        if name == "stationary":
            band["max_speed_kmd"] = 2.0
            band["speed_range_kmd"] = "[0, 2)"
        elif name == "slow":
            band["min_speed_kmd"] = 2.0
            band["max_speed_kmd"] = 5.0
            band["speed_range_kmd"] = "[2, 5)"
        elif name == "moderate":
            band["min_speed_kmd"] = 5.0
            band["max_speed_kmd"] = 10.0
            band["speed_range_kmd"] = "[5, 10)"
        else:
            band["min_speed_kmd"] = 10.0
            band["speed_range_kmd"] = "[10, infinity)"
        bands[name] = band

    total_band_samples = sum(x["sample_count"] for x in bands.values())
    if total_band_samples != len(df):
        raise AssertionError(
            f"Band counts sum to {total_band_samples}, expected {len(df)}."
        )

    return bands, overall_p75


def build_config(df: pd.DataFrame, bands: dict, overall_p75: float) -> dict:
    unique_ids = sorted(df["iceberg_id"].unique().tolist())
    band_config = {}
    for name, _, _ in BANDS:
        row = bands[name]
        band_config[name] = {
            key: row[key]
            for key in (
                "min_speed_kmd",
                "max_speed_kmd",
                "p75_km",
            )
            if key in row
        }
        band_config[name]["sample_count"] = row["sample_count"]

    return {
        "model_version": MODEL_VERSION,
        "horizon_hours": 24,
        "overall_p75_km": round(float(overall_p75), 2),
        "speed_basis": "predicted_speed_kmd",
        "speed_bands": band_config,
        "evaluation": {
            "icebergs": len(unique_ids),
            "iceberg_ids": unique_ids,
            "predictions": int(len(df)),
            "period": "2018-2021",
            "first_observation": str(df["date"].min()),
            "last_target": str(df["date_next"].max()),
            "leakage": "none",
            "error_metric": "Haversine ML prediction error (km)",
            "uncertainty_metric": "Empirical P75 within each predicted-speed band",
        },
        "limitations": {
            "validated_horizon_hours": 24,
            "48h_72h_ml": "not validated",
            "lstm": "experimental; did not outperform the baselines; not production",
            "calibration_note": (
                "P75 values are empirical summaries on the AMA-7 evaluation set; "
                "they are not an independent calibration-set coverage guarantee."
            ),
        },
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def write_note(df: pd.DataFrame, bands: dict, overall_p75: float, config: dict) -> None:
    lines = [
        "# AMA-8 Uncertainty Configuration Note",
        "",
        f"**Model:** {MODEL_VERSION}",
        "**Validated horizon:** 24 hours only",
        "**Runtime category variable:** `predicted_speed_kmd`",
        "",
        "## Evaluation basis",
        "",
        f"- Icebergs: {config['evaluation']['icebergs']}",
        f"- 24-hour prediction pairs: {len(df):,}",
        "- Period: 2018–2021",
        "- Leakage: none (approved 11 unseen iceberg test set)",
        f"- Overall ML P75 error: **{overall_p75:.3f} km**",
        "- Error metric: Haversine distance between actual and ML-predicted next-day positions",
        "",
        "## Runtime speed-band P75 radii",
        "",
        "| Speed band | Predicted speed (km/day) | Samples | P75 error / radius (km) |",
        "|---|---:|---:|---:|",
    ]
    for name, lower, upper in BANDS:
        row = bands[name]
        range_text = row["speed_range_kmd"]
        lines.append(
            f"| {name.capitalize()} | {range_text} | {row['sample_count']} | "
            f"**{row['p75_km']:.2f}** |"
        )

    lines += [
        "",
        "## Method",
        "",
        "- Runtime bins match `ama8_inference.py` / `speed_categories_kmd`: stationary below 2; slow below 5; moderate below 10; fast at 10 or above.",
        "- The accepted AMA-7 pair CSV contains the start and ML-predicted coordinates, but not the returned `predicted_speed_kmd` field.",
        "- To avoid classifying with actual observed speed, predicted speed was reconstructed from the saved ML-predicted coordinates using the exact inverse of the AMA-8 inference module's 24-hour local coordinate conversion (111,000 metres per degree and the cosine-of-latitude longitude adjustment).",
        "- P75 is calculated separately for the ML Haversine errors in each predicted-speed category using NumPy's default linear percentile method.",
        "- Band sample counts are included in the JSON for auditability.",
        "",
        "## AMA-7 model comparison",
        "",
        "| Model | Mean (km) | Median (km) | P75 (km) |",
        "|---|---:|---:|---:|",
        "| ML (AMA-8 inference) | 7.391 | 6.262 | 9.681 |",
        "| Physics (AMA-6 baseline) | 21.439 | 18.548 | 28.595 |",
        "| Zero velocity | 9.689 | 8.697 | 13.493 |",
        "",
        "## Required limitations",
        "",
        "- ML inference is validated for 24 hours only. Do not present 48-hour or 72-hour ML predictions as validated.",
        "- Any 48-hour or 72-hour physics results must be labelled **“Physics extrapolation, unvalidated beyond 24h.”**",
        "- The 1,777 prediction pairs are repeated temporal pairs across 11 iceberg tracks, not 1,777 independent icebergs.",
        "- These P75 values are calculated on the AMA-7 evaluation set itself; they are empirical test-set summaries, not an independent calibration-set coverage guarantee.",
        "- **LSTM remains experimental:** it did not outperform the baselines and is not the production model.",
        "",
        "## Data-quality disclosure",
        "",
        "- Four selected evaluation rows had marginal `siconc` values slightly above 1.0 (D28: 3; D30B: 1).",
        "- Maximum observed value: 1.0000152583234012; all four were within the 0.0001 tolerance and clipped only in the in-memory AMA-7 evaluation DataFrame.",
        "- The original `training_table.csv` was not modified.",
        "",
        "## Backend handoff",
        "",
        "- JSON schema follows Kumar's requested `model_version`, `horizon_hours`, `overall_p75_km`, `speed_bands`, and `evaluation` structure.",
        "- Runtime selector must use `predicted_speed_kmd`.",
        "- This is a separate handoff artifact. It does not overwrite `data/validation/model_config.json` or modify `drift_model.pkl`.",
        "",
    ]
    OUT_NOTE.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    print("AMA-8 runtime uncertainty handoff generator")
    print(f"Input: {PAIR_CSV}")
    print(f"Output folder: {SCRIPT_DIR}")
    df = load_pairs()
    bands, overall_p75 = calculate_bands(df)
    config = build_config(df, bands, overall_p75)

    OUT_JSON.write_text(json.dumps(config, indent=2), encoding="utf-8")
    write_note(df, bands, overall_p75, config)

    print(f"\nPairs: {len(df):,}")
    print(f"Icebergs: {df['iceberg_id'].nunique()}")
    print(f"Overall ML P75: {overall_p75:.6f} km")
    print("\nP75 by runtime predicted-speed category:")
    for name, _, _ in BANDS:
        row = bands[name]
        print(
            f"  {name:10s} N={row['sample_count']:4d} "
            f"P75={row['p75_km']:.6f} km"
        )
    print("\nCreated:")
    print(f"  {OUT_JSON}")
    print(f"  {OUT_NOTE}")
    print("\nExisting model_config.json and drift_model.pkl were not modified.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"\nAMA-8 generation failed: {exc}", file=sys.stderr)
        raise
