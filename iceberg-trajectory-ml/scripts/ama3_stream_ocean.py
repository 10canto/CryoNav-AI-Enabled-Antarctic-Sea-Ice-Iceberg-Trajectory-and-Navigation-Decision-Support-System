#!/usr/bin/env python3
# AMA-3: Stream Ocean Data from Copernicus Marine
"""
Streams ocean currents and sea ice data from Copernicus Marine Service.
Extracts values at iceberg positions only (not full grid).
Processes month-by-month to minimize RAM usage.

Dataset: GLORYS12 (cmems_mod_glo_phy_my_0.083deg_P1D-m)
Variables: uo, vo (currents), siconc, usi, vsi (sea ice)
Output: forcing_ocean_{year}.csv with values at iceberg positions only
"""

import argparse
import gc
import os
import sys
import time
import yaml
from pathlib import Path
from datetime import datetime
import calendar

import numpy as np
import pandas as pd
import xarray as xr
import copernicusmarine

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


def load_config(config_path):
    """Load the download configuration."""
    print_header("LOADING CONFIGURATION")
    
    if not config_path.exists():
        print_error(f"Config file not found: {config_path}")
        print("Run ama2_define_region.py first to generate download_config.yaml")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    print_stat("Region", f"{config['region']['minimum_latitude']:.2f}° to "
                         f"{config['region']['maximum_latitude']:.2f}° lat")
    print_stat("", f"{config['region']['minimum_longitude']:.2f}° to "
                   f"{config['region']['maximum_longitude']:.2f}° lon")
    print_stat("Date range", f"{config['date_range']['start']} to {config['date_range']['end']}")
    print_stat("Estimated total", f"~{config['estimated_size_gb']} GB")
    
    return config


def load_iceberg_positions(positions_file):
    """Load iceberg positions from CSV."""
    df = pd.read_csv(positions_file, parse_dates=['date'])
    print_stat("Loaded iceberg positions", f"{len(df):,} positions")
    print_stat("Date range", f"{df['date'].min().date()} to {df['date'].max().date()}")
    print_stat("Unique icebergs", df['iceberg_id'].nunique())
    return df


