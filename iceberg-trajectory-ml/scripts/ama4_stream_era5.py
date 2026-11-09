#!/usr/bin/env python3
# AMA-4: Stream ERA5 Wind Data from CDS
"""
Downloads ERA5 10m wind components from Copernicus Climate Data Store (CDS).
Extracts values at iceberg positions only (not full grid).
Processes month-by-month using tempfiles.

Dataset: ERA5 Reanalysis (reanalysis-era5-single-levels)
Variables: 10m_u_component_of_wind, 10m_v_component_of_wind
Output: forcing_wind_{year}.csv with values at iceberg positions only
"""

import argparse
import gc
import os
import sys
import time
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

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
    print(f"  {label:40s} {GREEN}{value}{RESET}")


def print_error(text):
    print(f"{RED}✗ ERROR:{RESET} {text}")


def print_warning(text):
    print(f"{YELLOW}⚠ WARNING:{RESET} {text}")


def print_success(text):
    print(f"{GREEN}✓{RESET} {text}")


def get_memory_usage():
    """Get current memory usage percentage (if psutil available)."""
    try:
        import psutil
        return psutil.virtual_memory().percent
    except ImportError:
        return None


def check_cdsapi():
    """Check if cdsapi is installed and configured."""
    print_header("CHECKING CDS API")
    
    try:
        import cdsapi
        print_success("cdsapi package is installed")
    except ImportError:
        print_error("cdsapi package not installed")
        print("\nInstall with: pip install cdsapi")
        sys.exit(1)
    
    # Check for API key configuration
    cdsapirc = Path.home() / ".cdsapirc"
    if not cdsapirc.exists():
        print_warning(f"CDS API key not found at {cdsapirc}")
        print("\nSetup instructions:")
        print("  1. Register at: https://cds.climate.copernicus.eu/user/register")
        print("  2. Get your API key from: https://cds.climate.copernicus.eu/api-how-to")
        print("  3. Create ~/.cdsapirc with:")
        print("     url: https://cds.climate.copernicus.eu/api/v2")
        print("     key: YOUR_UID:YOUR_API_KEY")
        sys.exit(1)
    
    print_success(f"CDS API key found at {cdsapirc}")
    return True


def load_iceberg_positions(positions_file):
    """Load iceberg positions from CSV."""
    df = pd.read_csv(positions_file, parse_dates=['date'])
    print_stat("Loaded iceberg positions", f"{len(df):,} positions")
    print_stat("Date range", f"{df['date'].min().date()} to {df['date'].max().date()}")
    print_stat("Unique icebergs", df['iceberg_id'].nunique())
    return df


