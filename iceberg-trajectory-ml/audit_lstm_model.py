"""
COMPREHENSIVE LSTM MODEL AUDIT
Evaluates train/test split, prediction target, baselines, and data overlap
"""
import pandas as pd
import numpy as np
import netCDF4 as nc
from pathlib import Path
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points on Earth in kilometers"""
    R = 6371  # Earth radius in km
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c

def check_netcdf_time_dimension(nc_path):
    """Check NetCDF time dimension and time step"""
    print("\n" + "=" * 80)
    print("6. NETCDF TIME DIMENSION CHECK")
    print("=" * 80)
    
    try:
        ds = nc.Dataset(str(nc_path), 'r')
        
        print(f"📂 File: {nc_path.name}")
        print(f"\n📋 Available dimensions:")
        for dim_name, dim in ds.dimensions.items():
            print(f"   {dim_name}: {len(dim)}")
        
        print(f"\n📋 Available variables:")
        for var_name in ds.variables.keys():
            var = ds.variables[var_name]
            print(f"   {var_name}: {var.dimensions} - {var.shape}")
        
        # Check time variable
        if 'time' in ds.variables:
            time_var = ds.variables['time']
            time_units = time_var.units if hasattr(time_var, 'units') else 'unknown'
            time_values = time_var[:]
            
            print(f"\n⏰ Time Information:")
            print(f"   Units: {time_units}")
            print(f"   Number of time steps: {len(time_values)}")
            print(f"   Time range: {time_values[0]} to {time_values[-1]}")
            
            # Convert to dates if possible
            try:
                dates = nc.num2date(time_values, units=time_units)
                print(f"   Date range: {dates[0]} to {dates[-1]}")
                
                # Calculate time step
                if len(dates) > 1:
                    time_deltas = [(dates[i+1] - dates[i]).days for i in range(min(10, len(dates)-1))]
                    avg_delta = np.mean(time_deltas)
                    print(f"   Time step: ~{avg_delta:.1f} days")
                    
                    if avg_delta < 2:
                        print(f"   ✅ DAILY data")
                    elif 28 <= avg_delta <= 31:
                        print(f"   ✅ MONTHLY data")
                    else:
                        print(f"   ⚠️  Irregular time step: {avg_delta:.1f} days")
            except:
                print(f"   ⚠️  Could not convert time values to dates")
        
        ds.close()
        
    except Exception as e:
        print(f"❌ Error reading NetCDF: {e}")

def audit_model():
    """Comprehensive model audit"""
    
    print("\n" + "=" * 80)
    print("🔍 LSTM MODEL AUDIT")
    print("=" * 80)
    
    base_dir = Path(__file__).parent
    data_path = base_dir / "data" / "iceberg_dataset_with_ocean_currents.csv"
    nc_path = base_dir.parent / "DATA" / "cmems_mod_glo_phy-cur_anfc_0.083deg_P1M-m_1791042227247.nc"
    
    # Load data
    print(f"\n📂 Loading dataset: {data_path.name}")
    df = pd.read_csv(data_path)
    
    # Parse datetime
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
    
    print(f"   Total rows: {len(df)}")
    print(f"   Unique icebergs: {df['iceberg_id'].nunique()}")
    print(f"   Columns: {list(df.columns)}")
    
    # ========================================================================
    # 1. CHECK TRAIN/TEST SPLIT METHOD
    # ========================================================================
    print("\n" + "=" * 80)
    print("1. TRAIN/TEST SPLIT METHOD CHECK")
    print("=" * 80)
    
    # Current training code (from train_enhanced_model.py)
    data_pairs = []
    for iceberg_id in df['iceberg_id'].unique():
        iceberg_df = df[df['iceberg_id'] == iceberg_id].sort_values('datetime')
        for i in range(len(iceberg_df) - 1):
            current = iceberg_df.iloc[i]
            next_pos = iceberg_df.iloc[i + 1]
            data_pairs.append({
                'iceberg_id': iceberg_id,
                'current_lat': current['lat'],
                'current_lon': current['lon'],
                'ocean_u': current.get('ocean_current_u', 0),
                'ocean_v': current.get('ocean_current_v', 0),
                'next_lat': next_pos['lat'],
                'next_lon': next_pos['lon'],
                'time_delta_days': (pd.to_datetime(next_pos['datetime']) - pd.to_datetime(current['datetime'])).total_seconds() / 86400 if pd.notna(current.get('datetime')) and pd.notna(next_pos.get('datetime')) else 1.0
            })
    
    train_df = pd.DataFrame(data_pairs)
    print(f"\n📊 Total trajectory pairs: {len(train_df)}")
    print(f"   From {train_df['iceberg_id'].nunique()} icebergs")
    
    # Check current split (random)
    X_random = train_df[['current_lat', 'current_lon', 'ocean_u', 'ocean_v']].values
    y_random = train_df[['next_lat', 'next_lon']].values
    
    X_train_rand, X_test_rand, y_train_rand, y_test_rand = train_test_split(
        X_random, y_random, test_size=0.2, random_state=42
    )
    
    print(f"\n❌ CURRENT METHOD: Random row split")
    print(f"   Problem: Test set contains rows from same icebergs as training")
    print(f"   Train samples: {len(X_train_rand)}")
    print(f"   Test samples: {len(X_test_rand)}")
    
    # Proper split by iceberg ID
    print(f"\n✅ CORRECT METHOD: Split by iceberg ID")
    unique_icebergs = list(train_df['iceberg_id'].unique())
    np.random.seed(42)
    np.random.shuffle(unique_icebergs)
    split_idx = int(len(unique_icebergs) * 0.8)
    train_icebergs = unique_icebergs[:split_idx]
    test_icebergs = unique_icebergs[split_idx:]
    
    train_mask = train_df['iceberg_id'].isin(train_icebergs)
    test_mask = train_df['iceberg_id'].isin(test_icebergs)
    
    X_train_proper = train_df[train_mask][['current_lat', 'current_lon', 'ocean_u', 'ocean_v']].values
    y_train_proper = train_df[train_mask][['next_lat', 'next_lon']].values
    X_test_proper = train_df[test_mask][['current_lat', 'current_lon', 'ocean_u', 'ocean_v']].values
    y_test_proper = train_df[test_mask][['next_lat', 'next_lon']].values
    
    print(f"   Train icebergs: {len(train_icebergs)} ({len(X_train_proper)} samples)")
    print(f"   Test icebergs: {len(test_icebergs)} ({len(X_test_proper)} samples)")
    print(f"   ✅ No overlap between train and test icebergs")
    
    # ========================================================================
    # 2. CHECK PREDICTION TARGET (ABSOLUTE VS DISPLACEMENT)
    # ========================================================================
    print("\n" + "=" * 80)
    print("2. PREDICTION TARGET CHECK")
    print("=" * 80)
    
    print(f"\n❌ CURRENT: Predicting absolute lat/lon")
    print(f"   Problem: Model learns geographic patterns, not dynamics")
    print(f"   Example: next_lat = {y_train_proper[0, 0]:.4f}°, next_lon = {y_train_proper[0, 1]:.4f}°")
    
    # Create displacement targets
    train_df['dlat'] = train_df['next_lat'] - train_df['current_lat']
    train_df['dlon'] = train_df['next_lon'] - train_df['current_lon']
    
    print(f"\n✅ CORRECT: Predicting displacement (dlat, dlon)")
    print(f"   Learns dynamics: how position changes given currents")
    print(f"   Example: dlat = {train_df.iloc[0]['dlat']:.4f}°, dlon = {train_df.iloc[0]['dlon']:.4f}°")
    
    y_train_displacement = train_df[train_mask][['dlat', 'dlon']].values
    y_test_displacement = train_df[test_mask][['dlat', 'dlon']].values
    
    # ========================================================================
    # 3. BASELINE MODELS
    # ========================================================================
    print("\n" + "=" * 80)
    print("3. BASELINE MODEL COMPARISON")
    print("=" * 80)
    
    # Prepare test data with time deltas
    test_df = train_df[test_mask].copy()
    
    # Baseline 1: Iceberg stays at last position
    print(f"\n🔵 Baseline 1: 'Iceberg stays at last position'")
    y_pred_stay = X_test_proper[:, :2]  # Just use current position
    
    # Baseline 2: Last velocity continues (use ocean currents as proxy)
    print(f"🔵 Baseline 2: 'Last velocity continues' (ocean current drift)")
    y_pred_velocity = np.zeros_like(y_test_proper)
    for i in range(len(X_test_proper)):
        current_lat, current_lon, u, v = X_test_proper[i]
        time_delta_days = test_df.iloc[i]['time_delta_days']
        
        # Convert m/s to degrees
        dlat = (v * 86400 * time_delta_days) / 111000
        dlon = (u * 86400 * time_delta_days) / (111000 * np.cos(radians(current_lat)))
        
        y_pred_velocity[i, 0] = current_lat + dlat
        y_pred_velocity[i, 1] = current_lon + dlon
    
    # Simple LSTM proxy: Use ocean currents (since no actual LSTM trained yet)
    print(f"🟢 LSTM Model: Ocean current-based prediction")
    y_pred_lstm = y_pred_velocity  # Placeholder - same as baseline 2 for now
    
    # ========================================================================
    # 4. ERROR IN KM AT MULTIPLE HORIZONS
    # ========================================================================
    print("\n" + "=" * 80)
    print("4. ERROR METRICS (Haversine Distance in km)")
    print("=" * 80)
    
    # Calculate errors for different time horizons
    horizons = [24, 48, 72]  # hours
    
    results = []
    
    for horizon_hours in horizons:
        # Filter test samples by time horizon
        horizon_days = horizon_hours / 24
        horizon_mask = np.abs(test_df['time_delta_days'].values - horizon_days) < 0.5
        
        if horizon_mask.sum() == 0:
            continue
        
        y_true_horizon = y_test_proper[horizon_mask]
        y_stay_horizon = y_pred_stay[horizon_mask]
        y_vel_horizon = y_pred_velocity[horizon_mask]
        y_lstm_horizon = y_pred_lstm[horizon_mask]
        
        # Calculate errors in km
        errors_stay = [haversine_distance(y_true_horizon[i, 0], y_true_horizon[i, 1],
                                          y_stay_horizon[i, 0], y_stay_horizon[i, 1])
                      for i in range(len(y_true_horizon))]
        
        errors_velocity = [haversine_distance(y_true_horizon[i, 0], y_true_horizon[i, 1],
                                              y_vel_horizon[i, 0], y_vel_horizon[i, 1])
                          for i in range(len(y_true_horizon))]
        
        errors_lstm = [haversine_distance(y_true_horizon[i, 0], y_true_horizon[i, 1],
                                         y_lstm_horizon[i, 0], y_lstm_horizon[i, 1])
                      for i in range(len(y_true_horizon))]
        
        results.append({
            'horizon': f'{horizon_hours}h',
            'n_samples': len(y_true_horizon),
            'stay_mean': np.mean(errors_stay),
            'stay_median': np.median(errors_stay),
            'velocity_mean': np.mean(errors_velocity),
            'velocity_median': np.median(errors_velocity),
            'lstm_mean': np.mean(errors_lstm),
            'lstm_median': np.median(errors_lstm)
        })
    
    # ========================================================================
    # 5. CHECK DATE OVERLAP WITH OCEAN DATA
    # ========================================================================
    print("\n" + "=" * 80)
    print("5. ICEBERG DATES VS OCEAN CURRENT DATES")
    print("=" * 80)
    
    ocean_start = datetime(2025, 10, 1)
    ocean_end = datetime(2026, 10, 31)
    
    print(f"\n🌊 Ocean current data range:")
    print(f"   {ocean_start.strftime('%Y-%m-%d')} to {ocean_end.strftime('%Y-%m-%d')}")
    
    df_with_dates = df.dropna(subset=['datetime'])
    
    if len(df_with_dates) > 0:
        iceberg_dates = pd.to_datetime(df_with_dates['datetime'])
        print(f"\n🧊 Iceberg trajectory data range:")
        print(f"   {iceberg_dates.min().strftime('%Y-%m-%d')} to {iceberg_dates.max().strftime('%Y-%m-%d')}")
        
        # Check overlap
        overlap_mask = (iceberg_dates >= ocean_start) & (iceberg_dates <= ocean_end)
        n_overlap = overlap_mask.sum()
        
        print(f"\n📊 Date overlap:")
        print(f"   Total iceberg samples: {len(df_with_dates)}")
        print(f"   Overlapping with ocean data: {n_overlap} ({n_overlap/len(df_with_dates)*100:.1f}%)")
        print(f"   Before ocean data: {(iceberg_dates < ocean_start).sum()}")
        print(f"   After ocean data: {(iceberg_dates > ocean_end).sum()}")
        
        if n_overlap == 0:
            print(f"\n   ❌ WARNING: NO OVERLAP between iceberg dates and ocean current dates!")
            print(f"   Your ocean currents are from 2025-2026, but icebergs are from different years")
    else:
        print(f"\n⚠️  No datetime information in iceberg dataset")
    
    # Check NetCDF time dimension
    if nc_path.exists():
        check_netcdf_time_dimension(nc_path)
    
    # ========================================================================
    # SUMMARY TABLE
    # ========================================================================
    print("\n" + "=" * 80)
    print("📊 SUMMARY TABLE")
    print("=" * 80)
    
    print(f"\n{'Model':<25} {'Horizon':<10} {'N':<8} {'Mean (km)':<15} {'Median (km)':<15}")
    print("-" * 80)
    
    for r in results:
        print(f"{'Stay at position':<25} {r['horizon']:<10} {r['n_samples']:<8} {r['stay_mean']:<15.2f} {r['stay_median']:<15.2f}")
        print(f"{'Velocity continues':<25} {r['horizon']:<10} {r['n_samples']:<8} {r['velocity_mean']:<15.2f} {r['velocity_median']:<15.2f}")
        print(f"{'LSTM (placeholder)':<25} {r['horizon']:<10} {r['n_samples']:<8} {r['lstm_mean']:<15.2f} {r['lstm_median']:<15.2f}")
        print("-" * 80)
    
    # ========================================================================
    # AUDIT FINDINGS
    # ========================================================================
    print("\n" + "=" * 80)
    print("🔍 AUDIT FINDINGS")
    print("=" * 80)
    
    print(f"\n1. ❌ TRAIN/TEST SPLIT: Currently uses RANDOM ROW split")
    print(f"   Should use: Split by iceberg ID to prevent data leakage")
    
    print(f"\n2. ❌ PREDICTION TARGET: Currently predicts ABSOLUTE lat/lon")
    print(f"   Should predict: DISPLACEMENT (dlat, dlon)")
    
    print(f"\n3. ✅ BASELINE MODELS: Implemented")
    print(f"   - 'Stay at position' baseline")
    print(f"   - 'Velocity continues' baseline")
    
    print(f"\n4. ✅ ERROR METRICS: Calculated in km (haversine)")
    print(f"   Mean and median errors at 24h, 48h, 72h horizons")
    
    print(f"\n5. ⚠️  DATE OVERLAP: Check results above")
    if len(df_with_dates) > 0:
        print(f"   {n_overlap}/{len(df_with_dates)} samples overlap with ocean data")
    
    print(f"\n6. ℹ️  NETCDF TIME DIMENSION: Check results above")
    
    print("\n" + "=" * 80)
    print("✅ AUDIT COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    audit_model()
