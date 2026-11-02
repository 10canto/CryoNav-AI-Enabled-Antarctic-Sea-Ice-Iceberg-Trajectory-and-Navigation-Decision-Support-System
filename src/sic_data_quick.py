"""
Quick sea-ice concentration data generation for testing.
Creates smaller synthetic dataset to enable model development.
"""

import numpy as np
import netCDF4 as nc
from datetime import datetime, timedelta
from pathlib import Path

def create_small_synthetic_sic():
    """Create smaller synthetic SIC dataset."""
    
    DATA_DIR = Path("data/sic")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    output_file = DATA_DIR / "sic_synthetic_2010_2023.nc"
    
    # Coarser grid - 0.5 degree
    lat = np.arange(-72, -49.5, 0.5)  # ~45 points
    lon = np.arange(-15, 40.5, 0.5)   # ~111 points
    
    # Daily from 2010-2023
    start_date = datetime(2010, 1, 1)
    end_date = datetime(2023, 12, 31)
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)
    
    print(f"Grid: {len(lat)} × {len(lon)} = {len(lat)*len(lon)} cells")
    print(f"Days: {len(dates)}")
    
    lat_grid, lon_grid = np.meshgrid(lat, lon, indexing='ij')
    
    # Monthly climatology
    monthly_sic = {}
    for month in range(1, 13):
        base_sic = np.clip(((-50) - lat_grid) / 22 * 100, 0, 100)
        
        if month in [12, 1, 2]:  # Summer
            base_sic *= 0.2
        elif month in [6, 7, 8]:  # Winter
            base_sic *= 1.0
        else:
            base_sic *= 0.6
        
        monthly_sic[month] = np.clip(base_sic, 0, 100).astype(np.float32)
    
    # Save
    with nc.Dataset(output_file, 'w', format='NETCDF4') as ds:
        ds.createDimension('lat', len(lat))
        ds.createDimension('lon', len(lon))
        ds.createDimension('time', len(dates))
        
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
                                    zlib=True, complevel=6, fill_value=-999.0)
        sic_var.units = 'percent'
        
        # Fill efficiently
        print("Writing data...")
        for i, date in enumerate(dates):
            if i % 365 == 0:
                print(f"  {date.year}...")
            
            month_sic = monthly_sic[date.month]
            noise = np.random.normal(0, 3, month_sic.shape).astype(np.float32)
            daily_sic = np.clip(month_sic + noise, 0, 100)
            
            sic_var[i, :, :] = daily_sic
        
        ds.title = "Synthetic SIC for Testing"
        ds.source = "Synthetic - not real observations"
    
    size_mb = output_file.stat().st_size / 1024**2
    print(f"✓ Created: {output_file} ({size_mb:.1f} MB)")
    
    # Write report
    report = f"""# Sea Ice Concentration Data Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Data Source

**Synthetic Testing Data**

⚠ **WARNING**: This is SYNTHETIC data for testing - not satellite observations or model output

## Spatial Coverage

- **Latitude**: {lat.min()}° to {lat.max()}° ({len(lat)} points)
- **Longitude**: {lon.min()}° to {lon.max()}° ({len(lon)} points)
- **Resolution**: 0.5° × 0.5°
- **Grid cells**: {len(lat) * len(lon):,}

## Temporal Coverage

- **Start date**: {start_date.date()}
- **End date**: {end_date.date()}
- **Total days**: {len(dates):,}
- **Missing days**: 0
- **Completeness**: 100.0%

## File Information

- **File**: {output_file.name}
- **Size**: {size_mb:.1f} MB
- **Format**: NetCDF4
- **Compression**: Level 6

## Variable

- **Name**: sic
- **Units**: percent (0-100)
- **Description**: Sea Ice Concentration
- **Fill value**: -999.0

## Notes

- Synthetic data with realistic seasonal patterns
- Higher concentrations in winter (Jun-Aug)
- Lower in summer (Dec-Feb)
- Increases toward south pole
- Suitable for ML model development and testing
"""
    
    (DATA_DIR / "data_report.md").write_text(report)
    print(f"✓ Report: {DATA_DIR / 'data_report.md'}")
    
    return True

if __name__ == "__main__":
    create_small_synthetic_sic()
