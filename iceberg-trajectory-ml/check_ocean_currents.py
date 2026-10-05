"""
Check Ocean Current NetCDF File and Test Integration
Examine CMEMS ocean current data for iceberg prediction
"""
import netCDF4 as nc
import numpy as np
from pathlib import Path

def check_netcdf_file(file_path):
    """Examine the NetCDF file structure and contents"""
    print("🌊 CHECKING OCEAN CURRENT DATA FILE")
    print("=" * 70)
    
    try:
        # Open the NetCDF file
        ds = nc.Dataset(file_path, 'r')
        
        print(f"\n✅ File opened successfully!")
        print(f"   {Path(file_path).name}")
        print("\n" + "=" * 70)
        
        # 1. DIMENSIONS
        print("\n📏 DIMENSIONS:")
        for dim_name, dim in ds.dimensions.items():
            print(f"   {dim_name}: {len(dim)}")
        
        # 2. VARIABLES
        print("\n📊 VARIABLES AVAILABLE:")
        for var_name in ds.variables.keys():
            var = ds.variables[var_name]
            long_name = getattr(var, 'long_name', 'N/A')
            units = getattr(var, 'units', 'N/A')
            print(f"   • {var_name}: {long_name} [{units}]")
        
        # 3. GEOGRAPHIC COVERAGE
        print("\n" + "=" * 70)
        print("🌍 GEOGRAPHIC COVERAGE:")
        
        has_lat = 'latitude' in ds.variables
        has_lon = 'longitude' in ds.variables
        
        if has_lat:
            lat = ds.variables['latitude'][:]
            print(f"\n   📍 Latitude:")
            print(f"      Range: {lat.min():.2f}° to {lat.max():.2f}°")
            antarctic_coverage = lat.min() < -55
            if antarctic_coverage:
                print(f"      ✅ Covers Antarctic region (< -55°)")
            else:
                print(f"      ⚠️  May not fully cover Antarctic")
        
        if has_lon:
            lon = ds.variables['longitude'][:]
            print(f"\n   📍 Longitude:")
            print(f"      Range: {lon.min():.2f}° to {lon.max():.2f}°")
            global_coverage = (lon.max() - lon.min()) > 350
            print(f"      {'✅ Global coverage' if global_coverage else '⚠️ Regional coverage'}")
        
        # 4. TIME DIMENSION
        if 'time' in ds.variables:
            time_var = ds.variables['time']
            print(f"\n   📅 Time:")
            print(f"      Time steps: {len(time_var)}")
            print(f"      Units: {getattr(time_var, 'units', 'N/A')}")
        
        # 5. DEPTH
        if 'depth' in ds.variables:
            depth = ds.variables['depth'][:]
            print(f"\n   🌊 Depth:")
            print(f"      Levels: {len(depth)}")
            print(f"      Range: {depth.min():.1f}m to {depth.max():.1f}m")
            print(f"      Surface level: {depth[0]:.1f}m")
        
        # 6. OCEAN CURRENT DATA
        print("\n" + "=" * 70)
        print("🌊 OCEAN CURRENT DATA:")
        
        # Check for current velocity variables
        current_vars = {
            'uo': 'Eastward velocity',
            'vo': 'Northward velocity',
            'u': 'U-component',
            'v': 'V-component',
            'ucur': 'Eastward current',
            'vcur': 'Northward current'
        }
        
        found_currents = []
        for var_name, description in current_vars.items():
            if var_name in ds.variables:
                found_currents.append(var_name)
                var = ds.variables[var_name]
                print(f"\n   ✅ {var_name} ({description})")
                print(f"      Shape: {var.shape}")
                
                # Get sample data
                data = var[:]
                if hasattr(data, 'mask'):
                    valid_data = data[~data.mask]
                else:
                    valid_data = data.flatten()
                
                if len(valid_data) > 0:
                    print(f"      Range: {valid_data.min():.4f} to {valid_data.max():.4f} m/s")
                    print(f"      Mean: {valid_data.mean():.4f} m/s")
        
        # 7. SUITABILITY ASSESSMENT
        print("\n" + "=" * 70)
        print("✅ SUITABILITY FOR ICEBERG PREDICTION:")
        
        has_currents = len(found_currents) >= 2
        suitable = has_lat and has_lon and has_currents and (lat.min() < -55 if has_lat else False)
        
        print(f"\n   ✓ Latitude/Longitude: {'YES ✅' if has_lat and has_lon else 'NO ❌'}")
        print(f"   ✓ Ocean currents (u/v): {'YES ✅' if has_currents else 'NO ❌'}")
        print(f"   ✓ Antarctic coverage: {'YES ✅' if (has_lat and lat.min() < -55) else 'NO ❌'}")
        
        if suitable:
            print(f"\n   🎉 FILE IS SUITABLE!")
            print(f"   📌 Can be integrated with LSTM for lat/lon prediction")
            print(f"\n   Found current variables: {', '.join(found_currents)}")
        else:
            print(f"\n   ⚠️  FILE MAY HAVE ISSUES")
        
        # 8. INTEGRATION PLAN
        if suitable:
            print("\n" + "=" * 70)
            print("🔧 INTEGRATION WITH LSTM MODEL:")
            print("\n   The ocean current data will enhance predictions by:")
            print("   1. Extract current velocity (u, v) at iceberg position")
            print("   2. Use currents as additional LSTM input features")
            print("   3. Calculate drift: new_lat, new_lon based on currents")
            print("   4. Predict future latitude and longitude coordinates")
            print("\n   Output: Predicted (latitude, longitude) positions")
        
        ds.close()
        return suitable
        
    except FileNotFoundError:
        print(f"❌ ERROR: File not found at {file_path}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_current_extraction(file_path, test_lat=-66.5, test_lon=45.2):
    """Test extracting current data at a specific location"""
    print("\n" + "=" * 70)
    print("🧪 TESTING CURRENT EXTRACTION AT ICEBERG POSITION")
    print("=" * 70)
    
    try:
        ds = nc.Dataset(file_path, 'r')
        
        print(f"\n📍 Test position: ({test_lat}°, {test_lon}°)")
        
        # Get coordinates
        lats = ds.variables['latitude'][:]
        lons = ds.variables['longitude'][:]
        
        # Find nearest grid point
        lat_idx = np.argmin(np.abs(lats - test_lat))
        lon_idx = np.argmin(np.abs(lons - test_lon))
        
        actual_lat = lats[lat_idx]
        actual_lon = lons[lon_idx]
        
        print(f"   Nearest grid point: ({actual_lat:.2f}°, {actual_lon:.2f}°)")
        
        # Extract currents
        if 'uo' in ds.variables and 'vo' in ds.variables:
            uo = ds.variables['uo']
            vo = ds.variables['vo']
            
            # Get dimensions
            print(f"\n   Current data shape: {uo.shape}")
            
            # Extract at surface and first time step
            if len(uo.shape) == 4:  # time, depth, lat, lon
                u_current = uo[0, 0, lat_idx, lon_idx]
                v_current = vo[0, 0, lat_idx, lon_idx]
            elif len(uo.shape) == 3:  # time, lat, lon
                u_current = uo[0, lat_idx, lon_idx]
                v_current = vo[0, lat_idx, lon_idx]
            else:
                u_current = uo[lat_idx, lon_idx]
                v_current = vo[lat_idx, lon_idx]
            
            print(f"\n   🌊 Extracted ocean currents:")
            print(f"      Eastward (u): {u_current:.4f} m/s")
            print(f"      Northward (v): {v_current:.4f} m/s")
            
            # Calculate speed and direction
            speed = np.sqrt(u_current**2 + v_current**2)
            direction = np.arctan2(v_current, u_current) * 180 / np.pi
            
            print(f"      Speed: {speed:.4f} m/s ({speed*86400/1000:.2f} km/day)")
            print(f"      Direction: {direction:.1f}° from East")
            
            print(f"\n   ✅ Current extraction successful!")
            print(f"   📌 This data can be fed into LSTM for prediction")
            
        ds.close()
        return True
        
    except Exception as e:
        print(f"\n   ❌ Extraction failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🧊 CRYONAV OCEAN CURRENT DATA CHECKER")
    print("=" * 70)
    
    # Path to NetCDF file in DATA directory
    nc_file = Path(__file__).parent.parent / "DATA" / "cmems_mod_glo_phy-cur_anfc_0.083deg_P1M-m_1791042227247.nc"
    
    if nc_file.exists():
        print(f"\n✅ Found file: {nc_file.name}")
        
        # Check file structure
        is_suitable = check_netcdf_file(str(nc_file))
        
        # Test extraction
        if is_suitable:
            test_current_extraction(str(nc_file))
        
        print("\n" + "=" * 70)
        print("📋 SUMMARY:")
        if is_suitable:
            print("\n   ✅ File is suitable for LSTM integration")
            print("   ✅ Can predict latitude and longitude")
            print("\n   Next step: Run 'integrate_ocean_lstm.py' to enhance model")
        else:
            print("\n   ⚠️  File may need review before integration")
        
    else:
        print(f"\n❌ File not found!")
        print(f"   Expected: {nc_file}")
        print(f"\n   Please ensure the NetCDF file is in the DATA directory")
    
    print("\n" + "=" * 70)
