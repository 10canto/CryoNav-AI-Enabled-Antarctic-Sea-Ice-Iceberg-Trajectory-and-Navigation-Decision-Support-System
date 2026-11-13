"""
AMA-3: Ocean Forcing Extraction Pipeline
==========================================
Extracts ocean surface forcing values at each validated iceberg position and
date from the Copernicus Marine Global Ocean Physics Reanalysis.

Dataset  : GLOBAL_MULTIYEAR_PHY_001_030
Dataset ID: cmems_mod_glo_phy_my_0.083deg_P1D-m
Variables : uo, vo, siconc  (required)
            usi, vsi         (optional — extracted when available)
Coverage  : 1993-01-01 to 2026-09-22, global, 0.083 deg (~9.25 km)

Input     : data/validation/selected_icebergs.csv    (AMA-2 deliverable)
            DATA/consolidated_database_v8.0/updated7_consol/*.csv

Output    : data/validation/ocean_forcing_cache.csv  (AMA-3 deliverable)
            data/validation/ama3_pilot_report.md     (after pilot)
            data/validation/ama3_full_report.md      (after full run)

Usage
-----
    # Pilot: one year, limited icebergs
    python scripts/fetch_ocean_forcing.py --pilot

    # Full run (requires explicit approval):
    python scripts/fetch_ocean_forcing.py --full

    # Resume interrupted full run:
    python scripts/fetch_ocean_forcing.py --full --resume

Rules
-----
- Never expose or log credentials.
- Never download bulk NetCDF files.
- Never use synthetic data.
- Pilot only unless --full flag is passed.
"""

from __future__ import annotations

import argparse
import csv
import logging
import os
import pathlib
import sys
import time
import warnings
from datetime import datetime

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
_ML_ROOT    = _SCRIPT_DIR.parent
_REPO_ROOT  = _ML_ROOT.parent
_DATA_DIR   = _REPO_ROOT / "DATA" / "consolidated_database_v8.0" / "updated7_consol"
_VAL_DIR    = _ML_ROOT / "data" / "validation"

# External data directory (outside repository, configured via environment variable)
# Default: C:\CryoNav-Data (Windows) or ~/CryoNav-Data (Unix)
_EXTERNAL_DATA_DIR = pathlib.Path(
    os.getenv("CRYONAV_DATA_DIR", "C:/CryoNav-Data" if sys.platform == "win32" else str(pathlib.Path.home() / "CryoNav-Data"))
)

# AMA-2 selected icebergs (small metadata file, kept in repo)
_SEL_CSV = _VAL_DIR / "selected_icebergs.csv"

# AMA-3 ocean forcing cache (large data file, stored externally)
_CACHE_CSV = _EXTERNAL_DATA_DIR / "validation" / "ocean_forcing_cache.csv"

# AMA-3 reports (small markdown files, kept in repo)
_PILOT_RPT = _VAL_DIR / "ama3_pilot_report.md"
_FULL_RPT  = _VAL_DIR / "ama3_full_report.md"

# ---------------------------------------------------------------------------
# Dataset configuration
# ---------------------------------------------------------------------------
DATASET_ID   = "cmems_mod_glo_phy_my_0.083deg_P1D-m"
REQUIRED_VARS = ["uo", "vo", "siconc"]
OPTIONAL_VARS = ["usi", "vsi"]
ALL_VARS      = REQUIRED_VARS + OPTIONAL_VARS

SURFACE_DEPTH_MIN = 0.494  # exact surface level in this dataset
SURFACE_DEPTH_MAX = 0.495  # narrow range — selects only surface level

WINDOW_START = 1993
WINDOW_END   = 2021

# Spatial region (SAT-2 bounding box, matches AMA-2)
LAT_MIN, LAT_MAX = -72.0, -30.0
LON_MIN, LON_MAX = -15.0,  40.0

# ---------------------------------------------------------------------------
# Retry / timeout settings
# ---------------------------------------------------------------------------
MAX_RETRIES       = 3
RETRY_WAIT_SEC    = 30   # seconds between retries (longer than before to let transients clear)
YEAR_OPEN_TIMEOUT = 120  # documented; enforcement handled by copernicusmarine internally

