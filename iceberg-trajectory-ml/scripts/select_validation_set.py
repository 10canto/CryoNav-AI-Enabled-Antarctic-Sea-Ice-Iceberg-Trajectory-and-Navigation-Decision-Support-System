"""
AMA-2: Select Validation Icebergs
==================================
Reads the BYU MERS Consolidated Antarctic Iceberg Database and selects
icebergs that meet the AMA-2 validation criteria.

Filters (exact, from team Excel plan AMA-2 and SAT-2 bounding box):
    Region  : latitude  -72 to -30
              longitude -15 to  40
    Window  : 1993-01-01 to 2021-12-31
    Min obs : 10 valid non-zero positions within the box AND window

Output
------
    data/validation/selected_icebergs.csv   (AMA-2 deliverable)

The script prints an aggregate yearly summary and size-class counts to
the terminal.  No companion file is created.

No network requests are made.  Only pandas and numpy are required.

Columns in the output CSV
--------------------------
iceberg_id          Uppercase iceberg name (matches source filename)
n_positions         Valid in-box in-window observations
yr_min              First year with >=1 in-box in-window position
yr_max              Last year with >=1 in-box in-window position
lat_mean            Mean latitude  of in-box in-window rows (2 d.p.)
lon_mean            Mean longitude of in-box in-window rows (2 d.p.)
size_km_median      Median major axis in km; empty string if no size data
size_class_10km     PRIMARY (AMA-7): giant_tabular (>=10 km) /
                    small (<10 km) / unknown (no size data)
size_class_nic      SECONDARY reference: giant_tabular (>=18.52 km) /
                    small_medium (<18.52 km) / unknown
n_positions_per_year  Pipe-separated YEAR:COUNT pairs for years with
                    >=1 observation, e.g. 2004:312|2005:365
"""

import glob
import os
import sys
import pathlib
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Paths — all relative to this script's location
# ---------------------------------------------------------------------------
_SCRIPT_DIR   = pathlib.Path(__file__).resolve().parent          # …/scripts
_ML_ROOT      = _SCRIPT_DIR.parent                               # …/iceberg-trajectory-ml
_REPO_ROOT    = _ML_ROOT.parent                                  # …/CryoNav-AI-…
_DATA_DIR     = _REPO_ROOT / "DATA" / "consolidated_database_v8.0" / "updated7_consol"
_OUT_DIR     = _ML_ROOT / "data" / "validation"
_OUT_CSV     = _OUT_DIR / "selected_icebergs.csv"

# ---------------------------------------------------------------------------
# Filter constants (AMA-2 exact requirements)
# ---------------------------------------------------------------------------
LAT_MIN, LAT_MAX =  -72.0,  -30.0   # SAT-2 bounding box latitudes
LON_MIN, LON_MAX =  -15.0,   40.0   # SAT-2 bounding box longitudes
YR_MIN,  YR_MAX  = 1993,    2021    # inclusive
MIN_POSITIONS    = 10               # valid non-zero in-box in-window obs

# ---------------------------------------------------------------------------
# Sensor column pairs present in the BYU database
# Each pair: (lat_col, lon_col)
# ---------------------------------------------------------------------------
SENSOR_PAIRS = [
    ("nic_1",       "nic_2"),
    ("sass_1",      "sass_2"),
    ("ers_1",       "ers_2"),
    ("nscat_1",     "nscat_2"),
    ("qscat_1",     "qscat_2"),
    ("seawinds_1",  "seawinds_2"),
    ("ascat_1",     "ascat_2"),
    ("oscat_1",     "oscat_2"),
]

# ---------------------------------------------------------------------------
# Size classification thresholds
# ---------------------------------------------------------------------------
THRESH_10KM   = 10.0    # AMA-7 Excel wording: small < 10 km, giant >= 10 km
THRESH_NIC_KM = 18.52   # NIC standard: 10 nautical miles = 18.52 km
NM_TO_KM      = 1.852


