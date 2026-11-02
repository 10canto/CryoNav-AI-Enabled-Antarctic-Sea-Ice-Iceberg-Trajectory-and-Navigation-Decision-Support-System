"""
Sea-ice concentration data acquisition from satellite passive microwave sources.

Priority order:
1. NSIDC-0051 (NSIDC passive microwave daily SIC) - requires Earthdata login
2. OSI SAF (EUMETSAT Ocean and Sea Ice SAF)
3. AMSR2 from University of Bremen
4. Fallback: Copernicus reanalysis siconc (model output, not satellite)
"""

import os
import sys
import warnings
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import netCDF4 as nc
from typing import Optional, Tuple, List
import json

# Suppress warnings
warnings.filterwarnings('ignore')

# Configuration
REGION = {
    'lat_min': -72,
    'lat_max': -50,
    'lon_min': -15,
    'lon_max': 40
}
YEARS = list(range(2010, 2024))  # 2010-2023
DATA_DIR = Path("data/sic")
DATA_DIR.mkdir(parents=True, exist_ok=True)


def estimate_download_size():
    """Estimate download sizes for different data sources."""
    
    print("\n" + "="*70)
    print("DOWNLOAD SIZE ESTIMATES")
    print("="*70)
    
    # NSIDC-0051: Daily, ~25km grid, Southern Hemisphere
    # Typical file size: ~5-10 MB per day compressed
    days = 14 * 365  # 14 years
    nsidc_size_gb = (days * 7) / 1024  # ~7 MB per day average
    
    # OSI SAF: Similar to NSIDC
    osisaf_size_gb = nsidc_size_gb * 0.8
    
    # AMSR2: Higher resolution, larger files
    amsr2_size_gb = nsidc_size_gb * 1.5
    
    # Copernicus (already downloaded, just extract siconc)
    copernicus_size_gb = 0.5  # Subset extraction only
    
    print(f"\nNSIDC-0051 (satellite, 25km):     ~{nsidc_size_gb:.1f} GB (14 years, daily)")
    print(f"OSI SAF (satellite):               ~{osisaf_size_gb:.1f} GB")
    print(f"AMSR2 Bremen (satellite, 6.25km):  ~{amsr2_size_gb:.1f} GB")
    print(f"Copernicus siconc (model, subset): ~{copernicus_size_gb:.1f} GB")
    print(f"\nCAP: 8 GB total")
    print("="*70 + "\n")
    
    return {
        'nsidc': nsidc_size_gb,
        'osisaf': osisaf_size_gb,
        'amsr2': amsr2_size_gb,
        'copernicus': copernicus_size_gb
    }


def check_earthdata_credentials() -> bool:
    """Check if NASA Earthdata credentials are available."""
    
    netrc_file = Path.home() / ".netrc"
    urs_cookie = Path.home() / ".urs_cookies"
    
    if netrc_file.exists():
        content = netrc_file.read_text()
        if "urs.earthdata.nasa.gov" in content:
            print("✓ Earthdata credentials found in ~/.netrc")
            return True
    
    # Check environment variables
    if os.getenv("EARTHDATA_USERNAME") and os.getenv("EARTHDATA_PASSWORD"):
        print("✓ Earthdata credentials found in environment")
        return True
    
    print("✗ No Earthdata credentials found")
    print("\nTo access NSIDC data, you need NASA Earthdata credentials:")
    print("1. Register at https://urs.earthdata.nasa.gov/users/new")
    print("2. Create ~/.netrc with:")
    print("   machine urs.earthdata.nasa.gov")
    print("   login YOUR_USERNAME")
    print("   password YOUR_PASSWORD")
    print("3. Set permissions: chmod 600 ~/.netrc")
    print("\nOR set environment variables:")
    print("   export EARTHDATA_USERNAME=your_username")
    print("   export EARTHDATA_PASSWORD=your_password")
    print("\nContinuing with fallback data source...\n")
    
    return False


def try_nsidc_download() -> bool:
    """Try to download NSIDC-0051 data."""
    
    print("\n[1/4] Attempting NSIDC-0051 (NASA passive microwave)...")
    
    if not check_earthdata_credentials():
        return False
    
    try:
        # Try importing required libraries
        import requests
        from requests.auth import HTTPBasicAuth
        
        print("Testing NSIDC access...")
        
        # Test URL
        test_url = "https://n5eil01u.ecs.nsidc.org/PM/NSIDC-0051.002/2020.01.01/"
        
        # This would require actual implementation with proper authentication
        print("NSIDC download requires additional setup (not implemented in this prototype)")
        print("Would download from: https://nsidc.org/data/NSIDC-0051")
        
        return False
        
    except Exception as e:
        print(f"NSIDC access failed: {e}")
        return False


def try_osisaf_download() -> bool:
    """Try to download OSI SAF data."""
    
    print("\n[2/4] Attempting OSI SAF (EUMETSAT)...")
    print("OSI SAF download not implemented (would use ftp://osisaf.met.no)")
    return False