# ---------------------------------------------------------------------------
# Sensor column pairs (BYU database format)
# ---------------------------------------------------------------------------
SENSOR_PAIRS = [
    ("nic_1",      "nic_2"),
    ("sass_1",     "sass_2"),
    ("ers_1",      "ers_2"),
    ("nscat_1",    "nscat_2"),
    ("qscat_1",    "qscat_2"),
    ("seawinds_1", "seawinds_2"),
    ("ascat_1",    "ascat_2"),
    ("oscat_1",    "oscat_2"),
]

# ---------------------------------------------------------------------------
# Cache CSV column order
# ---------------------------------------------------------------------------
CACHE_COLS = [
    "iceberg_id", "date_str", "lat", "lon",
    "uo", "vo", "siconc", "usi", "vsi",
    "uo_missing", "vo_missing", "siconc_missing",
    "usi_missing", "vsi_missing",
    "source_note",
]

# ---------------------------------------------------------------------------
# Logging — no credentials ever appear in log output
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ama3")


# ---------------------------------------------------------------------------
# Helper: Julian date → calendar date string
# ---------------------------------------------------------------------------
def julian_to_date(julian_int: int) -> str:
    """Convert BYU Julian date YYYYDDD to ISO date string YYYY-MM-DD."""
    year = julian_int // 1000
    doy  = julian_int % 1000
    doy  = max(1, min(doy, 366))
    try:
        dt = datetime.strptime(f"{year}-{doy}", "%Y-%j")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return f"{year}-01-01"


# ---------------------------------------------------------------------------
# Build the flat request table from AMA-2 CSV + tracking CSVs
# ---------------------------------------------------------------------------
def build_request_table(
    selected_csv: pathlib.Path,
    data_dir: pathlib.Path,
    years: list[int] | None = None,
    max_icebergs: int | None = None,
) -> pd.DataFrame:
    """
    Return a DataFrame with one row per (iceberg, date, lat, lon) observation
    that falls within the AMA-2 spatial window and date range.

    Parameters
    ----------
    selected_csv  : Path to selected_icebergs.csv (AMA-2 deliverable)
    data_dir      : Path to consolidated tracking CSV folder
    years         : If given, restrict to these calendar years
    max_icebergs  : If given, limit to the first N icebergs (pilot use)
    """
    sel = pd.read_csv(selected_csv)
    if max_icebergs:
        sel = sel.head(max_icebergs)

    records: list[dict] = []

    for _, row in sel.iterrows():
        iceberg_id = row["iceberg_id"]
        fpath = data_dir / f"{iceberg_id.lower()}.csv"
        if not fpath.exists():
            log.warning("Tracking file not found: %s", fpath.name)
            continue

        try:
            df = pd.read_csv(fpath)
        except Exception as exc:
            log.warning("Cannot read %s: %s", fpath.name, exc)
            continue

        df["year"] = df["date"] // 1000

        # Best position per row
        lat_col = pd.Series(np.nan, index=df.index, dtype=float)
        lon_col = pd.Series(np.nan, index=df.index, dtype=float)
        for sc, lc in SENSOR_PAIRS:
            if sc in df.columns and lc in df.columns:
                unfilled = lat_col.isna()
                valid = unfilled & (df[sc] != 0) & df[sc].notna()
                lat_col[valid] = df.loc[valid, sc]
                lon_col[valid] = df.loc[valid, lc]

        df["lat"] = lat_col
        df["lon"] = lon_col

        # Apply all filters
        mask = (
            df["lat"].notna() & df["lon"].notna() &
            (df["lat"] >= LAT_MIN) & (df["lat"] <= LAT_MAX) &
            (df["lon"] >= LON_MIN) & (df["lon"] <= LON_MAX) &
            (df["year"] >= WINDOW_START) & (df["year"] <= WINDOW_END)
        )
        if years:
            mask &= df["year"].isin(years)

        window = df[mask]

        for _, obs in window.iterrows():
            date_str = julian_to_date(int(obs["date"]))
            records.append({
                "iceberg_id": iceberg_id,
                "date_str":   date_str,
                "year":       int(obs["year"]),
                "lat":        round(float(obs["lat"]), 5),
                "lon":        round(float(obs["lon"]), 5),
            })

    result = pd.DataFrame(records)
    if not result.empty:
        result = result.sort_values(["year", "date_str", "iceberg_id"]).reset_index(drop=True)
    log.info(
        "Request table: %d positions across %d icebergs, years %s",
        len(result),
        result["iceberg_id"].nunique() if not result.empty else 0,
        sorted(result["year"].unique().tolist()) if not result.empty else [],
    )
    return result


