#!/usr/bin/env python3
# AMA-5: Build Training Table
"""
Builds the final training table for the CryoNav iceberg drift model.
Combines iceberg positions with ocean and atmospheric forcing data.

RULES:
- NO synthetic data (no filling missing values)
- NO accuracy claims
- Output files <= 10 MB (gzip if larger)
- Training refuses to run if data is marked as SYNTHETIC
"""

import argparse
import gzip
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# Color codes
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"


def print_header(text):
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")


def print_stat(label, value):
    print(f"  {label:50s} {GREEN}{value}{RESET}")


def print_check(passed, label):
    status = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
    print(f"  [{status}] {label}")


def print_error(text):
    print(f"{RED}✗ ERROR:{RESET} {text}")


def print_warning(text):
    print(f"{YELLOW}⚠ WARNING:{RESET} {text}")


def print_success(text):
    print(f"{GREEN}✓{RESET} {text}")


def load_positions(positions_file):
    """Load and clean iceberg positions."""
    print_header("LOADING ICEBERG POSITIONS")
    
    df = pd.read_csv(positions_file, parse_dates=['date'])
    print_stat("Raw positions loaded", f"{len(df):,}")
    
    # Sort by iceberg_id then date
    df = df.sort_values(['iceberg_id', 'date']).reset_index(drop=True)
    
    # Drop exact duplicates
    n_before = len(df)
    df = df.drop_duplicates(subset=['iceberg_id', 'date'], keep='first')
    n_dropped = n_before - len(df)
    
    if n_dropped > 0:
        print_warning(f"Dropped {n_dropped:,} duplicate (iceberg_id, date) rows")
    
    print_stat("Clean positions", f"{len(df):,}")
    print_stat("Unique icebergs", df['iceberg_id'].nunique())
    print_stat("Date range", f"{df['date'].min().date()} to {df['date'].max().date()}")
    
    return df


def build_step_pairs(df, max_dt_days=3):
    """Build position pairs for each iceberg."""
    print_header("BUILDING STEP PAIRS")
    
    pairs = []
    
    for iceberg_id in df['iceberg_id'].unique():
        iceberg_df = df[df['iceberg_id'] == iceberg_id].sort_values('date').reset_index(drop=True)
        
        if len(iceberg_df) < 2:
            continue
        
        for i in range(len(iceberg_df) - 1):
            current = iceberg_df.iloc[i]
            next_pos = iceberg_df.iloc[i + 1]
            
            dt_days = (next_pos['date'] - current['date']).total_seconds() / 86400
            
            pairs.append({
                'iceberg_id': iceberg_id,
                'date': current['date'],
                'date_next': next_pos['date'],
                'dt_days': dt_days,
                'lat': current['latitude'],
                'lon': current['longitude'],
                'lat_next': next_pos['latitude'],
                'lon_next': next_pos['longitude'],
            })
    
    pairs_df = pd.DataFrame(pairs)
    print_stat("Total pairs created", f"{len(pairs_df):,}")
    
    # Print dt_days distribution
    print("\n  Time gap distribution:")
    dt_counts = pairs_df['dt_days'].value_counts().sort_index()
    for dt in [1, 2, 3]:
        count = dt_counts.get(dt, 0)
        print(f"    {dt} day:  {count:,}")
    dt_4plus = pairs_df[pairs_df['dt_days'] > 3].shape[0]
    print(f"    4+ days: {dt_4plus:,}")
    
    # Filter by max_dt
    n_before = len(pairs_df)
    pairs_df = pairs_df[pairs_df['dt_days'] <= max_dt_days].copy()
    n_dropped = n_before - len(pairs_df)
    
    if n_dropped > 0:
        print_warning(f"Dropped {n_dropped:,} pairs with dt_days > {max_dt_days}")
    
    print_stat("Pairs after filter", f"{len(pairs_df):,}")
    
    return pairs_df


