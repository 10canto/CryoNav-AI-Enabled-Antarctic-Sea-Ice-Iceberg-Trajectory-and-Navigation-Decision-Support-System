#!/usr/bin/env python3
"""
Export Demo Sea Ice Grid
CryoNav AI - Iceberg Trajectory ML

PURPOSE:
    Export a gridded sea-ice concentration CSV for the CryoNav frontend demo.
    Real data from Copernicus Marine GLORYS12, regridded to 2° × 2°.

DEMO AREA:
    Cape Town to Maitri station route
    Latitude: -34 to -70
    Longitude: 11 to 18

DEMO DATES:
    - 2020-01-15 (austral summer — minimal ice)
    - 2020-05-15 (austral autumn — ice advancing)
    - 2020-08-15 (austral winter — maximum ice extent)

DATA SOURCE:
    - Dataset: cmems_mod_glo_phy_my_0.083deg_P1D-m (GLORYS12 reanalysis)
    - Variable: siconc (sea ice concentration, fraction 0-1)
    - Credentials: COPERNICUSMARINE_SERVICE_USERNAME / COPERNICUSMARINE_SERVICE_PASSWORD

OUTPUT:
    - CSV: iceberg-trajectory-ml/data/validation/demo_seaice_grid.csv
    - JSON: iceberg-trajectory-ml/data/validation/demo_seaice_grid.json

DATA INTEGRITY:
    - NO synthetic data (REAL Copernicus data only)
    - NO filling of NaN values (land/no-data preserved)
    - NO .nc files saved to disk (streaming only)
"""

import sys
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import copernicusmarine