# ---------------------------------------------------------------------------
# Load already-cached rows to enable resume
# ---------------------------------------------------------------------------
def load_cache_keys(cache_path: pathlib.Path) -> set[tuple[str, str]]:
    """Return set of (iceberg_id, date_str) already in the cache CSV."""
    if not cache_path.exists():
        return set()
    done: set[tuple[str, str]] = set()
    try:
        cached = pd.read_csv(cache_path, usecols=["iceberg_id", "date_str"])
        for _, r in cached.iterrows():
            done.add((r["iceberg_id"], r["date_str"]))
    except Exception as exc:
        log.warning("Could not read existing cache (%s) — starting fresh.", exc)
    return done


# ---------------------------------------------------------------------------
# Write rows to the cache CSV (append mode)
# ---------------------------------------------------------------------------
def append_to_cache(rows: list[dict], cache_path: pathlib.Path) -> None:
    """Append a list of row dicts to the cache CSV, creating header if needed."""
    write_header = not cache_path.exists()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CACHE_COLS)
        if write_header:
            writer.writeheader()
        for row in rows:
            # Fill any missing optional columns with empty string
            for col in CACHE_COLS:
                row.setdefault(col, "")
            writer.writerow({c: row[c] for c in CACHE_COLS})


# ---------------------------------------------------------------------------
# Extract one year's worth of forcing via the Copernicus Marine lazy API
# — Option B: open_dataset() + vectorised .sel() + single .compute() —
# No NetCDF file is written at any point.  All data stays in RAM.
# ---------------------------------------------------------------------------
def extract_year(
    year: int,
    year_rows: pd.DataFrame,
    cache_keys: set[tuple[str, str]],
    dry_run: bool = False,
) -> tuple[list[dict], dict]:
    """
    Open the CMEMS dataset lazily for `year`, build vectorised coordinate
    arrays for all un-cached positions, call .compute() once to pull the
    required values into RAM, then assemble and return result rows.

    Design
    ------
    1. open_dataset() — authenticated, lazy (no data transferred).
    2. Vectorised xr.DataArray index arrays — one entry per observation.
    3. Single ds.sel(...).compute() — one coordinated zarr read for all
       observations this year.  No per-row network round-trips.
    4. ds.close() — releases the remote zarr connection.
    5. Nothing is written to disk beyond the final cache CSV.

    Error handling
    --------------
    - open_dataset retried up to MAX_RETRIES times with RETRY_WAIT_SEC delay.
    - .compute() retried up to MAX_RETRIES times independently.
    - Any remaining NaN/masked values are flagged as missing (not errors).
    - Per-observation exceptions during result assembly are caught; those
      rows are marked with source_note and missing flags set to 1.
    - Logger level is always restored before every return path.
    """
    import copernicusmarine  # deferred so module imports without the package
    import xarray as xr

    # ------------------------------------------------------------------
    # Filter to un-cached rows only
    # ------------------------------------------------------------------
    to_fetch = year_rows[
        ~year_rows.apply(
            lambda r: (r["iceberg_id"], r["date_str"]) in cache_keys, axis=1
        )
    ]

    stats: dict = {
        "year":           year,
        "requested":      len(year_rows),
        "already_cached": len(year_rows) - len(to_fetch),
        "fetched":        0,
        "missing_value":  0,
        "api_error":      0,
        "retried":        0,
    }

    if to_fetch.empty:
        log.info("Year %d: all %d rows already cached.", year, len(year_rows))
        return [], stats

    if dry_run:
        log.info("Year %d: dry-run, would fetch %d rows.", year, len(to_fetch))
        return [], stats

    # ------------------------------------------------------------------
    # Tight spatial/temporal bounding box
    # Two grid-cell margin (2 × 0.083° ≈ 0.17°) so nearest-neighbour
    # selection never falls outside the opened window.
    # ------------------------------------------------------------------
    lat_lo = max(LAT_MIN, float(to_fetch["lat"].min()) - 0.17)
    lat_hi = min(LAT_MAX, float(to_fetch["lat"].max()) + 0.17)
    lon_lo = max(LON_MIN, float(to_fetch["lon"].min()) - 0.17)
    lon_hi = min(LON_MAX, float(to_fetch["lon"].max()) + 0.17)

    n_rows = len(to_fetch)
    log.info(
        "Year %d: vectorised fetch for %d positions "
        "(lat %.2f..%.2f  lon %.2f..%.2f) …",
        year, n_rows, lat_lo, lat_hi, lon_lo, lon_hi,
    )

    # Silence copernicusmarine INFO/DEBUG during open_dataset and compute
    cm_log    = logging.getLogger("copernicusmarine")
    prev_level = cm_log.level
    cm_log.setLevel(logging.WARNING)

    # ------------------------------------------------------------------
    # Step 1 — open_dataset (lazy, ~1–3 s, no data transferred yet)
    # ------------------------------------------------------------------
    ds = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            ds = copernicusmarine.open_dataset(
                dataset_id        = DATASET_ID,
                variables         = ALL_VARS,
                minimum_latitude  = lat_lo,
                maximum_latitude  = lat_hi,
                minimum_longitude = lon_lo,
                maximum_longitude = lon_hi,
                minimum_depth     = SURFACE_DEPTH_MIN,
                maximum_depth     = SURFACE_DEPTH_MAX,
                start_datetime    = f"{year}-01-01",
                end_datetime      = f"{year}-12-31",
            )
            break  # success
        except Exception as exc:
            log.warning(
                "Year %d: open_dataset attempt %d/%d failed: %s",
                year, attempt, MAX_RETRIES, type(exc).__name__,
            )
            stats["api_error"] += 1
            if attempt < MAX_RETRIES:
                stats["retried"] += 1
                time.sleep(RETRY_WAIT_SEC)
            else:
                log.error(
                    "Year %d: all %d open_dataset attempts failed. Skipping.",
                    year, MAX_RETRIES,
                )
                cm_log.setLevel(prev_level)
                return [], stats

    cm_log.setLevel(prev_level)  # restore before any further work

    if ds is None:
        return [], stats

    # ------------------------------------------------------------------
    # Determine which optional variables are present in this dataset slice
    # ------------------------------------------------------------------
    present_vars       = set(ds.data_vars)
    available_optional = [v for v in OPTIONAL_VARS if v in present_vars]
    missing_optional   = [v for v in OPTIONAL_VARS if v not in present_vars]
    if missing_optional:
        log.info("Year %d: optional vars absent from dataset: %s", year, missing_optional)

    vars_to_select = REQUIRED_VARS + available_optional

    # ------------------------------------------------------------------
    # Step 2 — build vectorised index arrays (all observations at once)
    # xr.DataArray with dim="obs" tells xarray to do element-wise indexing
    # (also called "pointwise" or "orthogonal-like" selection).
    # ------------------------------------------------------------------
    obs_times = xr.DataArray(
        pd.to_datetime(to_fetch["date_str"].values), dims="obs"
    )
    obs_lats  = xr.DataArray(to_fetch["lat"].values.astype(float),  dims="obs")
    obs_lons  = xr.DataArray(to_fetch["lon"].values.astype(float),  dims="obs")

    # ------------------------------------------------------------------
    # Step 3 — single .sel() + .compute()
    # Still lazy after .sel(); .compute() triggers the actual data fetch.
    # We retry the compute step independently from the open step.
    # ------------------------------------------------------------------
    computed = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            cm_log.setLevel(logging.WARNING)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                computed = (
                    ds[vars_to_select]
                    .sel(
                        time      = obs_times,
                        latitude  = obs_lats,
                        longitude = obs_lons,
                        depth     = SURFACE_DEPTH_MIN,
                        method    = "nearest",
                    )
                    .compute()
                )
            cm_log.setLevel(prev_level)
            break
        except Exception as exc:
            cm_log.setLevel(prev_level)
            log.warning(
                "Year %d: .compute() attempt %d/%d failed: %s — %s",
                year, attempt, MAX_RETRIES,
                type(exc).__name__, str(exc)[:120],
            )
            stats["api_error"] += 1
            if attempt < MAX_RETRIES:
                stats["retried"] += 1
                time.sleep(RETRY_WAIT_SEC)
            else:
                log.error(
                    "Year %d: all %d .compute() attempts failed. Skipping.",
                    year, MAX_RETRIES,
                )
                try:
                    ds.close()
                except Exception:
                    pass
                return [], stats

    try:
        ds.close()
    except Exception:
        pass

    if computed is None:
        return [], stats

    # ------------------------------------------------------------------
    # Step 4 — assemble result rows from the in-memory computed Dataset
    # ------------------------------------------------------------------
    t0       = time.time()
    results: list[dict] = []
    n_fetched = 0
    n_missing = 0

    for i, (_, obs) in enumerate(to_fetch.iterrows()):
        iceberg_id = obs["iceberg_id"]
        date_str   = obs["date_str"]
        lat        = obs["lat"]
        lon        = obs["lon"]

        row: dict = {
            "iceberg_id":  iceberg_id,
            "date_str":    date_str,
            "lat":         lat,
            "lon":         lon,
            "source_note": "",
        }
        # Initialise all value and missing-flag columns
        for v in ALL_VARS:
            row[v]              = ""
            row[f"{v}_missing"] = 0

        try:
            obs_slice = computed.isel(obs=i)

            # Required variables
            for v in REQUIRED_VARS:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    val = float(obs_slice[v].values)
                if np.isnan(val):
                    row[v]              = ""
                    row[f"{v}_missing"] = 1
                    n_missing += 1
                else:
                    row[v]              = round(val, 6)
                    row[f"{v}_missing"] = 0

            # Optional variables that were present
            for v in available_optional:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    val = float(obs_slice[v].values)
                if np.isnan(val):
                    row[v]              = ""
                    row[f"{v}_missing"] = 1
                else:
                    row[v]              = round(val, 6)
                    row[f"{v}_missing"] = 0

            # Optional variables absent from the dataset for this year
            for v in missing_optional:
                row[f"{v}_missing"] = 1

            n_fetched += 1

        except Exception as exc:
            exc_name = type(exc).__name__
            row["source_note"] = f"assembly_error:{exc_name}"
            for v in ALL_VARS:
                row[f"{v}_missing"] = 1
            n_missing += 1

        results.append(row)

    elapsed = time.time() - t0
    stats["fetched"]       = n_fetched
    stats["missing_value"] = n_missing

    log.info(
        "Year %d: done — %d fetched, %d missing values, %.1f s assembly",
        year, n_fetched, n_missing, elapsed,
    )
    return results, stats