def _best_position(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """
    Return (lat_series, lon_series) using the first non-zero sensor reading
    per row across all known sensor pairs.
    """
    lat_col = pd.Series(np.nan, index=df.index, dtype=float)
    lon_col = pd.Series(np.nan, index=df.index, dtype=float)
    for sc, lc in SENSOR_PAIRS:
        if sc in df.columns and lc in df.columns:
            unfilled = lat_col.isna()
            valid    = unfilled & (df[sc] != 0) & df[sc].notna()
            lat_col[valid] = df.loc[valid, sc]
            lon_col[valid] = df.loc[valid, lc]
    return lat_col, lon_col


def _size_class(size_km) -> tuple[str, str]:
    """
    Return (size_class_10km, size_class_nic) for a median size value in km.
    None / NaN → 'unknown' for both.
    """
    if size_km is None or (isinstance(size_km, float) and np.isnan(size_km)):
        return "unknown", "unknown"
    if size_km >= THRESH_NIC_KM:                     # >= 18.52 km
        return "giant_tabular", "giant_tabular"
    if size_km >= THRESH_10KM:                        # 10 km <= x < 18.52 km
        return "giant_tabular", "small_medium"
    return "small", "small_medium"                   # < 10 km


def process_files(data_dir: pathlib.Path) -> list[dict]:
    """
    Scan all CSV files in data_dir and return a list of row-dicts for
    icebergs that pass all AMA-2 filters.
    """
    csv_files = sorted(glob.glob(str(data_dir / "*.csv")))
    if not csv_files:
        sys.exit(f"ERROR: No CSV files found in {data_dir}")

    print(f"Scanning {len(csv_files)} iceberg files …")

    rows = []
    skipped_few   = 0
    skipped_error = 0

    for fpath in csv_files:
        try:
            df = pd.read_csv(fpath)
            iceberg_id = os.path.basename(fpath).replace(".csv", "").upper()

            # Julian date YYYYDDD → year
            df["year"] = df["date"] // 1000

            # Best position per row
            df["lat"], df["lon"] = _best_position(df)

            # Apply all filters in one step
            window = df[
                (df["year"] >= YR_MIN) & (df["year"] <= YR_MAX) &
                df["lat"].notna() & df["lon"].notna() &
                (df["lat"] >= LAT_MIN) & (df["lat"] <= LAT_MAX) &
                (df["lon"] >= LON_MIN) & (df["lon"] <= LON_MAX)
            ].copy()

            if len(window) < MIN_POSITIONS:
                skipped_few += 1
                continue

            # --- Per-year position counts -----------------------------------
            yr_counts = (
                window.groupby("year")
                      .size()
                      .sort_index()
            )
            n_positions_per_year = "|".join(
                f"{int(yr)}:{int(cnt)}" for yr, cnt in yr_counts.items()
            )

            # --- Size (from ALL rows in file, not just window rows) ---------
            # size_1 is the major axis in nautical miles; 0 means no data.
            if "size_1" in df.columns:
                size_vals = df["size_1"].replace(0, np.nan).dropna()
                if len(size_vals) > 0:
                    size_nm_med = float(size_vals.median())
                    size_km_med = round(size_nm_med * NM_TO_KM, 2)
                else:
                    size_km_med = None
            else:
                size_km_med = None

            sc_10km, sc_nic = _size_class(size_km_med)

            rows.append({
                "iceberg_id":          iceberg_id,
                "n_positions":         len(window),
                "yr_min":              int(window["year"].min()),
                "yr_max":              int(window["year"].max()),
                "lat_mean":            round(float(window["lat"].mean()), 2),
                "lon_mean":            round(float(window["lon"].mean()), 2),
                "size_km_median":      size_km_med if size_km_med is not None else "",
                "size_class_10km":     sc_10km,
                "size_class_nic":      sc_nic,
                "n_positions_per_year": n_positions_per_year,
            })

        except Exception:
            skipped_error += 1
            continue

    print(f"  Files passing filters : {len(rows)}")
    print(f"  Skipped (< {MIN_POSITIONS} positions): {skipped_few}")
    print(f"  Skipped (read errors) : {skipped_error}")
    return rows


def print_summary(df: pd.DataFrame) -> None:
    """Print the aggregate yearly summary and size-class counts."""

    print()
    print("=" * 62)
    print("  AMA-2 VALIDATION SET — AGGREGATE SUMMARY")
    print("=" * 62)
    print(f"  Region : lat {LAT_MIN} to {LAT_MAX}, lon {LON_MIN} to {LON_MAX}")
    print(f"  Window : {YR_MIN}-01-01 to {YR_MAX}-12-31")
    print(f"  Filter : min {MIN_POSITIONS} valid non-zero in-box in-window positions")
    print(f"  Total icebergs selected : {len(df)}")

    # --- Size-class counts (primary: 10 km) ---------------------------------
    print()
    print("  Size class (PRIMARY — 10 km threshold, AMA-7):")
    sc_counts = df["size_class_10km"].value_counts()
    for label in ["giant_tabular", "small", "unknown"]:
        print(f"    {label:<20} {sc_counts.get(label, 0):>3}")

    print()
    print("  Size class (secondary — 18.52 km / 10 NM NIC standard):")
    sc_nic_counts = df["size_class_nic"].value_counts()
    for label in ["giant_tabular", "small_medium", "unknown"]:
        print(f"    {label:<20} {sc_nic_counts.get(label, 0):>3}")

    # Boundary icebergs (10 km <= size < 18.52 km) — classified differently
    boundary = df[
        df["size_km_median"].apply(
            lambda x: isinstance(x, float) and THRESH_10KM <= x < THRESH_NIC_KM
        )
    ]
    if len(boundary) > 0:
        print()
        print("  Boundary icebergs (>=10 km AND <18.52 km — differ between thresholds):")
        for _, r in boundary.iterrows():
            print(f"    {r['iceberg_id']:<12} {r['size_km_median']:.2f} km")

    # Icebergs with no size data
    no_size = df[df["size_km_median"] == ""]
    print()
    print(f"  Icebergs with no size data (unknown): {len(no_size)}")
    if len(no_size) > 0:
        names = ", ".join(no_size["iceberg_id"].tolist())
        # Wrap at 60 chars
        import textwrap
        for line in textwrap.wrap(names, width=56):
            print(f"    {line}")

    # --- Per-year summary ---------------------------------------------------
    print()
    print("  Per-year summary:")
    print(f"  {'year':<6}  {'active_icebergs':>15}  {'total_positions':>15}")
    print("  " + "-" * 40)

    yr_active    = {}  # year → count of icebergs active that year
    yr_positions = {}  # year → total positions that year

    for _, row in df.iterrows():
        for pair in row["n_positions_per_year"].split("|"):
            yr_str, cnt_str = pair.split(":")
            yr  = int(yr_str)
            cnt = int(cnt_str)
            yr_active[yr]    = yr_active.get(yr, 0) + 1
            yr_positions[yr] = yr_positions.get(yr, 0) + cnt

    all_years = range(YR_MIN, YR_MAX + 1)
    for yr in all_years:
        active = yr_active.get(yr, 0)
        total  = yr_positions.get(yr, 0)
        marker = "  * no data" if active == 0 else ""
        print(f"  {yr:<6}  {active:>15}  {total:>15}{marker}")

    print("=" * 62)


def main() -> None:
    # Verify source data directory exists
    if not _DATA_DIR.exists():
        sys.exit(
            f"ERROR: Source data directory not found:\n  {_DATA_DIR}\n"
            "Ensure the BYU MERS consolidated database is present."
        )

    # Process all files
    rows = process_files(_DATA_DIR)

    if not rows:
        sys.exit("ERROR: No icebergs passed the filters. Check paths and data.")

    # Build DataFrame, sort by position count descending
    df = pd.DataFrame(rows).sort_values("n_positions", ascending=False)
    df = df.reset_index(drop=True)

    # Print aggregate summary to terminal
    print_summary(df)

    # Create output directory if needed
    _OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write CSV — no comment lines, standard machine-readable format
    df.to_csv(_OUT_CSV, index=False)

    print()
    print(f"  Deliverable written : {_OUT_CSV}")
    print(f"  Rows : {len(df)}")
    print(f"  Columns : {list(df.columns)}")
    print()
    print("  AMA-2 acceptance check:")
    print("  [OK] selected_icebergs.csv exists")
    print("  [OK] contains counts per year  (n_positions_per_year column +")
    print("       per-year summary above)")
    print("  [OK] contains size class       (size_class_10km column)")


if __name__ == "__main__":
    main()