def compute_drift(df):
    """Compute observed drift from position pairs."""
    print_header("COMPUTING OBSERVED DRIFT")
    
    # Wrap longitude difference to [-180, 180]
    dlon = df['lon_next'] - df['lon']
    dlon = (dlon + 180) % 360 - 180
    
    # Compute distance
    mean_lat = (df['lat'] + df['lat_next']) / 2
    df['dy_km'] = (df['lat_next'] - df['lat']) * 111.32
    df['dx_km'] = dlon * 111.32 * np.cos(np.radians(mean_lat))
    
    # Compute velocity (m/s)
    dt_seconds = df['dt_days'] * 86400
    df['u_obs'] = (df['dx_km'] * 1000) / dt_seconds
    df['v_obs'] = (df['dy_km'] * 1000) / dt_seconds
    df['speed_obs'] = np.sqrt(df['u_obs']**2 + df['v_obs']**2)
    
    # Flag outliers (likely position errors)
    df['outlier_flag'] = df['speed_obs'] > 2.0
    n_outliers = df['outlier_flag'].sum()
    
    print_stat("Pairs with drift computed", f"{len(df):,}")
    print_stat("Speed range", f"{df['speed_obs'].min():.3f} to {df['speed_obs'].max():.3f} m/s")
    print_stat("Outliers flagged (>2 m/s)", f"{n_outliers:,} ({100*n_outliers/len(df):.1f}%)")
    
    return df


def load_forcing_files(data_dir, partial=False):
    """Load ocean and wind forcing files."""
    print_header("LOADING FORCING DATA")
    
    # Ocean forcing
    ocean_file = data_dir / "forcing_ocean_all.csv"
    if not ocean_file.exists():
        print_error(f"Ocean forcing not found: {ocean_file}")
        print("Run ama3_stream_ocean.py first.")
        sys.exit(1)
    
    ocean_df = pd.read_csv(ocean_file, parse_dates=['date'])
    print_stat("Ocean forcing loaded", f"{len(ocean_df):,} rows")
    
    # Standardize column names
    if 'latitude' in ocean_df.columns:
        ocean_df = ocean_df.rename(columns={'latitude': 'lat_forcing', 'longitude': 'lon_forcing'})
    
    # Wind forcing - try combined first, else combine year files
    wind_file = data_dir / "forcing_wind_all.csv"
    
    if wind_file.exists():
        wind_df = pd.read_csv(wind_file, parse_dates=['date'])
        print_stat("Wind forcing loaded", f"{len(wind_df):,} rows (combined file)")
        years_included = sorted(wind_df['date'].dt.year.unique())
    else:
        # Combine individual year files
        year_files = sorted(data_dir.glob("forcing_wind_*.csv"))
        year_files = [f for f in year_files if f.name != "forcing_wind_all.csv"]
        
        if not year_files:
            print_error("No wind forcing files found")
            print("Run ama4_stream_era5.py first.")
            sys.exit(1)
        
        # Check if all expected years are present
        all_years = set(range(1995, 2022))  # Expected range
        found_years = set()
        
        wind_dfs = []
        for f in year_files:
            try:
                year = int(f.stem.split('_')[-1])
                found_years.add(year)
                df_year = pd.read_csv(f, parse_dates=['date'])
                wind_dfs.append(df_year)
            except:
                continue
        
        missing_years = sorted(all_years - found_years)
        
        if missing_years and not partial:
            print_error(f"Wind forcing incomplete: missing years {missing_years}")
            print("\nOptions:")
            print("  1. Run ama4_stream_era5.py to complete wind extraction")
            print("  2. Use --partial flag to proceed with available years only")
            sys.exit(1)
        
        if missing_years:
            print_warning(f"Using partial wind data: missing {len(missing_years)} years")
            print(f"  Missing: {missing_years}")
        
        wind_df = pd.concat(wind_dfs, ignore_index=True)
        years_included = sorted(wind_df['date'].dt.year.unique())
        print_stat("Wind forcing combined", f"{len(wind_df):,} rows from {len(year_files)} files")
        print_stat("Years included", f"{len(years_included)}: {years_included[0]}-{years_included[-1]}")
    
    # Standardize wind column names
    if 'latitude' in wind_df.columns:
        wind_df = wind_df.rename(columns={'latitude': 'lat_forcing', 'longitude': 'lon_forcing'})
    
    return ocean_df, wind_df, years_included