# ---------------------------------------------------------------------------
# Pilot: single year, limited icebergs
# ---------------------------------------------------------------------------
def run_pilot(
    selected_csv: pathlib.Path,
    data_dir: pathlib.Path,
    cache_path: pathlib.Path,
    pilot_year: int = 2016,
    pilot_icebergs: int = 5,
) -> dict:
    """
    Run a small pilot extraction:
        - 1 year (pilot_year, default 2016 — the busiest year with 12 icebergs)
        - Up to pilot_icebergs icebergs
    Returns a stats dict.
    """
    log.info("=== AMA-3 PILOT ===  year=%d  max_icebergs=%d", pilot_year, pilot_icebergs)

    req = build_request_table(
        selected_csv,
        data_dir,
        years=[pilot_year],
        max_icebergs=pilot_icebergs,
    )

    if req.empty:
        log.error("No positions found for pilot year %d. Check selected_icebergs.csv.", pilot_year)
        return {}

    log.info("Pilot request table: %d positions", len(req))

    cache_keys = load_cache_keys(cache_path)
    rows, stats = extract_year(pilot_year, req, cache_keys)

    if rows:
        append_to_cache(rows, cache_path)
        log.info("Pilot: %d rows written to cache.", len(rows))

    return stats


# ---------------------------------------------------------------------------
# Full run: all 29 years
# ---------------------------------------------------------------------------
def run_full(
    selected_csv: pathlib.Path,
    data_dir: pathlib.Path,
    cache_path: pathlib.Path,
    resume: bool = False,
) -> list[dict]:
    """
    Process all years from WINDOW_START to WINDOW_END.
    If resume=True, skips rows already present in cache_path.
    Returns a list of per-year stats dicts.
    """
    log.info("=== AMA-3 FULL RUN ===  years %d-%d", WINDOW_START, WINDOW_END)

    req = build_request_table(selected_csv, data_dir)
    if req.empty:
        log.error("Empty request table. Aborting.")
        return []

    cache_keys = load_cache_keys(cache_path) if resume else set()
    all_years  = sorted(req["year"].unique().tolist())
    all_stats  = []

    for year in all_years:
        year_rows = req[req["year"] == year]
        rows, stats = extract_year(year, year_rows, cache_keys)
        if rows:
            append_to_cache(rows, cache_path)
            # Update cache keys so subsequent years don't re-fetch
            for r in rows:
                cache_keys.add((r["iceberg_id"], r["date_str"]))
        all_stats.append(stats)

    return all_stats