def stream_month(year, month, config, max_retries=3):
    """
    Stream ocean data for one month from Copernicus Marine.
    
    Args:
        year: Year to stream
        month: Month to stream (1-12)
        config: Configuration dict with region
        max_retries: Number of retry attempts
    
    Returns:
        xarray.Dataset or None if failed
    """
    dataset_id = "cmems_mod_glo_phy_my_0.083deg_P1D-m"
    variables = ["uo", "vo", "siconc", "usi", "vsi"]
    
    # Get last day of month
    _, last_day = calendar.monthrange(year, month)
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"
    
    for attempt in range(1, max_retries + 1):
        try:
            # Get credentials from environment if available
            username = os.environ.get('COPERNICUSMARINE_SERVICE_USERNAME')
            password = os.environ.get('COPERNICUSMARINE_SERVICE_PASSWORD')
            
            # Build kwargs
            kwargs = {
                'dataset_id': dataset_id,
                'minimum_longitude': config['region']['minimum_longitude'],
                'maximum_longitude': config['region']['maximum_longitude'],
                'minimum_latitude': config['region']['minimum_latitude'],
                'maximum_latitude': config['region']['maximum_latitude'],
                'start_datetime': start_date,
                'end_datetime': end_date,
                'variables': variables,
                'minimum_depth': 0,
                'maximum_depth': 1,
            }
            
            # Add credentials if available
            if username and password:
                kwargs['username'] = username
                kwargs['password'] = password
            
            # Stream the data
            ds = copernicusmarine.open_dataset(**kwargs)
            
            # Check if we got any data
            if 'time' not in ds.dims or len(ds.time) == 0:
                print_warning(f"NO DATA for {year}-{month:02d}")
                ds.close()
                return None
            
            # Load into memory
            ds_loaded = ds.load()
            ds.close()
            
            return ds_loaded
            
        except Exception as e:
            if attempt < max_retries:
                wait_time = 30 * attempt
                print(f"    Attempt {attempt}/{max_retries} failed, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print_warning(f"Failed to stream {year}-{month:02d} after {max_retries} attempts: {e}")
                return None
    
    return None


def interpolate_to_positions(ds, positions_df):
    """
    Extract ocean values at iceberg positions using bilinear interpolation.
    
    Args:
        ds: xarray.Dataset with ocean data
        positions_df: DataFrame with iceberg positions (iceberg_id, date, latitude, longitude)
    
    Returns:
        DataFrame with ocean values added
    """
    if len(positions_df) == 0:
        return positions_df
    
    # Floor timestamps to days (exact day match, no nearest)
    positions_df = positions_df.copy()
    positions_df['date_day'] = pd.to_datetime(positions_df['date'].dt.date)
    
    results = []
    
    for day in positions_df['date_day'].unique():
        day_positions = positions_df[positions_df['date_day'] == day].copy()
        
        # Check if this day exists in the dataset
        try:
            day_ts = pd.Timestamp(day)
            if day_ts not in ds.time.values:
                # No data for this day - keep positions but set values to NaN
                for var in ['uo', 'vo', 'siconc', 'usi', 'vsi']:
                    day_positions[var] = np.nan
                results.append(day_positions)
                continue
            
            # Select this day's data
            ds_day = ds.sel(time=day_ts)
            
            # Extract values for each variable with bilinear interpolation
            for var in ['uo', 'vo', 'siconc', 'usi', 'vsi']:
                if var not in ds_day:
                    day_positions[var] = np.nan
                    continue
                
                var_data = ds_day[var]
                
                # Handle depth dimension: only uo/vo have depth
                if 'depth' in var_data.dims:
                    var_data = var_data.isel(depth=0)
                
                # Vectorized bilinear interpolation
                try:
                    interpolated = var_data.interp(
                        latitude=xr.DataArray(day_positions['latitude'].values, dims='points'),
                        longitude=xr.DataArray(day_positions['longitude'].values, dims='points'),
                        method='linear'
                    )
                    day_positions[var] = interpolated.values
                except Exception as e:
                    # If interpolation fails, set to NaN
                    day_positions[var] = np.nan
            
            results.append(day_positions)
            
        except Exception as e:
            # If anything fails for this day, keep positions but set values to NaN
            for var in ['uo', 'vo', 'siconc', 'usi', 'vsi']:
                day_positions[var] = np.nan
            results.append(day_positions)
    
    if results:
        combined = pd.concat(results, ignore_index=True)
        # Drop the temporary date_day column
        combined = combined.drop(columns=['date_day'])
        return combined
    else:
        return positions_df


def stream_test_data():
    """Stream a tiny test dataset to verify connection."""
    print_header("TEST MODE - Streaming 3 days, 5x5 degree box")
    
    dataset_id = "cmems_mod_glo_phy_my_0.083deg_P1D-m"
    variables = ["uo", "vo", "siconc", "usi", "vsi"]
    
    print_stat("Region", "-60° to -55° lat, 0° to 5° lon")
    print_stat("Dates", "2020-01-01 to 2020-01-03 (3 days)")
    print_stat("Variables", ", ".join(variables))
    
    try:
        # Get credentials from environment if available
        username = os.environ.get('COPERNICUSMARINE_SERVICE_USERNAME')
        password = os.environ.get('COPERNICUSMARINE_SERVICE_PASSWORD')
        
        kwargs = {
            'dataset_id': dataset_id,
            'minimum_longitude': 0,
            'maximum_longitude': 5,
            'minimum_latitude': -60,
            'maximum_latitude': -55,
            'start_datetime': '2020-01-01',
            'end_datetime': '2020-01-03',
            'variables': variables,
            'minimum_depth': 0,
            'maximum_depth': 1,
        }
        
        if username and password:
            kwargs['username'] = username
            kwargs['password'] = password
        
        print("\nConnecting to Copernicus Marine Service...")
        ds = copernicusmarine.open_dataset(**kwargs)
        
        print("Loading test data into memory...")
        ds_loaded = ds.load()
        ds.close()
        
        print_header("TEST RESULTS")
        print_success("Connection successful!")
        print_stat("Dataset shape", str(ds_loaded.dims))
        print_stat("Variables", ", ".join(list(ds_loaded.data_vars.keys())))
        print_stat("Date range", f"{ds_loaded.time.values[0]} to {ds_loaded.time.values[-1]}")
        print_stat("Size in memory", 
                  f"{sum(var.nbytes for var in ds_loaded.data_vars.values()) / 1024**2:.2f} MB")
        
        # Print sample values (handle depth dimension correctly)
        print("\n  Sample data (first time step, first lat/lon):")
        for var in variables:
            if var in ds_loaded:
                var_data = ds_loaded[var].isel(time=0, latitude=0, longitude=0)
                # Only apply depth selection if depth dimension exists
                if 'depth' in var_data.dims:
                    var_data = var_data.isel(depth=0)
                val = float(var_data.values)
                print(f"    {var:10s} = {val:.6f}")
        
        print(f"\n{GREEN}✓ Test successful! Ready to stream full dataset.{RESET}\n")
        return True
        
    except Exception as e:
        print_error(f"Test failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Check if copernicusmarine credentials are configured")
        print("  2. Set environment variables:")
        print("     COPERNICUSMARINE_SERVICE_USERNAME=your_username")
        print("     COPERNICUSMARINE_SERVICE_PASSWORD=your_password")
        print("  3. Or run copernicusmarine.open_dataset() which will prompt interactively")
        return False


def process_year(year, positions_df, config, output_dir):
    """
    Process one year: stream month-by-month, extract values at iceberg positions.
    
    Args:
        year: Year to process
        positions_df: DataFrame with all iceberg positions
        config: Configuration dict
        output_dir: Output directory
    
    Returns:
        DataFrame with interpolated values, or None if failed
    """
    # Get positions for this year only
    year_positions = positions_df[positions_df['date'].dt.year == year].copy()
    
    if len(year_positions) == 0:
        print_warning(f"No iceberg positions for year {year}, skipping")
        return None
    
    print(f"\n{CYAN}Processing year {year}...{RESET}")
    print_stat(f"  Iceberg positions", f"{len(year_positions):,}")
    
    all_results = []
    
    # Process month by month
    for month in range(1, 13):
        month_positions = year_positions[year_positions['date'].dt.month == month].copy()
        
        if len(month_positions) == 0:
            continue
        
        print(f"  Month {month:02d}: {len(month_positions):,} positions...", end='', flush=True)
        
        # Stream this month's data
        ds = stream_month(year, month, config, max_retries=3)
        
        if ds is None:
            # No data or failed - keep positions but set values to NaN
            for var in ['uo', 'vo', 'siconc', 'usi', 'vsi']:
                month_positions[var] = np.nan
            all_results.append(month_positions)
            print(" NO DATA")
            continue
        
        # Interpolate to iceberg positions
        month_with_values = interpolate_to_positions(ds, month_positions)
        all_results.append(month_with_values)
        
        # Count valid values
        valid_uo = month_with_values['uo'].notna().sum()
        valid_siconc = month_with_values['siconc'].notna().sum()
        print(f" {valid_uo}/{len(month_positions)} uo, {valid_siconc}/{len(month_positions)} siconc")
        
        # Clean up
        del ds
        gc.collect()
    
    # Combine all months
    if all_results:
        year_df = pd.concat(all_results, ignore_index=True)
        
        # Save year file
        output_file = output_dir / f"forcing_ocean_{year}.csv"
        year_df.to_csv(output_file, index=False)
        
        file_size_kb = output_file.stat().st_size / 1024
        print_success(f"Saved {output_file.name} ({file_size_kb:.1f} KB, {len(year_df):,} rows)")
        
        # Print statistics
        valid_uo = year_df['uo'].notna().sum()
        valid_vo = year_df['vo'].notna().sum()
        valid_siconc = year_df['siconc'].notna().sum()
        print(f"  Valid data: uo/vo={valid_uo}/{len(year_df)} ({100*valid_uo/len(year_df):.1f}%), "
              f"siconc={valid_siconc}/{len(year_df)} ({100*valid_siconc/len(year_df):.1f}%)")
        
        return year_df
    else:
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Stream ocean data from Copernicus Marine Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test connection (3 days, 5x5 degree box)
  python ama3_stream_ocean.py --test
  
  # Stream one specific year
  python ama3_stream_ocean.py --year 2015
  
  # Stream all years (1995-2021)
  python ama3_stream_ocean.py
        """
    )
    
    parser.add_argument('--test', action='store_true',
                       help='Test mode: stream 3 days of tiny region only')
    parser.add_argument('--year', type=int,
                       help='Stream only this specific year (e.g., 2015)')
    
    args = parser.parse_args()
    
    print(f"\n{BLUE}╔════════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BLUE}║     AMA-3: Stream Ocean Data from Copernicus Marine                       ║{RESET}")
    print(f"{BLUE}║     CryoNav AI - Iceberg Trajectory ML                                     ║{RESET}")
    print(f"{BLUE}╚════════════════════════════════════════════════════════════════════════════╝{RESET}")
    
    # Test mode
    if args.test:
        success = stream_test_data()
        sys.exit(0 if success else 1)
    
    # Load configuration
    config_path = Path("iceberg-trajectory-ml/data/validation/download_config.yaml")
    config = load_config(config_path)
    
    # Load iceberg positions
    print_header("LOADING ICEBERG POSITIONS")
    positions_file = Path("iceberg-trajectory-ml/data/validation/selected_positions.csv")
    if not positions_file.exists():
        print_error(f"Iceberg positions file not found: {positions_file}")
        print("Run ama2_select_icebergs.py first to generate this file.")
        sys.exit(1)
    
    positions_df = load_iceberg_positions(positions_file)
    
    # Determine years to process
    start_year = int(config['date_range']['start'][:4])
    end_year = int(config['date_range']['end'][:4])
    
    if args.year:
        if args.year < start_year or args.year > end_year:
            print_error(f"Year {args.year} is outside config range ({start_year}-{end_year})")
            sys.exit(1)
        years = [args.year]
        print_stat("Processing", f"Single year: {args.year}")
    else:
        years = list(range(start_year, end_year + 1))
        print_stat("Processing", f"{len(years)} years ({start_year}-{end_year})")
    
    # Output directory
    output_dir = Path("iceberg-trajectory-ml/data/validation")
    
    print_header("PROCESSING YEARS (MONTH-BY-MONTH)")
    print(f"{YELLOW}Note:{RESET} Extracting values at iceberg positions only (not full grid)")
    print(f"{YELLOW}→{RESET} Processing month-by-month to keep RAM usage low\n")
    
    # Track statistics
    all_year_results = []
    successful_years = []
    failed_years = []
    total_positions = 0
    total_valid_uo = 0
    total_valid_siconc = 0
    
    # Process each year
    for idx, year in enumerate(years, 1):
        print(f"\n{CYAN}{'─' * 80}{RESET}")
        print(f"{CYAN}Year {year} ({idx}/{len(years)}){RESET}")
        print(f"{CYAN}{'─' * 80}{RESET}")
        
        # Process the year
        year_df = process_year(year, positions_df, config, output_dir)
        
        if year_df is not None:
            successful_years.append(year)
            all_year_results.append(year_df)
            
            # Update totals
            total_positions += len(year_df)
            total_valid_uo += year_df['uo'].notna().sum()
            total_valid_siconc += year_df['siconc'].notna().sum()
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
        combined_file = output_dir / "forcing_ocean_all.csv"
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
        print_stat("Valid uo/vo", f"{total_valid_uo:,} ({100*total_valid_uo/total_positions:.1f}%)")
        print_stat("Valid siconc", f"{total_valid_siconc:,} ({100*total_valid_siconc/total_positions:.1f}%)")
    
    print_stat("Saved to", output_dir)
    
    print(f"\n{GREEN}{'=' * 80}{RESET}")
    if len(successful_years) > 0:
        print(f"{GREEN}✓ Processing complete!{RESET}")
        print(f"{GREEN}{'=' * 80}{RESET}\n")
        print("Next step: Run ama3_verify_chunks.py to verify the data\n")
    else:
        print(f"{RED}✗ All years failed!{RESET}")
        print(f"{RED}{'=' * 80}{RESET}\n")
        print("Check your network connection and Copernicus Marine credentials.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