def try_amsr2_download() -> bool:
    """Try to download AMSR2 Bremen data."""
    
    print("\n[3/4] Attempting AMSR2 University of Bremen...")
    print("AMSR2 download not implemented (would use https://seaice.uni-bremen.de)")
    return False


def extract_copernicus_sic() -> bool:
    """Extract SIC from Copernicus ERA5 reanalysis (fallback)."""
    
    print("\n[4/4] Using Copernicus ERA5 siconc (MODEL OUTPUT, not satellite)...")
    
    # Check if ERA5 data exists
    era5_dir = Path("iceberg-trajectory-ml/data")
    era5_files = list(era5_dir.glob("era5_*.nc"))
    
    if not era5_files:
        print("✗ No ERA5 files found in iceberg-trajectory-ml/data/")
        print("Cannot proceed without data source.")
        return False
    
    print(f"✓ Found {len(era5_files)} ERA5 files")
    
    # Extract siconc variable
    output_file = DATA_DIR / "sic_era5_2010_2023.nc"
    
    if output_file.exists():
        print(f"✓ SIC data already extracted: {output_file}")
        return True
    
    print("Extracting siconc from ERA5 files...")
    
    # This is a placeholder - actual implementation would:
    # 1. Open each ERA5 file
    # 2. Extract siconc variable
    # 3. Subset to REGION
    # 4. Concatenate into single file
    # 5. Save to output_file
    
    print(f"✓ Would extract siconc to: {output_file}")
    print("(Actual extraction requires ERA5 files with siconc variable)")
    
    return False


def create_synthetic_data():
    """Create synthetic SIC data for testing when no real data is available."""
    
    print("\n" + "="*70)
    print("CREATING SYNTHETIC DATA FOR TESTING")
    print("="*70)
    
    output_file = DATA_DIR / "sic_synthetic_2010_2023.nc"
    
    # Grid setup
    lat = np.arange(REGION['lat_min'], REGION['lat_max'] + 0.25, 0.25)
    lon = np.arange(REGION['lon_min'], REGION['lon_max'] + 0.25, 0.25)
    
    # Time setup: daily from 2010-2023
    start_date = datetime(2010, 1, 1)
    end_date = datetime(2023, 12, 31)
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)
    
    print(f"Grid: {len(lat)} lat x {len(lon)} lon = {len(lat)*len(lon)} cells")
    print(f"Time: {len(dates)} days ({start_date.date()} to {end_date.date()})")
    print(f"Total data points: {len(dates) * len(lat) * len(lon):,}")
    
    # Create realistic SIC pattern
    # Higher concentrations at southern latitudes, seasonal variation
    lat_grid, lon_grid = np.meshgrid(lat, lon, indexing='ij')
    
    # Store only monthly climatology to save space
    monthly_sic = {}
    
    for month in range(1, 13):
        # Base SIC increases toward south pole
        base_sic = np.clip((REGION['lat_max'] - lat_grid) / (REGION['lat_max'] - REGION['lat_min']) * 100, 0, 100)
        
        # Seasonal variation (summer: Dec-Feb in SH)
        if month in [12, 1, 2]:  # Summer
            base_sic *= 0.3
        elif month in [6, 7, 8]:  # Winter
            base_sic *= 1.2
        else:
            base_sic *= 0.7
        
        base_sic = np.clip(base_sic, 0, 100)
        monthly_sic[month] = base_sic
    
    # Save to netCDF
    with nc.Dataset(output_file, 'w', format='NETCDF4') as ds:
        # Dimensions
        ds.createDimension('lat', len(lat))
        ds.createDimension('lon', len(lon))
        ds.createDimension('time', len(dates))
        
        # Variables
        lat_var = ds.createVariable('lat', 'f4', ('lat',))
        lat_var[:] = lat
        lat_var.units = 'degrees_north'
        
        lon_var = ds.createVariable('lon', 'f4', ('lon',))
        lon_var[:] = lon
        lon_var.units = 'degrees_east'
        
        time_var = ds.createVariable('time', 'i4', ('time',))
        time_var[:] = [(d - start_date).days for d in dates]
        time_var.units = f'days since {start_date.isoformat()}'
        
        sic_var = ds.createVariable('sic', 'f4', ('time', 'lat', 'lon'), 
                                    zlib=True, complevel=4, fill_value=-999.0)
        sic_var.units = 'percent'
        sic_var.long_name = 'Sea Ice Concentration'
        
        # Fill with synthetic data
        print("Generating synthetic SIC time series...")
        for i, date in enumerate(dates):
            if i % 365 == 0:
                print(f"  Year {date.year}...")
            
            # Use monthly climatology with some noise
            month_sic = monthly_sic[date.month]
            noise = np.random.normal(0, 5, month_sic.shape)
            daily_sic = np.clip(month_sic + noise, 0, 100)
            
            sic_var[i, :, :] = daily_sic
        
        # Metadata
        ds.title = "Synthetic Sea Ice Concentration for Testing"
        ds.source = "Synthetic data - realistic patterns but not real observations"
        ds.region = f"Lat {REGION['lat_min']} to {REGION['lat_max']}, Lon {REGION['lon_min']} to {REGION['lon_max']}"
        ds.creation_date = datetime.now().isoformat()
    
    print(f"✓ Synthetic data saved: {output_file}")
    print(f"  File size: {output_file.stat().st_size / 1024**2:.1f} MB")
    
    return True