# ---------------------------------------------------------------------------
# Report writers
# ---------------------------------------------------------------------------
def _safe_pct(num: int, denom: int) -> str:
    if denom == 0:
        return "n/a"
    return f"{100 * num / denom:.1f}%"


def write_pilot_report(stats: dict, cache_path: pathlib.Path, report_path: pathlib.Path) -> None:
    """Write a markdown pilot report."""
    lines = [
        "# AMA-3 Pilot Report",
        "",
        f"Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Pilot year: {stats.get('year', '?')}",
        "",
        "## Extraction Statistics",
        "",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Positions requested | {stats.get('requested', 0)} |",
        f"| Already cached (skipped) | {stats.get('already_cached', 0)} |",
        f"| Newly fetched | {stats.get('fetched', 0)} |",
        f"| Missing values (land/ice/gap) | {stats.get('missing_value', 0)} |",
        f"| API errors | {stats.get('api_error', 0)} |",
        f"| Retries | {stats.get('retried', 0)} |",
        f"| Success rate | {_safe_pct(stats.get('fetched', 0), stats.get('requested', 0))} |",
        "",
    ]

    if cache_path.exists():
        df = pd.read_csv(cache_path)
        pilot_year = stats.get("year")
        if pilot_year:
            df = df[pd.to_datetime(df["date_str"]).dt.year == pilot_year]

        lines += [
            "## Variable Coverage (pilot year, fetched rows only)",
            "",
            "| Variable | Non-missing | Missing | Missing % |",
            "|---|---|---|---|",
        ]
        for v in ALL_VARS:
            if v in df.columns:
                non_miss = (df[f"{v}_missing"] == 0).sum()
                miss     = (df[f"{v}_missing"] == 1).sum()
                total    = non_miss + miss
                lines.append(
                    f"| {v} | {non_miss} | {miss} | {_safe_pct(miss, total)} |"
                )

        lines += [
            "",
            "## Cache File",
            "",
            f"Path  : `{cache_path}`",
            f"Rows  : {len(df)}  (this pilot)",
        ]
        size_bytes = cache_path.stat().st_size
        lines.append(f"Size  : {size_bytes / 1024:.1f} KB")

        # Sample rows
        lines += [
            "",
            "## Sample Rows (first 3)",
            "",
            "```",
        ]
        for _, r in df.head(3).iterrows():
            lines.append(
                f"iceberg={r['iceberg_id']}  date={r['date_str']}  "
                f"lat={r['lat']}  lon={r['lon']}  "
                f"uo={r['uo']}  vo={r['vo']}  siconc={r['siconc']}"
            )
        lines.append("```")

    lines += [
        "",
        "## AMA-3 Pilot Acceptance Check",
        "",
        "- [ ] API connectivity confirmed",
        "- [ ] Correct variables extracted (uo, vo, siconc)",
        "- [ ] Coordinate and timestamp matching verified",
        "- [ ] Missing-value handling works",
        "- [ ] Cache written and readable",
        "",
        "_Full 29-year extraction requires explicit approval after pilot review._",
    ]

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    log.info("Pilot report written: %s", report_path)