def print_header(title):
    """Print section header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def fetch_seaice_for_date(date_str, lat_min=-70, lat_max=-34, lon_min=11, lon_max=18):
    """
    Fetch sea ice concentration for a single date from Copernicus Marine.
    
    Args:
        date_str: Date string "YYYY-MM-DD"
        lat_min, lat_max, lon_min, lon_max: Bounding box
    
    Returns:
        xarray.Dataset with siconc variable
    """
    print(f"\nFetching sea ice data for {date_str}...")
    
    try:
        ds = copernicusmarine.open_dataset(
            dataset_id="cmems_mod_glo_phy_my_0.083deg_P1D-m",
            variables=["siconc"],
            minimum_longitude=lon_min,
            maximum_longitude=lon_max,
            minimum_latitude=lat_min,
            maximum_latitude=lat_max,
            start_datetime=date_str,
            end_datetime=date_str
        )
        
        print(f"  Data shape: {ds.siconc.shape}")
        print(f"  Lat range: {float(ds.latitude.min()):.2f} to {float(ds.latitude.max()):.2f}")
        print(f"  Lon range: {float(ds.longitude.min()):.2f} to {float(ds.longitude.max()):.2f}")
        
        return ds
        
    except Exception as e:
        print(f"\nERROR fetching data from Copernicus Marine: {e}")
        print("\nPossible causes:")
        print("  1. Invalid credentials (check COPERNICUSMARINE_SERVICE_USERNAME/PASSWORD)")
        print("  2. Network connection issue")
        print("  3. Dataset temporarily unavailable")
        print("\nABORTING: Cannot proceed without real data")
        sys.exit(1)


def regrid_to_coarse(ds, date_str, lat_bin=2.0, lon_bin=2.0):
    """
    Regrid from 1/12° to coarser resolution (default 2° × 2°).
    
    Args:
        ds: xarray.Dataset with siconc
        date_str: Date string for labeling
        lat_bin: Latitude bin size (degrees)
        lon_bin: Longitude bin size (degrees)
    
    Returns:
        pandas.DataFrame with columns: lat, lon, date, concentration
    """
    print(f"\nRegridding to {lat_bin}° × {lon_bin}° grid...")
    
    # Extract siconc (no depth dimension for sea ice)
    siconc = ds.siconc.squeeze()  # Remove time dimension if present
    
    # Get coordinates
    lats = siconc.latitude.values
    lons = siconc.longitude.values
    
    # Create bins
    lat_bins = np.arange(-70, -34 + lat_bin, lat_bin)
    lon_bins = np.arange(10, 18 + lon_bin, lon_bin)
    
    print(f"  Lat bins: {len(lat_bins) - 1} cells")
    print(f"  Lon bins: {len(lon_bins) - 1} cells")
    
    # Build regridded data
    rows = []
    
    for i in range(len(lat_bins) - 1):
        lat_center = (lat_bins[i] + lat_bins[i+1]) / 2
        
        for j in range(len(lon_bins) - 1):
            lon_center = (lon_bins[j] + lon_bins[j+1]) / 2
            
            # Select data in this bin using xarray's selection
            bin_data = siconc.where(
                (siconc.latitude >= lat_bins[i]) & (siconc.latitude < lat_bins[i+1]) &
                (siconc.longitude >= lon_bins[j]) & (siconc.longitude < lon_bins[j+1]),
                drop=False
            )
            
            # Compute mean (preserving NaN)
            mean_conc = float(bin_data.mean().values)
            
            # Convert to percentage (0-100)
            if not np.isnan(mean_conc):
                conc_pct = np.clip(mean_conc * 100, 0, 100)
                conc_pct = round(conc_pct, 1)
            else:
                conc_pct = np.nan
            
            rows.append({
                'lat': round(lat_center, 2),
                'lon': round(lon_center, 2),
                'date': date_str,
                'concentration': conc_pct
            })
    
    df = pd.DataFrame(rows)
    
    # Statistics (excluding NaN)
    valid_conc = df['concentration'].dropna()
    if len(valid_conc) > 0:
        print(f"  Valid cells: {len(valid_conc)} / {len(df)}")
        print(f"  Concentration range: {valid_conc.min():.1f}% to {valid_conc.max():.1f}%")
        print(f"  Mean concentration: {valid_conc.mean():.1f}%")
    else:
        print(f"  All cells are NaN (no valid data)")
    
    return df


def export_demo_seaice():
    """Main execution: fetch and regrid sea ice data for demo dates."""
    print_header("EXPORT DEMO SEA ICE GRID")
    print("CryoNav AI - Iceberg Trajectory ML")
    print("\nDemo area: Cape Town to Maitri station")
    print("Latitude: -34 to -70, Longitude: 11 to 18")
    print("Resolution: 2° × 2° grid")
    
    # Demo dates
    demo_dates = [
        "2020-01-15",  # Austral summer — minimal ice
        "2020-05-15",  # Austral autumn — ice advancing
        "2020-08-15"   # Austral winter — maximum ice extent
    ]
    
    print(f"\nDemo dates: {', '.join(demo_dates)}")
    
    # Fetch and regrid for each date
    all_data = []
    
    for date_str in demo_dates:
        print_header(f"PROCESSING {date_str}")
        
        # Fetch data
        ds = fetch_seaice_for_date(date_str)
        
        # Regrid
        df = regrid_to_coarse(ds, date_str)
        
        all_data.append(df)
        
        # Close dataset
        ds.close()
    
    # Combine all dates
    print_header("COMBINING DATA")
    combined_df = pd.concat(all_data, ignore_index=True)
    
    print(f"  Total rows: {len(combined_df):,}")
    print(f"  Dates: {combined_df['date'].nunique()}")
    print(f"  Unique grid cells: {combined_df.groupby(['lat', 'lon']).size().shape[0]}")
    
    # Summary statistics per date
    print("\nPer-date statistics (excluding NaN):")
    for date_str in demo_dates:
        date_df = combined_df[combined_df['date'] == date_str]
        valid_conc = date_df['concentration'].dropna()
        if len(valid_conc) > 0:
            print(f"  {date_str}: min={valid_conc.min():.1f}%, "
                  f"max={valid_conc.max():.1f}%, mean={valid_conc.mean():.1f}%")
        else:
            print(f"  {date_str}: No valid data (all NaN)")
    
    # Save CSV
    print_header("SAVING OUTPUT")
    
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "data" / "validation"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = output_dir / "demo_seaice_grid.csv"
    json_path = output_dir / "demo_seaice_grid.json"
    
    # Write CSV with header comment
    with open(csv_path, 'w') as f:
        f.write("# Source: Copernicus Marine GLORYS12 reanalysis, regridded to 2x2 degrees\n")
        f.write("# Variable: siconc (sea ice concentration), converted to 0-100%\n")
        f.write("# NaN = no data (land or ice shelf)\n")
        combined_df.to_csv(f, index=False, na_rep='NaN')
    
    csv_size_kb = csv_path.stat().st_size / 1024
    print(f"  CSV saved: {csv_path}")
    print(f"  CSV size: {csv_size_kb:.1f} KB")
    
    # Write JSON
    # Convert NaN to None for JSON
    json_data = combined_df.where(pd.notna(combined_df), None).to_dict(orient='records')
    with open(json_path, 'w') as f:
        json.dump(json_data, f, indent=2)
    
    json_size_kb = json_path.stat().st_size / 1024
    print(f"  JSON saved: {json_path}")
    print(f"  JSON size: {json_size_kb:.1f} KB")
    
    total_size_kb = csv_size_kb + json_size_kb
    print(f"  Total size: {total_size_kb:.1f} KB")
    
    if total_size_kb > 10240:  # 10 MB in KB
        print("\n  WARNING: Output exceeds 10 MB limit!")
    else:
        print(f"  ✓ Output size OK (< 10 MB)")
    
    # Grid dimensions
    n_lat = combined_df['lat'].nunique()
    n_lon = combined_df['lon'].nunique()
    print(f"\n  Grid dimensions: {n_lat} lat × {n_lon} lon = {n_lat * n_lon} cells")
    print(f"  Dates: {combined_df['date'].nunique()}")
    print(f"  Total rows: {len(combined_df):,}")
    
    print_header("COMPLETE")
    print("  Data exported successfully")
    print(f"  CSV: {csv_path.name}")
    print(f"  JSON: {json_path.name}")
    print("\nNext steps:")
    print("  1. Review the exported files")
    print("  2. Use JSON for frontend demo (easier to consume)")
    print("  3. Display as heatmap overlay on map")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    export_demo_seaice()
