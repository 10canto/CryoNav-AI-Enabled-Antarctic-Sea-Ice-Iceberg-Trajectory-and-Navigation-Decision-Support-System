"""
Integrate Ocean Current Data with Iceberg Dataset for Training
Combines downloaded ocean currents with iceberg positions
"""
import pandas as pd
import numpy as np
import netCDF4 as nc
from pathlib import Path
from tqdm import tqdm

def integrate_ocean_data():
    """
    Integrate ocean current data with iceberg trajectory dataset
    """
    
    print("\n" + "=" * 70)
    print("🧊 OCEAN CURRENT + ICEBERG DATA INTEGRATION")
    print("=" * 70)
    
    base_dir = Path(__file__).parent
    
    # Check for downloaded ocean data (recent year)
    ocean_file_recent = base_dir / "data" / "ocean_currents_2025_2026_daily.nc"
    
    # Check for existing ocean data (your original file)
    ocean_file_original = base_dir.parent / "DATA" / "cmems_mod_glo_phy-cur_anfc_0.083deg_P1M-m_1791042227247.nc"
    
    # Determine which file to use
    if ocean_file_recent.exists():
        ocean_data_path = ocean_file_recent
        print(f"\n✅ Using downloaded ocean data: {ocean_file_recent.name}")
    elif ocean_file_original.exists():
        ocean_data_path = ocean_file_original
        print(f"\n✅ Using existing ocean data: {ocean_file_original.name}")
    else:
        print("\n❌ No ocean current data found!")
        print(f"   Checked: {ocean_file_recent}")
        print(f"   Checked: {ocean_file_original}")
        print("\n   Please download ocean data first or ensure the file exists.")
        return False
    
    # Iceberg data path
    iceberg_data_path = base_dir / "data" / "iceberg_dataset_sample.csv"
    
    if not iceberg_data_path.exists():
        print(f"\n❌ Iceberg dataset not found: {iceberg_data_path}")
        return False
    
    # Output path
    output_path = base_dir / "data" / "iceberg_dataset_with_ocean_currents.csv"
    
    print(f"\n📊 Files:")
    print(f"   Ocean data: {ocean_data_path.name}")
    print(f"   Iceberg data: {iceberg_data_path.name}")
    print(f"   Output: {output_path.name}")
    
    try:
        # Load ocean data
        print(f"\n📂 Loading ocean current data...")
        ocean_ds = nc.Dataset(str(ocean_data_path), 'r')
        
        lats = ocean_ds.variables['latitude'][:]
        lons = ocean_ds.variables['longitude'][:]
        
        print(f"   ✅ Loaded: {len(lats)} lat × {len(lons)} lon points")
        
        # Load iceberg data
        print(f"\n📂 Loading iceberg data...")
        df = pd.read_csv(iceberg_data_path)
        print(f"   Rows: {len(df)}")
        print(f"   Icebergs: {df['iceberg_id'].nunique() if 'iceberg_id' in df.columns else 'unknown'}")
        
        # Add new columns
        df['ocean_current_u'] = np.nan
        df['ocean_current_v'] = np.nan
        df['ocean_current_speed'] = np.nan
        df['ocean_current_direction'] = np.nan
        
        # Extract currents for each position
        print(f"\n🌊 Extracting ocean currents...")
        
        successful = 0
        failed = 0
        
        uo = ocean_ds.variables['uo']
        vo = ocean_ds.variables['vo']
        
        for idx, row in tqdm(df.iterrows(), total=len(df), desc="   Processing"):
            lat = row['lat']  # Column name is 'lat' not 'latitude'
            lon = row['lon']  # Column name is 'lon' not 'longitude'
            
            try:
                # Find nearest grid point
                lat_idx = np.argmin(np.abs(lats - lat))
                lon_idx = np.argmin(np.abs(lons - lon))
                
                # Extract currents (handle different dimensions)
                if len(uo.shape) == 4:  # time, depth, lat, lon
                    u_current = float(uo[0, 0, lat_idx, lon_idx])
                    v_current = float(vo[0, 0, lat_idx, lon_idx])
                elif len(uo.shape) == 3:  # time, lat, lon
                    u_current = float(uo[0, lat_idx, lon_idx])
                    v_current = float(vo[0, lat_idx, lon_idx])
                else:  # lat, lon
                    u_current = float(uo[lat_idx, lon_idx])
                    v_current = float(vo[lat_idx, lon_idx])
                
                # Handle masked/missing values
                if np.ma.is_masked(u_current) or np.ma.is_masked(v_current):
                    failed += 1
                    continue
                
                if np.isnan(u_current) or np.isnan(v_current):
                    failed += 1
                    continue
                
                # Save currents
                df.at[idx, 'ocean_current_u'] = u_current
                df.at[idx, 'ocean_current_v'] = v_current
                
                # Calculate speed and direction
                speed = np.sqrt(u_current**2 + v_current**2)
                direction = np.arctan2(v_current, u_current) * 180 / np.pi
                
                df.at[idx, 'ocean_current_speed'] = speed
                df.at[idx, 'ocean_current_direction'] = direction
                
                successful += 1
                
            except Exception as e:
                failed += 1
        
        ocean_ds.close()
        
        print(f"\n   ✅ Successful: {successful}/{len(df)} ({successful/len(df)*100:.1f}%)")
        if failed > 0:
            print(f"   ⚠️  Failed/missing: {failed}/{len(df)} ({failed/len(df)*100:.1f}%)")
        
        # Save enhanced dataset
        output_path.parent.mkdir(exist_ok=True, parents=True)
        df.to_csv(output_path, index=False)
        
        print(f"\n💾 Enhanced dataset saved: {output_path.name}")
        
        # Show statistics
        print(f"\n📈 Ocean Current Statistics:")
        print(f"   Eastward (u) mean: {df['ocean_current_u'].mean():.4f} m/s")
        print(f"   Northward (v) mean: {df['ocean_current_v'].mean():.4f} m/s")
        print(f"   Speed mean: {df['ocean_current_speed'].mean():.4f} m/s")
        print(f"   Speed max: {df['ocean_current_speed'].max():.4f} m/s")
        
        print("\n" + "=" * 70)
        print("🎉 INTEGRATION COMPLETE!")
        print("=" * 70)
        
        print("\n✅ Enhanced dataset created with ocean current features:")
        print(f"   Output: {output_path}")
        print(f"   New features: ocean_current_u, ocean_current_v, speed, direction")
        
        print("\n🚀 Next Steps:")
        print("   1. Train LSTM with enhanced features")
        print("   2. Model will learn current → iceberg movement relationship")
        print("   3. Improved prediction accuracy expected!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = integrate_ocean_data()
    
    if not success:
        print("\n" + "=" * 70)
        exit(1)