def write_full_report(all_stats: list[dict], cache_path: pathlib.Path, report_path: pathlib.Path) -> None:
    """Write a markdown full-run report."""
    total_req    = sum(s.get("requested", 0)     for s in all_stats)
    total_fetch  = sum(s.get("fetched", 0)       for s in all_stats)
    total_miss   = sum(s.get("missing_value", 0) for s in all_stats)
    total_err    = sum(s.get("api_error", 0)     for s in all_stats)
    total_retry  = sum(s.get("retried", 0)       for s in all_stats)

    lines = [
        "# AMA-3 Full Extraction Report",
        "",
        f"Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Period    : {WINDOW_START}-01-01 to {WINDOW_END}-12-31",
        "",
        "## Overall Statistics",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Total positions requested | {total_req} |",
        f"| Newly fetched | {total_fetch} |",
        f"| Missing values | {total_miss} |",
        f"| API errors | {total_err} |",
        f"| Retries | {total_retry} |",
        f"| Overall success rate | {_safe_pct(total_fetch, total_req)} |",
        "",
        "## Per-Year Summary",
        "",
        "| Year | Requested | Fetched | Missing | API errors |",
        "|---|---|---|---|---|",
    ]
    for s in all_stats:
        lines.append(
            f"| {s['year']} | {s['requested']} | {s['fetched']} "
            f"| {s['missing_value']} | {s['api_error']} |"
        )

    if cache_path.exists():
        size_bytes = cache_path.stat().st_size
        size_mb    = size_bytes / (1024 ** 2)
        df         = pd.read_csv(cache_path)
        lines += [
            "",
            "## Cache File",
            "",
            f"Path  : `{cache_path}`",
            f"Rows  : {len(df)}",
            f"Size  : {size_mb:.2f} MB  _(actual measured value)_",
            "",
            "## Variable Coverage (all rows)",
            "",
            "| Variable | Non-missing | Missing | Missing % |",
            "|---|---|---|---|",
        ]
        for v in ALL_VARS:
            miss_col = f"{v}_missing"
            if miss_col in df.columns:
                non_miss = (df[miss_col] == 0).sum()
                miss     = (df[miss_col] == 1).sum()
                total    = non_miss + miss
                lines.append(f"| {v} | {non_miss} | {miss} | {_safe_pct(miss, total)} |")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    log.info("Full report written: %s", report_path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="AMA-3: Extract ocean forcing for validated iceberg positions."
    )
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--pilot", action="store_true",
        help="Run a small one-year pilot (safe, no approval needed).",
    )
    mode.add_argument(
        "--full", action="store_true",
        help="Run the full 29-year extraction (requires prior approval).",
    )
    p.add_argument(
        "--resume", action="store_true",
        help="Skip positions already in the cache (--full only).",
    )
    p.add_argument(
        "--pilot-year", type=int, default=2016,
        help="Year to use for the pilot run (default: 2016).",
    )
    p.add_argument(
        "--pilot-icebergs", type=int, default=5,
        help="Max icebergs in the pilot run (default: 5).",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    # Verify required inputs exist
    if not _SEL_CSV.exists():
        log.error("AMA-2 deliverable not found: %s", _SEL_CSV)
        sys.exit(1)
    if not _DATA_DIR.exists():
        log.error("Tracking CSV directory not found: %s", _DATA_DIR)
        sys.exit(1)

    if args.pilot:
        stats = run_pilot(
            _SEL_CSV, _DATA_DIR, _CACHE_CSV,
            pilot_year=args.pilot_year,
            pilot_icebergs=args.pilot_icebergs,
        )
        if stats:
            write_pilot_report(stats, _CACHE_CSV, _PILOT_RPT)
            # Print summary to terminal
            print()
            print("=" * 60)
            print("  AMA-3 PILOT COMPLETE")
            print("=" * 60)
            print(f"  Year          : {stats.get('year')}")
            print(f"  Requested     : {stats.get('requested')}")
            print(f"  Fetched       : {stats.get('fetched')}")
            print(f"  Missing vals  : {stats.get('missing_value')}")
            print(f"  API errors    : {stats.get('api_error')}")
            print(f"  Retries       : {stats.get('retried')}")
            if _CACHE_CSV.exists():
                kb = _CACHE_CSV.stat().st_size / 1024
                print(f"  Cache size    : {kb:.1f} KB  (actual)")
            print(f"  Report        : {_PILOT_RPT.name}")
            print("=" * 60)
            print()
            print("  Review the pilot report, then approve full extraction.")
            print()

    elif args.full:
        log.info("Starting full 29-year extraction. This requires prior approval.")
        all_stats = run_full(_SEL_CSV, _DATA_DIR, _CACHE_CSV, resume=args.resume)
        if all_stats:
            write_full_report(all_stats, _CACHE_CSV, _FULL_RPT)


if __name__ == "__main__":
    main()