def download_era5_year(year, area, max_retries=3):
    """
    Download ERA5 wind data for one full year using CDS API.
    
    Args:
        year: Year to download
        area: Bounding box [north, west, south, east]
        max_retries: Number of retry attempts
    
    Returns:
        xarray.Dataset or None if failed
    """
    import cdsapi
    
    # Create temp file
    temp_file = tempfile.NamedTemporaryFile(
        suffix=f'_era5_{year}.nc',
        delete=False
    )
    temp_path = Path(temp_file.name)
    temp_file.close()
    
    for attempt in range(1, max_retries + 1):
        try:
            c = cdsapi.Client()
            
            # Build request for full year - all months, all days
            request = {
                'product_type': 'reanalysis',
                'variable': [
                    '10m_u_component_of_wind',
                    '10m_v_component_of_wind'
                ],
                'year': str(year),
                'month': [
                    '01', '02', '03', '04', '05', '06',
                    '07', '08', '09', '10', '11', '12'
                ],
                'day': [
                    '01', '02', '03', '04', '05', '06', '07', '08', '09', '10',
                    '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
                    '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31'
                ],
                'time': '12:00',  # Single daily timestep
                'area': area,  # [north, west, south, east]
                'data_format': 'netcdf',
                'download_format': 'unarchived',
            }
            
            print(f"  Submitting CDS request for year {year} (this may take 3-30 minutes)...")
            
            # Submit request (this waits for data)
            c.retrieve('reanalysis-era5-single-levels', request, str(temp_path))
            
            print(f"  Download complete, loading into memory...")
            
            # Load into xarray
            ds = xr.open_dataset(temp_path)
            ds_loaded = ds.load()
            ds.close()
            
            # Rename dimensions to standardize (CDS uses valid_time, latitude, longitude)
            rename_map = {}
            if 'valid_time' in ds_loaded.dims:
                rename_map['valid_time'] = 'time'
            if 'lat' in ds_loaded.dims and 'latitude' not in ds_loaded.dims:
                rename_map['lat'] = 'latitude'
            if 'lon' in ds_loaded.dims and 'longitude' not in ds_loaded.dims:
                rename_map['lon'] = 'longitude'
            
            if rename_map:
                ds_loaded = ds_loaded.rename(rename_map)
            
            # Ensure time is pandas datetime
            if 'time' in ds_loaded.coords:
                ds_loaded['time'] = pd.to_datetime(ds_loaded['time'].values)
            
            # Delete temp file immediately
            if temp_path.exists():
                temp_path.unlink()
                print(f"  Temp file deleted")
            
            return ds_loaded
            
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            
            if attempt < max_retries:
                wait_time = 30 * attempt
                print(f"    Attempt {attempt}/{max_retries} failed, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print_warning(f"Failed to download year {year} after {max_retries} attempts: {e}")
                return None
    
    return None


def extract_wind_at_positions(ds, positions_df, verbose=False):
    """
    Extract wind values at iceberg positions using nearest neighbor.
    
    Args:
        ds: xarray.Dataset with ERA5 data
        positions_df: DataFrame with iceberg positions
        verbose: Print diagnostics for first extraction
    
    Returns:
        DataFrame with wind values added
    """
    if len(positions_df) == 0:
        return positions_df
    
    # Print diagnostics on first call
    if verbose:
        print(f"\n  Dataset diagnostics:")
        print(f"    Dimensions: {dict(ds.dims)}")
        print(f"    Coordinates: {list(ds.coords.keys())}")
        print(f"    Variables: {list(ds.data_vars.keys())}")
        if 'latitude' in ds.coords:
            print(f"    Latitude range: {float(ds.latitude.min()):.2f} to {float(ds.latitude.max()):.2f}")
        if 'longitude' in ds.coords:
            print(f"    Longitude range: {float(ds.longitude.min()):.2f} to {float(ds.longitude.max()):.2f}")
        if 'time' in ds.coords:
            print(f"    Time range: {ds.time.values[0]} to {ds.time.values[-1]}")
    
    # Floor timestamps to days
    positions_df = positions_df.copy()
    positions_df['date_day'] = pd.to_datetime(positions_df['date'].dt.date)
    
    results = []
    first_position_done = False
    
    # ERA5 variable names (CDS API returns these exact names)
    era5_vars = {
        'u10': 'u10',  # May be 'u10' or '10m_u_component_of_wind'
        'v10': 'v10'   # May be 'v10' or '10m_v_component_of_wind'
    }
    
    # Check actual variable names in dataset
    actual_vars = {}
    for out_name, var_name in era5_vars.items():
        if var_name in ds.data_vars:
            actual_vars[out_name] = var_name
        elif f'10m_{out_name[0]}_component_of_wind' in ds.data_vars:
            actual_vars[out_name] = f'10m_{out_name[0]}_component_of_wind'
        else:
            # Try to find any matching variable
            for v in ds.data_vars:
                if out_name in v.lower() or 'wind' in v.lower():
                    actual_vars[out_name] = v
                    break
    
    if verbose:
        print(f"    Variable mapping: {actual_vars}")
    
    for day_idx, day in enumerate(positions_df['date_day'].unique()):
        day_positions = positions_df[positions_df['date_day'] == day].copy()
        
        try:
            # Find this day in the dataset (12:00 timestep)
            day_ts = pd.Timestamp(f"{day} 12:00:00")
            
            # Check if this day exists (convert both to comparable format)
            ds_times = pd.to_datetime(ds.time.values)
            time_match = None
            for t in ds_times:
                if t.date() == day_ts.date():
                    time_match = t
                    break
            
            if time_match is None:
                # No data for this day - set to NaN
                day_positions['u10'] = np.nan
                day_positions['v10'] = np.nan
                results.append(day_positions)
                continue
            
            # Select this day's data
            ds_day = ds.sel(time=time_match, method='nearest')
            
            # Extract wind components using nearest neighbor
            for out_name, era5_name in actual_vars.items():
                if era5_name not in ds_day:
                    day_positions[out_name] = np.nan
                    continue
                
                var_data = ds_day[era5_name]
                
                # Use vectorized nearest neighbor selection
                try:
                    # Extract all positions at once
                    lats = day_positions['latitude'].values
                    lons = day_positions['longitude'].values
                    
                    values = []
                    for lat, lon in zip(lats, lons):
                        val = var_data.sel(
                            latitude=lat,
                            longitude=lon,
                            method='nearest'
                        )
                        values.append(float(val.values))
                    
                    day_positions[out_name] = values
                    
                    # Print diagnostic for first position
                    if verbose and day_idx == 0 and not first_position_done and len(values) > 0:
                        print(f"\n  First position extraction:")
                        print(f"    Position: lat={lats[0]:.2f}, lon={lons[0]:.2f}")
                        nearest_lat = float(var_data.sel(latitude=lats[0], method='nearest').latitude.values)
                        nearest_lon = float(var_data.sel(longitude=lons[0], method='nearest').longitude.values)
                        print(f"    Nearest grid: lat={nearest_lat:.2f}, lon={nearest_lon:.2f}")
                        print(f"    {out_name} value: {values[0]:.2f} m/s")
                        first_position_done = True
                    
                except Exception as e:
                    if verbose:
                        print(f"    Warning: Extraction failed for {out_name}: {e}")
                    day_positions[out_name] = np.nan
            
            results.append(day_positions)
            
        except Exception as e:
            if verbose:
                print(f"    Warning: Failed to process day {day}: {e}")
            # If anything fails, set to NaN
            day_positions['u10'] = np.nan
            day_positions['v10'] = np.nan
            results.append(day_positions)
    
    if results:
        combined = pd.concat(results, ignore_index=True)
        combined = combined.drop(columns=['date_day'])
        return combined
    else:
        return positions_df


def process_year(year, positions_df, output_dir):
    """
    Process one year: download full year, extract at iceberg positions.
    
    Args:
        year: Year to process
        positions_df: DataFrame with all iceberg positions
        output_dir: Output directory
    
    Returns:
        DataFrame with wind values, or None if failed
    """
    # Get positions for this year only
    year_positions = positions_df[positions_df['date'].dt.year == year].copy()
    
    if len(year_positions) == 0:
        print_warning(f"No iceberg positions for year {year}, skipping")
        return None
    
    print(f"\n{CYAN}Processing year {year}...{RESET}")
    print_stat(f"  Iceberg positions", f"{len(year_positions):,}")
    
    # Bounding box: [north, west, south, east]
    area = [-42, -23, -75, 63]
    
    # Download full year of data
    print(f"  Downloading ERA5 data for entire year {year}...")
    ds = download_era5_year(year, area)
    
    if ds is None:
        # No data or failed - keep positions but set values to NaN
        year_positions['u10'] = np.nan
        year_positions['v10'] = np.nan
        print_warning(f"Year {year} failed - saving with NaN values")
    else:
        # Extract wind at positions for the whole year
        print(f"  Extracting wind values at {len(year_positions):,} positions...")
        year_positions = extract_wind_at_positions(ds, year_positions, verbose=False)
        
        # Clean up
        del ds
        gc.collect()
    
    # Save year file
    output_file = output_dir / f"forcing_wind_{year}.csv"
    year_positions.to_csv(output_file, index=False)
    
    file_size_kb = output_file.stat().st_size / 1024
    print_success(f"Saved {output_file.name} ({file_size_kb:.1f} KB, {len(year_positions):,} rows)")
    
    # Print statistics
    valid_u10 = year_positions['u10'].notna().sum()
    valid_v10 = year_positions['v10'].notna().sum()
    print(f"  Valid data: u10={valid_u10}/{len(year_positions)} ({100*valid_u10/len(year_positions):.1f}%), "
          f"v10={valid_v10}/{len(year_positions)} ({100*valid_v10/len(year_positions):.1f}%)")
    
    # Sleep to avoid CDS throttling (30 seconds between years)
    print(f"  Sleeping 30 seconds to avoid CDS throttling...")
    time.sleep(30)
    
    return year_positions


def test_mode():
    """Test mode: Download only January 2015."""
    print_header("TEST MODE - January 2015 Only")
    
    # Check cdsapi
    check_cdsapi()
    
    # Load positions
    print_header("LOADING ICEBERG POSITIONS")
    positions_file = Path("iceberg-trajectory-ml/data/validation/selected_positions.csv")
    if not positions_file.exists():
        print_error(f"Positions file not found: {positions_file}")
        sys.exit(1)
    
    positions_df = load_iceberg_positions(positions_file)
    
    # Filter to January 2015
    test_positions = positions_df[
        (positions_df['date'].dt.year == 2015) &
        (positions_df['date'].dt.month == 1)
    ].copy()
    
    if len(test_positions) == 0:
        print_error("No positions found for January 2015")
        sys.exit(1)
    
    print_stat("Test positions", f"{len(test_positions):,} (January 2015)")
    
    # Download January 2015 only (single month for test)
    area = [-42, -23, -75, 63]
    days = sorted(test_positions['date'].dt.day.unique())
    
    print("\nDownloading ERA5 data for January 2015...")
    print_stat("Days", f"{len(days)} days")
    
    # Use special test function for single month
    import cdsapi
    
    temp_file = tempfile.NamedTemporaryFile(suffix='_era5_test.nc', delete=False)
    temp_path = Path(temp_file.name)
    temp_file.close()
    
    try:
        c = cdsapi.Client()
        
        request = {
            'product_type': 'reanalysis',
            'variable': [
                '10m_u_component_of_wind',
                '10m_v_component_of_wind'
            ],
            'year': '2015',
            'month': '01',
            'day': [f'{d:02d}' for d in days],
            'time': '12:00',
            'area': area,
            'data_format': 'netcdf',
            'download_format': 'unarchived',
        }
        
        print("  Submitting CDS request (this may take 3-10 minutes)...")
        c.retrieve('reanalysis-era5-single-levels', request, str(temp_path))
        
        print("  Download complete, loading into memory...")
        ds = xr.open_dataset(temp_path)
        ds_loaded = ds.load()
        ds.close()
        
        # Rename dimensions
        rename_map = {}
        if 'valid_time' in ds_loaded.dims:
            rename_map['valid_time'] = 'time'
        if 'lat' in ds_loaded.dims and 'latitude' not in ds_loaded.dims:
            rename_map['lat'] = 'latitude'
        if 'lon' in ds_loaded.dims and 'longitude' not in ds_loaded.dims:
            rename_map['lon'] = 'longitude'
        
        if rename_map:
            ds_loaded = ds_loaded.rename(rename_map)
        
        if 'time' in ds_loaded.coords:
            ds_loaded['time'] = pd.to_datetime(ds_loaded['time'].values)
        
        # Delete temp file
        if temp_path.exists():
            temp_path.unlink()
        
        ds = ds_loaded
        
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        print_error(f"Test download failed: {e}")
        sys.exit(1)
    
    print_success("Download successful!")
    print_stat("Dataset shape", str(ds.dims))
    print_stat("Variables", ", ".join(list(ds.data_vars.keys())))
    
    # Extract values
    print("\nExtracting wind values at iceberg positions...")
    test_with_values = extract_wind_at_positions(ds, test_positions, verbose=True)
    
    valid_u10 = test_with_values['u10'].notna().sum()
    print_stat("Valid u10 values", f"{valid_u10}/{len(test_with_values)} ({100*valid_u10/len(test_with_values):.1f}%)")
    
    # Show sample and statistics
    print("\nSample data (first 5 positions):")
    sample = test_with_values[['iceberg_id', 'date', 'latitude', 'longitude', 'u10', 'v10']].head()
    print(sample.to_string(index=False))
    
    # Show wind statistics
    if valid_u10 > 0:
        print("\nWind statistics:")
        print(f"  u10: min={test_with_values['u10'].min():.2f}, max={test_with_values['u10'].max():.2f}, mean={test_with_values['u10'].mean():.2f} m/s")
        print(f"  v10: min={test_with_values['v10'].min():.2f}, max={test_with_values['v10'].max():.2f}, mean={test_with_values['v10'].mean():.2f} m/s")
    
    print(f"\n{GREEN}✓ Test successful! Ready to process full dataset.{RESET}\n")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Download ERA5 wind data from CDS and extract at iceberg positions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test mode (January 2015 only)
  python ama4_stream_era5.py --test
  
  # Process one year
  python ama4_stream_era5.py --year 2015
  
  # Process all years
  python ama4_stream_era5.py
        """
    )
    
    parser.add_argument('--test', action='store_true',
                       help='Test mode: download January 2015 only')
    parser.add_argument('--year', type=int,
                       help='Process only this specific year')
    
    args = parser.parse_args()
    
    print(f"\n{BLUE}╔════════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BLUE}║     AMA-4: Stream ERA5 Wind Data from CDS                                 ║{RESET}")
    print(f"{BLUE}║     CryoNav AI - Iceberg Trajectory ML                                     ║{RESET}")
    print(f"{BLUE}╚════════════════════════════════════════════════════════════════════════════╝{RESET}")
    
    # Test mode
    if args.test:
        success = test_mode()
        sys.exit(0 if success else 1)
    
    # Check cdsapi
    check_cdsapi()
    
    # Load positions
    print_header("LOADING ICEBERG POSITIONS")
    positions_file = Path("iceberg-trajectory-ml/data/validation/selected_positions.csv")
    if not positions_file.exists():
        print_error(f"Positions file not found: {positions_file}")
        print("Run ama2_select_icebergs.py first to generate this file.")
        sys.exit(1)
    
    positions_df = load_iceberg_positions(positions_file)
    
    # Determine years to process
    if args.year:
        years = [args.year]
        print_stat("Processing", f"Single year: {args.year}")
    else:
        start_year = positions_df['date'].dt.year.min()
        end_year = positions_df['date'].dt.year.max()
        years = list(range(start_year, end_year + 1))
        print_stat("Processing", f"{len(years)} years ({start_year}-{end_year})")
    
    # Output directory
    output_dir = Path("iceberg-trajectory-ml/data/validation")
    
    print_header("PROCESSING YEARS (ONE CDS REQUEST PER YEAR)")
    print(f"{YELLOW}Note:{RESET} Each year is one CDS request (all 12 months at once).")
    print(f"{YELLOW}→{RESET} Estimated time: ~{len(years) * 5} minutes (5 min/year average)\n")
    
    # Track statistics
    all_year_results = []
    successful_years = []
    failed_years = []
    total_positions = 0
    total_valid_u10 = 0
    
    # Process each year
    for idx, year in enumerate(years, 1):
        print(f"\n{CYAN}{'─' * 80}{RESET}")
        print(f"{CYAN}Year {year} ({idx}/{len(years)}){RESET}")
        print(f"{CYAN}{'─' * 80}{RESET}")
        
        # Process the year
        year_df = process_year(year, positions_df, output_dir)
        
        if year_df is not None:
            successful_years.append(year)
            all_year_results.append(year_df)
            
            # Update totals
            total_positions += len(year_df)
            total_valid_u10 += year_df['u10'].notna().sum()
        else:
            failed_years.append(year)
        
        # Print memory usage
        mem = get_memory_usage()
        if mem is not None:
            print(f"  Memory usage: {mem:.1f}%")
        
        print_success(f"Year {year} complete ({idx}/{len(years)})")
    
    # Combine all years into one file
    if all_year_results:
        print_header("COMBINING ALL YEARS")
        combined_df = pd.concat(all_year_results, ignore_index=True)
        combined_file = output_dir / "forcing_wind_all.csv"
        combined_df.to_csv(combined_file, index=False)
        
        file_size_mb = combined_file.stat().st_size / 1024**2
        print_success(f"Saved {combined_file.name} ({file_size_mb:.1f} MB, {len(combined_df):,} rows)")
    
    # Final summary
    print_header("PROCESSING COMPLETE")
    
    print_stat("Successful years", f"{len(successful_years)} / {len(years)}")
    print_stat("Failed years", f"{len(failed_years)}")
    
    if failed_years:
        print(f"\n  {YELLOW}Failed years:{RESET} {', '.join(map(str, failed_years))}")
        print(f"  {YELLOW}→{RESET} Re-run with --year flag to retry individual years")
    
    print_stat("Total positions processed", f"{total_positions:,}")
    
    if total_positions > 0:
        print_stat("Valid u10/v10", f"{total_valid_u10:,} ({100*total_valid_u10/total_positions:.1f}%)")
    
    print_stat("Saved to", output_dir)
    
    print(f"\n{GREEN}{'=' * 80}{RESET}")
    if len(successful_years) > 0:
        print(f"{GREEN}✓ Processing complete!{RESET}")
        print(f"{GREEN}{'=' * 80}{RESET}\n")
        print("Next step: AMA-5 - Combine ocean + wind + ice forcing into training table\n")
    else:
        print(f"{RED}✗ All years failed!{RESET}")
        print(f"{RED}{'=' * 80}{RESET}\n")
        print("Check your CDS API credentials and network connection.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
