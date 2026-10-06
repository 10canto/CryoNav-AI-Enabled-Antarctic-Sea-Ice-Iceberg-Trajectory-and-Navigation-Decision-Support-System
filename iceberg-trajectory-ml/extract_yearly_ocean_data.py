"""
Extract 1 Year of Ocean Current Data (2025) with Daily Time Steps
Creates time-series ocean data that UI can use based on current date
"""
import netCDF4 as nc
import numpy as np
import json
from pathlib import Path
from datetime import datetime, timedelta
from tqdm import tqdm

def extract_yearly_ocean_currents(netcdf_path, output_dir, year=2025, resolution=1.0):
    """
    Extract full year of ocean current data with daily time steps
    
    Args:
        netcdf_path: Path to NetCDF file
        output_dir: Directory to save JSON files
        year: Year to extract (default 2025)
        resolution: Grid resolution in degrees
    """
    
    print("\n" + "=" * 70)
    print(f"🌊 EXTRACTING OCEAN CURRENT DATA FOR YEAR {year}")
    print("=" * 70)
    
    print(f"\n📂 Loading ocean data: {Path(netcdf_path).name}")
    
    # Open NetCDF file
    ds = nc.Dataset(netcdf_path, 'r')
    
    # Get dimensions
    lats = ds.variables['latitude'][:]
    lons = ds.variables['longitude'][:]
    times = ds.variables['time']
    
    print(f"   Grid: {len(lats)} × {len(lons)} points")
    print(f"   Time steps available: {len(times)}")
    
    # Get time units and parse
    time_units = times.units
    time_calendar = getattr(times, 'calendar', 'standard')
    
    print(f"   Time units: {time_units}")
    
    # Convert time to datetime
    try:
        from netCDF4 import num2date
        dates = num2date(times[:], units=time_units, calendar=time_calendar)
        print(f"   Date range: {dates[0]} to {dates[-1]}")
    except Exception as e:
        print(f"   Could not parse dates: {e}")
        dates = None
    
    # Get current data
    uo = ds.variables['uo']
    vo = ds.variables['vo']
    
    print(f"   Current data shape: {uo.shape}")
    
    # Define Antarctic regions
    antarctic_regions = {
        'weddell_sea': {
            'lat_min': -80, 'lat_max': -60,
            'lon_min': -60, 'lon_max': -20
        },
        'east_antarctic': {
            'lat_min': -70, 'lat_max': -60,
            'lon_min': 30, 'lon_max': 150
        },
        'ross_sea': {
            'lat_min': -80, 'lat_max': -65,
            'lon_min': 160, 'lon_max': -160
        },
        'southern_ocean': {
            'lat_min': -65, 'lat_max': -50,
            'lon_min': -180, 'lon_max': 180
        }
    }
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    # Create date range for 2025
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)
    
    # Find matching time indices in NetCDF
    time_indices = []
    date_strings = []
    
    if dates is not None:
        for i, date in enumerate(dates):
            # Convert to datetime if needed
            if hasattr(date, 'year'):
                date_dt = datetime(date.year, date.month, date.day)
            else:
                date_dt = date
            
            if start_date <= date_dt <= end_date:
                time_indices.append(i)
                date_strings.append(date_dt.strftime('%Y-%m-%d'))
    else:
        # Fallback: use first 365 time steps
        print("   Using first 365 time steps as fallback")
        time_indices = list(range(min(365, len(times))))
        current_date = start_date
        for i in range(len(time_indices)):
            date_strings.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
    
    print(f"\n📅 Found {len(time_indices)} time steps for year {year}")
    print(f"   Date range: {date_strings[0]} to {date_strings[-1]}")
    
    print(f"\n🔧 Processing {len(antarctic_regions)} regions...")
    
    for region_name, bounds in antarctic_regions.items():
        print(f"\n   📍 Region: {region_name}")
        
        # Create downsampled grid
        lat_grid = np.arange(bounds['lat_min'], bounds['lat_max'], resolution)
        lon_grid = np.arange(bounds['lon_min'], bounds['lon_max'], resolution)
        
        # Handle wraparound for Ross Sea
        if bounds['lon_max'] < bounds['lon_min']:
            lon_grid = np.concatenate([
                np.arange(bounds['lon_min'], 180, resolution),
                np.arange(-180, bounds['lon_max'], resolution)
            ])
        
        print(f"      Grid: {len(lat_grid)} × {len(lon_grid)} points")
        print(f"      Processing {len(time_indices)} daily time steps...")
        
        # Extract currents for each time step
        time_series_data = []
        
        for time_idx, date_str in tqdm(
            zip(time_indices, date_strings),
            total=len(time_indices),
            desc=f"      {region_name}"
        ):
            daily_currents = []
            
            for lat in lat_grid:
                for lon in lon_grid:
                    # Find nearest point
                    lat_idx = np.argmin(np.abs(lats - lat))
                    lon_idx = np.argmin(np.abs(lons - lon))
                    
                    try:
                        # Extract current for this time step
                        if len(uo.shape) == 4:  # time, depth, lat, lon
                            u = float(uo[time_idx, 0, lat_idx, lon_idx])
                            v = float(vo[time_idx, 0, lat_idx, lon_idx])
                        elif len(uo.shape) == 3:  # time, lat, lon
                            u = float(uo[time_idx, lat_idx, lon_idx])
                            v = float(vo[time_idx, lat_idx, lon_idx])
                        else:
                            continue
                        
                        # Check for masked/invalid values
                        if np.ma.is_masked(u) or np.ma.is_masked(v):
                            continue
                        if np.isnan(u) or np.isnan(v):
                            continue
                        
                        magnitude = np.sqrt(u**2 + v**2)
                        
                        # Skip very weak currents
                        if magnitude < 0.01:
                            continue
                        
                        daily_currents.append({
                            'lat': float(lat),
                            'lon': float(lon),
                            'u': round(u, 4),
                            'v': round(v, 4),
                            'speed': round(magnitude, 4)
                        })
                    
                    except Exception:
                        continue
            
            # Add this day's data
            if daily_currents:
                time_series_data.append({
                    'date': date_str,
                    'day_of_year': (datetime.strptime(date_str, '%Y-%m-%d') - start_date).days + 1,
                    'currents': daily_currents
                })
        
        print(f"      ✅ Extracted {len(time_series_data)} days with data")
        
        # Save to JSON
        output_file = output_path / f"ocean_currents_{region_name}_2025.json"
        
        region_data = {
            'region': region_name,
            'year': year,
            'bounds': bounds,
            'resolution': resolution,
            'units': 'm/s',
            'time_steps': len(time_series_data),
            'start_date': date_strings[0] if date_strings else f"{year}-01-01",
            'end_date': date_strings[-1] if date_strings else f"{year}-12-31",
            'data': time_series_data
        }
        
        with open(output_file, 'w') as f:
            json.dump(region_data, f, indent=2)
        
        file_size = output_file.stat().st_size / (1024 * 1024)  # MB
        print(f"      💾 Saved: {output_file.name} ({file_size:.2f} MB)")
    
    ds.close()
    
    # Create metadata
    metadata = {
        'year': year,
        'start_date': f"{year}-01-01",
        'end_date': f"{year}-12-31",
        'time_steps': len(time_indices),
        'resolution_degrees': resolution,
        'regions': list(antarctic_regions.keys()),
        'units': 'm/s',
        'usage': 'UI should load current data based on today\'s date (day of year)',
        'description': f'Daily ocean surface currents for Antarctic region, year {year}'
    }
    
    metadata_file = output_path / 'ocean_currents_yearly_metadata.json'
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n💾 Metadata: {metadata_file.name}")
    
    print("\n" + "=" * 70)
    print("🎉 YEARLY DATA EXTRACTION COMPLETE!")
    print("=" * 70)
    
    print(f"\n✅ Extracted ocean currents for {year}:")
    print(f"   Time period: {date_strings[0]} to {date_strings[-1]}")
    print(f"   Daily time steps: {len(time_indices)}")
    print(f"   Regions: {len(antarctic_regions)}")
    
    print(f"\n📋 Files created:")
    for json_file in sorted(output_path.glob("*_2025.json")):
        size_mb = json_file.stat().st_size / (1024 * 1024)
        print(f"   • {json_file.name} ({size_mb:.2f} MB)")
    
    print(f"\n🚀 UI Integration:")
    print(f"   1. Backend API should:")
    print(f"      - Get current date from request")
    print(f"      - Calculate day of year (1-365)")
    print(f"      - Return currents for that day from JSON")
    print(f"   2. Frontend should:")
    print(f"      - Pass today's date to API")
    print(f"      - Display ocean currents matching current date")
    print(f"      - Animate particles based on u/v vectors")

if __name__ == "__main__":
    # Paths
    base_dir = Path(__file__).parent
    netcdf_file = base_dir / "data" / "ocean_currents_2025_2026_daily.nc"
    output_directory = base_dir / "data" / "ocean_currents_yearly"
    
    # Check if NetCDF file exists
    if not netcdf_file.exists():
        print(f"\n❌ Ocean data file not found: {netcdf_file}")
        print(f"\n   The file may have been deleted.")
        print(f"   Using existing processed data instead.")
        exit(1)
    
    # Extract full year 2025 with daily time steps
    extract_yearly_ocean_currents(
        netcdf_path=str(netcdf_file),
        output_dir=str(output_directory),
        year=2025,
        resolution=1.0  # 1 degree (~111 km)
    )
    
    print("\n" + "=" * 70)