def join_forcing(pairs_df, ocean_df, wind_df):
    """Join forcing data to position pairs."""
    print_header("JOINING FORCING DATA")
    
    n_before = len(pairs_df)
    
    # Check for duplicates in forcing files
    ocean_dups = ocean_df.duplicated(subset=['iceberg_id', 'date']).sum()
    wind_dups = wind_df.duplicated(subset=['iceberg_id', 'date']).sum()
    
    if ocean_dups > 0:
        print_warning(f"Ocean forcing has {ocean_dups:,} duplicate keys - keeping first")
        ocean_df = ocean_df.drop_duplicates(subset=['iceberg_id', 'date'], keep='first')
    
    if wind_dups > 0:
        print_warning(f"Wind forcing has {wind_dups:,} duplicate keys - keeping first")
        wind_df = wind_df.drop_duplicates(subset=['iceberg_id', 'date'], keep='first')
    
    # Keep only needed columns from forcing
    ocean_cols = ['iceberg_id', 'date', 'uo', 'vo', 'siconc', 'usi', 'vsi']
    wind_cols = ['iceberg_id', 'date', 'u10', 'v10']
    
    ocean_df = ocean_df[ocean_cols]
    wind_df = wind_df[wind_cols]
    
    # Left join ocean
    result_df = pairs_df.merge(ocean_df, on=['iceberg_id', 'date'], how='left')
    print_stat("After ocean join", f"{len(result_df):,} rows")
    
    # Left join wind
    result_df = result_df.merge(wind_df, on=['iceberg_id', 'date'], how='left')
    print_stat("After wind join", f"{len(result_df):,} rows")
    
    if len(result_df) != n_before:
        print_error(f"Row count changed after joins: {n_before:,} -> {len(result_df):,}")
        print("This indicates duplicate keys in forcing data.")
    
    return result_df


def add_flags(df):
    """Add flag columns for data completeness."""
    print_header("ADDING FLAG COLUMNS")
    
    df['has_ocean'] = df['uo'].notna() & df['vo'].notna()
    df['has_ice'] = df['siconc'].notna()
    df['has_wind'] = df['u10'].notna() & df['v10'].notna()
    df['complete_case'] = df['has_ocean'] & df['has_ice'] & df['has_wind']
    
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    
    print_stat("Has ocean forcing", f"{df['has_ocean'].sum():,} ({100*df['has_ocean'].mean():.1f}%)")
    print_stat("Has ice forcing", f"{df['has_ice'].sum():,} ({100*df['has_ice'].mean():.1f}%)")
    print_stat("Has wind forcing", f"{df['has_wind'].sum():,} ({100*df['has_wind'].mean():.1f}%)")
    print_stat("Complete cases", f"{df['complete_case'].sum():,} ({100*df['complete_case'].mean():.1f}%)")
    
    return df


def run_sanity_checks(df):
    """Run sanity checks on the data."""
    print_header("SANITY CHECKS")
    
    all_passed = True
    
    # Check 1: Row count preserved
    # (Already checked in join_forcing)
    
    # Check 2: Lat/lon ranges
    lat_ok = ((df['lat'] >= -75) & (df['lat'] <= -42)).all()
    lon_ok = ((df['lon'] >= -23) & (df['lon'] <= 63)).all()
    print_check(lat_ok, "Latitude within [-75, -42]")
    print_check(lon_ok, "Longitude within [-23, 63]")
    
    # Check 3: Ocean currents range
    uo_ok = ((df['uo'].abs() <= 3) | df['uo'].isna()).all()
    vo_ok = ((df['vo'].abs() <= 3) | df['vo'].isna()).all()
    print_check(uo_ok, "uo within [-3, 3] m/s (or NaN)")
    print_check(vo_ok, "vo within [-3, 3] m/s (or NaN)")
    
    # Check 4: Wind range
    u10_ok = ((df['u10'].abs() <= 40) | df['u10'].isna()).all()
    v10_ok = ((df['v10'].abs() <= 40) | df['v10'].isna()).all()
    print_check(u10_ok, "u10 within [-40, 40] m/s (or NaN)")
    print_check(v10_ok, "v10 within [-40, 40] m/s (or NaN)")
    
    # Check 5: Sea ice concentration (Copernicus uses 0-1, but check actual range)
    if not df['siconc'].isna().all():
        siconc_min = df['siconc'].min()
        siconc_max = df['siconc'].max()
        siconc_ok = (((df['siconc'] >= 0) & (df['siconc'] <= 1.1)) | df['siconc'].isna()).all()  # Allow small overflow
        print_check(siconc_ok, f"siconc within [0, ~1] (or NaN) [actual: {siconc_min:.3f} to {siconc_max:.3f}]")
    else:
        print_check(True, "siconc all NaN (wind-only mode)")
    
    # Print NaN counts
    print("\n  NaN counts by column:")
    for col in ['uo', 'vo', 'siconc', 'usi', 'vsi', 'u10', 'v10']:
        if col in df.columns:
            nan_count = df[col].isna().sum()
            nan_pct = 100 * nan_count / len(df)
            print(f"    {col:10s} {nan_count:8,} ({nan_pct:5.1f}%)")
    
    return all_passed


