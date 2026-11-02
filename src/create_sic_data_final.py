"""Create final SIC dataset efficiently."""
import numpy as np
import netCDF4 as nc
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path("data/sic")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Smaller subset: 2018-2023 only (6 years)
lat = np.arange(-72, -50, 2.0)  # 11 points
lon = np.arange(-15, 40, 2.0)   # 28 points

start = datetime(2018, 1, 1)
end = datetime(2023, 12, 31)
dates = []
d = start
while d <= end:
    dates.append(d)
    d += timedelta(days=1)

print(f"Grid: {len(lat)}×{len(lon)}={len(lat)*len(lon)}")
print(f"Days: {len(dates)} ({start.date()} to {end.date()})")

# Create patterns
lg, lng = np.meshgrid(lat, lon, indexing='ij')
monthly_patterns = {}

for m in range(1, 13):
    base = np.clip(((-50-lg)/22*100), 0, 100)
    if m in [12,1,2]:  # Summer
        base *= 0.15
    elif m in [6,7,8]:  # Winter  
        base *= 0.95
    else:
        base *= 0.55
    monthly_patterns[m] = base.astype(np.float32)

# Write
output = DATA_DIR / "sic_synthetic_2018_2023.nc"
with nc.Dataset(output, 'w') as ds:
    ds.createDimension('lat', len(lat))
    ds.createDimension('lon', len(lon))
    ds.createDimension('time', len(dates))
    
    lv = ds.createVariable('lat', 'f4', ('lat',))
    lv[:] = lat
    lv.units = 'degrees_north'
    
    lnv = ds.createVariable('lon', 'f4', ('lon',))
    lnv[:] = lon
    lnv.units = 'degrees_east'
    
    tv = ds.createVariable('time', 'i4', ('time',))
    tv[:] = list(range(len(dates)))
    tv.units = f'days since {start.isoformat()}'
    
    sv = ds.createVariable('sic', 'f4', ('time', 'lat', 'lon'), zlib=True, complevel=5)
    sv.units = 'percent'
    
    print("Writing...")
    for i, date in enumerate(dates):
        if i % 365 == 0:
            print(f"  {date.year}...")
        pattern = monthly_patterns[date.month]
        noise = np.random.normal(0, 2.5, pattern.shape).astype(np.float32)
        sv[i,:,:] = np.clip(pattern + noise, 0, 100)
    
    ds.title = "Synthetic SIC 2018-2023"

print(f"✓ {output} ({output.stat().st_size/1024**2:.1f} MB)")

# Update report
report = f"""# Sea Ice Concentration Data Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Data Source

**Synthetic Testing Data**

⚠ **WARNING**: SYNTHETIC data - not satellite observations

## Coverage

- **Latitude**: {lat.min()}° to {lat.max()}° ({len(lat)} points)
- **Longitude**: {lon.min()}° to {lon.max()}° ({len(lon)} points)
- **Resolution**: 2.0° × 2.0°
- **Grid cells**: {len(lat)*len(lon):,}
- **Period**: {start.date()} to {end.date()}
- **Days**: {len(dates):,}
- **Completeness**: 100%

## File

- **Name**: {output.name}
- **Size**: {output.stat().st_size/1024**2:.1f} MB
- **Format**: NetCDF4 compressed

## Notes

Synthetic data with realistic patterns:
- Seasonal cycle (summer low, winter high)
- Latitude gradient (higher toward south)
- Random variability (~2.5% std)
"""

(DATA_DIR / "data_report.md").write_text(report)
print(f"✓ {DATA_DIR}/data_report.md")
