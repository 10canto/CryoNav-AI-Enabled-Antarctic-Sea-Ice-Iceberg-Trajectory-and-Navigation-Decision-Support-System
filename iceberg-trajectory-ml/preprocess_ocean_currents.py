"""
Pre-process Ocean Current Data for Frontend Visualization
Extracts and downsamples ocean currents from NetCDF to JSON
"""
import netCDF4 as nc
import numpy as np
import json
from pathlib import Path
from tqdm import tqdm

def extract_ocean_currents_grid(netcdf_path, output_dir, resolution=1.0):
    """
    Extract ocean currents from NetCDF and save as JSON grid
    
    Args:
        netcdf_path: Path to NetCDF file
        output_dir: Directory to save JSON files
        resolution: Grid resolution in degrees (default 1.0 = ~111km)
    """
    
    print("\n" + "=" * 70)
    print("🌊 OCEAN CURRENT DATA PRE-PROCESSING")
    print("=" * 70)
    
    print(f"\n📂 Loading ocean data: {Path(netcdf_path).name}")
    
    # Open NetCDF file
    ds = nc.Dataset(netcdf_path, 'r')
    
    # Get dimensions
    lats = ds.variables['latitude'][:]
    lons = ds.variables['longitude'][:]
    
    print(f"   Original grid: {len(lats)} × {len(lons)} points")
    print(f"   Lat range: {lats.min():.2f}° to {lats.max():.2f}°")
    print(f"   Lon range: {lons.min():.2f}° to {lons.max():.2f}°")
    
    # Get current data
    uo = ds.variables['uo']
    vo = ds.variables['vo']
    
    print(f"   Current data shape: {uo.shape}")
    
    # Antarctic region bounds
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
    
    print(f"\n🔧 Processing {len(antarctic_regions)} regions...")
    
    for region_name, bounds in antarctic_regions.items():
        print(f"\n   📍 Region: {region_name}")
        print(f"      Bounds: {bounds['lat_min']}° to {bounds['lat_max']}°, "
              f"{bounds['lon_min']}° to {bounds['lon_max']}°")
        
        # Create downsampled grid
        lat_grid = np.arange(bounds['lat_min'], bounds['lat_max'], resolution)
        lon_grid = np.arange(bounds['lon_min'], bounds['lon_max'], resolution)
        
        # Handle wraparound for Ross Sea
        if bounds['lon_max'] < bounds['lon_min']:
            lon_grid = np.concatenate([
                np.arange(bounds['lon_min'], 180, resolution),
                np.arange(-180, bounds['lon_max'], resolution)
            ])
        
        print(f"      Downsampled grid: {len(lat_grid)} × {len(lon_grid)} points")
        
        # Extract currents for grid
        grid_data = []
        
        for lat in tqdm(lat_grid, desc=f"      Processing {region_name}"):
            for lon in lon_grid:
                # Find nearest point in original data
                lat_idx = np.argmin(np.abs(lats - lat))
                lon_idx = np.argmin(np.abs(lons - lon))
                
                try:
                    # Extract current (handle different dimensions)
                    if len(uo.shape) == 4:  # time, depth, lat, lon
                        u = float(uo[0, 0, lat_idx, lon_idx])
                        v = float(vo[0, 0, lat_idx, lon_idx])
                    elif len(uo.shape) == 3:  # time, lat, lon
                        u = float(uo[0, lat_idx, lon_idx])
                        v = float(vo[0, lat_idx, lon_idx])
                    else:  # lat, lon
                        u = float(uo[lat_idx, lon_idx])
                        v = float(vo[lat_idx, lon_idx])
                    
                    # Check for masked/invalid values
                    if np.ma.is_masked(u) or np.ma.is_masked(v):
                        continue
                    if np.isnan(u) or np.isnan(v):
                        continue
                    
                    # Calculate magnitude
                    magnitude = np.sqrt(u**2 + v**2)
                    
                    # Skip very weak currents (< 1 cm/s)
                    if magnitude < 0.01:
                        continue
                    
                    grid_data.append({
                        'lat': float(lat),
                        'lon': float(lon),
                        'u': round(u, 4),  # m/s eastward
                        'v': round(v, 4),  # m/s northward
                        'speed': round(magnitude, 4)  # m/s
                    })
                
                except Exception:
                    continue
        
        print(f"      ✅ Extracted {len(grid_data)} valid current vectors")
        
        # Save to JSON
        output_file = output_path / f"ocean_currents_{region_name}.json"
        
        region_data = {
            'region': region_name,
            'bounds': bounds,
            'resolution': resolution,
            'units': 'm/s',
            'timestamp': '2025-10-01T00:00:00Z',
            'data': grid_data
        }
        
        with open(output_file, 'w') as f:
            json.dump(region_data, f, indent=2)
        
        file_size = output_file.stat().st_size / 1024  # KB
        print(f"      💾 Saved: {output_file.name} ({file_size:.1f} KB)")
    
    ds.close()
    
    # Create combined metadata file
    metadata = {
        'source': 'CMEMS Global Ocean Physics',
        'resolution_degrees': resolution,
        'regions': list(antarctic_regions.keys()),
        'units': 'm/s',
        'description': 'Ocean surface currents for Antarctic navigation'
    }
    
    metadata_file = output_path / 'ocean_currents_metadata.json'
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n💾 Metadata saved: {metadata_file.name}")
    
    print("\n" + "=" * 70)
    print("🎉 PRE-PROCESSING COMPLETE!")
    print("=" * 70)
    
    print(f"\n✅ Processed ocean current data:")
    print(f"   Output directory: {output_path}")
    print(f"   Regions: {len(antarctic_regions)}")
    print(f"   Resolution: {resolution}° (~{resolution * 111:.0f} km)")
    
    print(f"\n📋 Files created:")
    for json_file in sorted(output_path.glob("*.json")):
        size_kb = json_file.stat().st_size / 1024
        print(f"   • {json_file.name} ({size_kb:.1f} KB)")
    
    print(f"\n🚀 Next steps:")
    print(f"   1. Copy JSON files to backend: cryonav-backend/data/ocean_currents/")
    print(f"   2. Add API endpoint to serve current data")
    print(f"   3. Create frontend animation component")

if __name__ == "__main__":
    # Paths
    base_dir = Path(__file__).parent
    netcdf_file = base_dir / "data" / "ocean_currents_2025_2026_daily.nc"
    output_directory = base_dir / "data" / "ocean_currents_processed"
    
    # Check if NetCDF file exists
    if not netcdf_file.exists():
        print(f"\n❌ Ocean data file not found: {netcdf_file}")
        print(f"\n   Please ensure the NetCDF file is downloaded.")
        exit(1)
    
    # Pre-process with 1 degree resolution (~111 km grid)
    # Adjust resolution for more/less detail:
    # - 0.5 = ~55km (more detail, larger files)
    # - 1.0 = ~111km (balanced)
    # - 2.0 = ~222km (less detail, smaller files)
    
    extract_ocean_currents_grid(
        netcdf_path=str(netcdf_file),
        output_dir=str(output_directory),
        resolution=1.0
    )
    
    print("\n" + "=" * 70)