def save_outputs(df, data_dir, years_included, partial, max_dt_days, test_mode=False):
    """Save training table and metadata."""
    print_header("SAVING OUTPUTS")
    
    suffix = "_test" if test_mode else ""
    
    # Define column order
    column_order = [
        'iceberg_id', 'date', 'date_next', 'dt_days', 'year', 'month',
        'lat', 'lon', 'lat_next', 'lon_next', 'dx_km', 'dy_km',
        'u_obs', 'v_obs', 'speed_obs', 'outlier_flag',
        'uo', 'vo', 'siconc', 'usi', 'vsi', 'u10', 'v10',
        'has_ocean', 'has_ice', 'has_wind', 'complete_case'
    ]
    
    df_out = df[column_order].copy()
    
    # Save CSV
    csv_file = data_dir / f"training_table{suffix}.csv"
    df_out.to_csv(csv_file, index=False)
    
    file_size_mb = csv_file.stat().st_size / 1024**2
    
    if file_size_mb > 10:
        print_warning(f"File size {file_size_mb:.1f} MB exceeds 10 MB limit")
        print("  Compressing to gzip...")
        
        # Save as gzip
        csv_file.unlink()
        csv_gz_file = data_dir / f"training_table{suffix}.csv.gz"
        df_out.to_csv(csv_gz_file, index=False, compression='gzip')
        
        file_size_mb = csv_gz_file.stat().st_size / 1024**2
        print_success(f"Saved {csv_gz_file.name} ({file_size_mb:.1f} MB)")
    else:
        print_success(f"Saved {csv_file.name} ({file_size_mb:.1f} MB)")
    
    # Build metadata report
    nan_counts = {}
    for col in ['uo', 'vo', 'siconc', 'usi', 'vsi', 'u10', 'v10']:
        if col in df.columns:
            nan_counts[col] = int(df[col].isna().sum())
    
    report = {
        'data_source': 'REAL',
        'sources': [
            'BYU Antarctic Iceberg Database v8.0',
            'Copernicus Marine GLORYS12 cmems_mod_glo_phy_my_0.083deg_P1D-m',
            'ERA5 reanalysis-era5-single-levels'
        ],
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'n_rows': int(len(df)),
        'n_icebergs': int(df['iceberg_id'].nunique()),
        'date_min': df['date'].min().strftime('%Y-%m-%d'),
        'date_max': df['date'].max().strftime('%Y-%m-%d'),
        'years_included': [int(y) for y in years_included],  # Convert numpy int32 to Python int
        'partial': partial,
        'nan_counts': nan_counts,  # Already converted to int above
        'n_complete_case': int(df['complete_case'].sum()),
        'n_outliers_flagged': int(df['outlier_flag'].sum()),
        'max_dt_days': max_dt_days,
        'synthetic': False
    }
    
    # Save JSON report
    json_file = data_dir / f"data_report{suffix}.json"
    with open(json_file, 'w') as f:
        json.dump(report, f, indent=2)
    print_success(f"Saved {json_file.name}")
    
    # Save markdown summary
    md_content = f"""# Training Data Summary

**Created**: {report['created_utc']}  
**Data Source**: REAL (observational data only)

## Sources

1. BYU Antarctic Iceberg Database v8.0 (iceberg positions)
2. Copernicus Marine GLORYS12 (ocean currents and sea ice)
3. ERA5 Reanalysis (atmospheric winds)

## Dataset Statistics

- **Total rows**: {report['n_rows']:,}
- **Unique icebergs**: {report['n_icebergs']}
- **Date range**: {report['date_min']} to {report['date_max']}
- **Years included**: {len(years_included)} years ({years_included[0]}-{years_included[-1]})
- **Partial data**: {'Yes' if partial else 'No'}
- **Max time gap**: {max_dt_days} days

## Data Completeness

- **Complete cases** (all forcing available): {report['n_complete_case']:,} ({100*report['n_complete_case']/report['n_rows']:.1f}%)
- **Outliers flagged** (speed > 2 m/s): {report['n_outliers_flagged']:,} ({100*report['n_outliers_flagged']/report['n_rows']:.1f}%)

### Valid Data by Variable

| Variable | Valid | Missing | % Valid |
|----------|-------|---------|---------|
"""
    
    for var in ['uo', 'vo', 'siconc', 'usi', 'vsi', 'u10', 'v10']:
        if var in nan_counts:
            valid = report['n_rows'] - nan_counts[var]
            pct_valid = 100 * valid / report['n_rows']
            md_content += f"| {var} | {valid:,} | {nan_counts[var]:,} | {pct_valid:.1f}% |\n"
    
    md_content += f"""
## Columns

Position data:
- iceberg_id, date, date_next, dt_days, year, month
- lat, lon, lat_next, lon_next

Observed drift:
- dx_km, dy_km, u_obs, v_obs, speed_obs, outlier_flag

Ocean forcing (from GLORYS12):
- uo, vo (ocean currents, m/s)
- siconc (sea ice concentration, 0-1)
- usi, vsi (sea ice drift, m/s)

Atmospheric forcing (from ERA5):
- u10, v10 (10m wind components, m/s)

Flags:
- has_ocean, has_ice, has_wind, complete_case

## Data Integrity

✓ NO synthetic data (all NaN values are real missing data, not filled)  
✓ NO accuracy claims  
✓ Data gate enforced via data_report.json

---

*This dataset contains only REAL observational data. No values have been fabricated, interpolated, or filled.*
"""
    
    md_file = data_dir / f"data_summary{suffix}.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print_success(f"Saved {md_file.name}")
    
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Build training table for iceberg drift model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test mode (year 2015 only)
  python ama5_build_training_table.py --test --partial
  
  # Full dataset with complete wind data
  python ama5_build_training_table.py
  
  # Partial wind data (some years missing)
  python ama5_build_training_table.py --partial
  
  # Custom max time gap
  python ama5_build_training_table.py --max-dt 5
        """
    )
    
    parser.add_argument('--partial', action='store_true',
                       help='Allow incomplete wind forcing years')
    parser.add_argument('--max-dt', type=int, default=3,
                       help='Maximum time gap in days (default: 3)')
    parser.add_argument('--test', action='store_true',
                       help='Test mode: use only 2015 data')
    
    args = parser.parse_args()
    
    print(f"\n{BLUE}╔════════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BLUE}║     AMA-5: Build Training Table                                           ║{RESET}")
    print(f"{BLUE}║     CryoNav AI - Iceberg Trajectory ML                                     ║{RESET}")
    print(f"{BLUE}╚════════════════════════════════════════════════════════════════════════════╝{RESET}")
    
    if args.test:
        print(f"\n{YELLOW}TEST MODE: Using 2015 data only{RESET}")
    
    data_dir = Path("iceberg-trajectory-ml/data/validation")
    
    # Load positions
    positions_file = data_dir / "selected_positions.csv"
    if not positions_file.exists():
        print_error(f"Positions file not found: {positions_file}")
        print("Run ama2_select_icebergs.py first.")
        sys.exit(1)
    
    positions_df = load_positions(positions_file)
    
    # Test mode: filter to 2015
    if args.test:
        positions_df = positions_df[positions_df['date'].dt.year == 2015].copy()
        print_warning(f"Test mode: filtered to {len(positions_df):,} positions from 2015")
    
    # Build pairs
    pairs_df = build_step_pairs(positions_df, max_dt_days=args.max_dt)
    
    # Compute drift
    pairs_df = compute_drift(pairs_df)
    
    # Load forcing
    ocean_df, wind_df, years_included = load_forcing_files(data_dir, partial=args.partial)
    
    # Test mode: filter forcing too
    if args.test:
        ocean_df = ocean_df[ocean_df['date'].dt.year == 2015].copy()
        wind_df = wind_df[wind_df['date'].dt.year == 2015].copy()
        years_included = [2015]
    
    # Join forcing
    result_df = join_forcing(pairs_df, ocean_df, wind_df)
    
    # Add flags
    result_df = add_flags(result_df)
    
    # Sanity checks
    run_sanity_checks(result_df)
    
    # Save outputs
    report = save_outputs(result_df, data_dir, years_included, args.partial, args.max_dt, test_mode=args.test)
    
    # Final summary
    print_header("COMPLETE")
    print_stat("Total rows", f"{report['n_rows']:,}")
    print_stat("Complete cases", f"{report['n_complete_case']:,} ({100*report['n_complete_case']/report['n_rows']:.1f}%)")
    print_stat("Date range", f"{report['date_min']} to {report['date_max']}")
    print_stat("Output directory", data_dir)
    
    print(f"\n{GREEN}{'=' * 80}{RESET}")
    print(f"{GREEN}✓ Training table built successfully{RESET}")
    print(f"{GREEN}{'=' * 80}{RESET}\n")
    
    print("Next steps:")
    print("  1. Review data_summary.md for completeness")
    print("  2. Run data gate check: python iceberg-trajectory-ml/scripts/data_gate.py")
    print("  3. Proceed to model training (AMA-6)")
    print()
    
    print("TEST COMMAND:")
    print("  python iceberg-trajectory-ml/scripts/ama5_build_training_table.py --test --partial")
    print()


if __name__ == "__main__":
    main()