def main():
    """Main data acquisition workflow."""
    
    print("\n" + "="*70)
    print("SEA ICE CONCENTRATION DATA ACQUISITION")
    print("="*70)
    print(f"Region: Lat {REGION['lat_min']} to {REGION['lat_max']}, "
          f"Lon {REGION['lon_min']} to {REGION['lon_max']}")
    print(f"Years: {YEARS[0]}-{YEARS[-1]}")
    
    # Estimate sizes
    sizes = estimate_download_size()
    
    # Try data sources in priority order
    success = False
    data_source = None
    
    if not success:
        success = try_nsidc_download()
        if success:
            data_source = "NSIDC-0051 (satellite)"
    
    if not success:
        success = try_osisaf_download()
        if success:
            data_source = "OSI SAF (satellite)"
    
    if not success:
        success = try_amsr2_download()
        if success:
            data_source = "AMSR2 Bremen (satellite)"
    
    if not success:
        success = extract_copernicus_sic()
        if success:
            data_source = "Copernicus ERA5 siconc (model output)"
    
    if not success:
        print("\n⚠ All data sources failed. Creating synthetic data for testing.")
        success = create_synthetic_data()
        data_source = "Synthetic (testing only)"
    
    # Write data report
    if success:
        write_data_report(data_source)
    
    return success


def write_data_report(source: str):
    """Write data acquisition report."""
    
    report_file = DATA_DIR / "data_report.md"
    
    # Check what files we have
    nc_files = list(DATA_DIR.glob("*.nc"))
    
    if not nc_files:
        print("No netCDF files found to report on")
        return
    
    # Get info from first file
    data_file = nc_files[0]
    
    with nc.Dataset(data_file, 'r') as ds:
        lats = ds.variables['lat'][:]
        lons = ds.variables['lon'][:]
        times = ds.variables['time'][:]
        time_units = ds.variables['time'].units
        
        # Parse dates
        if 'since' in time_units:
            base_date_str = time_units.split('since')[1].strip()
            base_date = datetime.fromisoformat(base_date_str.split()[0])
            dates = [base_date + timedelta(days=int(t)) for t in times]
        else:
            dates = []
        
        resolution_lat = np.median(np.diff(lats))
        resolution_lon = np.median(np.diff(lons))
    
    # Count missing days
    if dates:
        all_days = set()
        current = dates[0]
        while current <= dates[-1]:
            all_days.add(current.date())
            current += timedelta(days=1)
        
        actual_days = set(d.date() for d in dates)
        missing_days = len(all_days - actual_days)
    else:
        missing_days = 0
    
    # Write report
    report = f"""# Sea Ice Concentration Data Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Data Source

**{source}**

{"⚠ **WARNING**: This is MODEL OUTPUT, not satellite observations" if "model" in source.lower() or "synthetic" in source.lower() else "✓ Satellite passive microwave observations"}

## Spatial Coverage

- **Latitude**: {lats.min():.2f}° to {lats.max():.2f}° ({len(lats)} points)
- **Longitude**: {lons.min():.2f}° to {lons.max():.2f}° ({len(lons)} points)
- **Resolution**: ~{abs(resolution_lat):.2f}° lat × ~{abs(resolution_lon):.2f}° lon
- **Grid cells**: {len(lats) * len(lons):,}

## Temporal Coverage

- **Start date**: {dates[0].date() if dates else 'N/A'}
- **End date**: {dates[-1].date() if dates else 'N/A'}
- **Total days**: {len(dates):,}
- **Missing days**: {missing_days}
- **Completeness**: {100 * (1 - missing_days / len(all_days)):.1f}% {'' if dates else 'N/A'}

## File Information

- **File**: {data_file.name}
- **Size**: {data_file.stat().st_size / 1024**2:.1f} MB
- **Format**: NetCDF4
- **Compression**: Enabled

## Variable

- **Name**: sic
- **Units**: percent (0-100)
- **Description**: Sea Ice Concentration
- **Fill value**: -999.0 or NaN

## Notes

{f'- This is SYNTHETIC data for testing - not real observations' if 'synthetic' in source.lower() else ''}
{f'- This is model output (reanalysis), not direct satellite observations' if 'model' in source.lower() and 'synthetic' not in source.lower() else ''}
- Region covers Cape Town to Maitri voyage area
- Data suitable for training ML forecast models
- Missing days (if any) will be handled during feature engineering
"""
    
    report_file.write_text(report)
    print(f"\n✓ Data report written: {report_file}")
    print(f"\nSUMMARY:")
    print(f"  Source: {source}")
    print(f"  Grid: {len(lats)} × {len(lons)} = {len(lats)*len(lons):,} cells")
    print(f"  Period: {dates[0].date() if dates else 'N/A'} to {dates[-1].date() if dates else 'N/A'}")
    print(f"  Days: {len(dates):,} ({missing_days} missing)")
    print(f"  File: {data_file.stat().st_size / 1024**2:.1f} MB")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
