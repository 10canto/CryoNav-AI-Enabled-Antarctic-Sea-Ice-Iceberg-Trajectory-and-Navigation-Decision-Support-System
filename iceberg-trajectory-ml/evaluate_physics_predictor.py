"""
Evaluate Physics-Based Predictor on Real 2025-26 Icebergs
Compare against baselines: "stay in place" and "constant velocity"
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2
import sys

sys.path.append(str(Path(__file__).parent / "src"))
from physics_predictor import PhysicsPredictor

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km"""
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def evaluate_physics_predictor():
    """Evaluate physics predictor on icebergs within ocean current date range"""
    
    print("\n" + "=" * 80)
    print("PHYSICS PREDICTOR EVALUATION")
    print("=" * 80)
    
    # Load iceberg data
    data_path = Path(__file__).parent / "data" / "iceberg_dataset_with_ocean_currents.csv"
    
    if not data_path.exists():
        print(f"ERROR: Data not found at {data_path}")
        return
    
    df = pd.read_csv(data_path)
    df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
    df = df.dropna(subset=['lat', 'lon', 'datetime'])
    
    print(f"\nTotal dataset: {len(df)} observations, {df['iceberg_id'].nunique()} icebergs")
    
    # Filter to ocean current date range (Oct 2025 - Aug 2026)
    ocean_start = datetime(2025, 10, 1)
    ocean_end = datetime(2026, 8, 31)
    
    df_in_range = df[(df['datetime'] >= ocean_start) & (df['datetime'] <= ocean_end)].copy()
    
    print(f"Icebergs in ocean current date range ({ocean_start.date()} to {ocean_end.date()}):")
    print(f"  {len(df_in_range)} observations from {df_in_range['iceberg_id'].nunique()} icebergs")
    
    if len(df_in_range) == 0:
        print("\nWARNING: No icebergs found in ocean current date range!")
        print("Cannot evaluate physics predictor - no ground truth data available.")
        
        # Save empty results
        results_dir = Path(__file__).parent / "results"
        results_dir.mkdir(exist_ok=True)
        
        with open(results_dir / "physics_vs_baselines.md", 'w') as f:
            f.write("# Physics Predictor Evaluation\n\n")
            f.write("**Status:** Cannot evaluate\n\n")
            f.write("**Problem:** No icebergs in ocean current date range (Oct 2025 - Aug 2026)\n\n")
            f.write("**Dataset Details:**\n")
            f.write(f"- Total observations: {len(df)}\n")
            f.write(f"- Date range: {df['datetime'].min()} to {df['datetime'].max()}\n")
            f.write(f"- Ocean current data: Oct 2025 - Aug 2026 (monthly)\n")
            f.write(f"- Overlap: 0 observations\n\n")
            f.write("**Conclusion:** Physics predictor cannot be validated without ground truth data in the correct time period.\n")
        
        print(f"\nResults saved to: results/physics_vs_baselines.md")
        return
    
    # Initialize physics predictor
    print("\nInitializing physics predictor...")
    predictor = PhysicsPredictor()
    
    # Create test sequences (need at least 24h, 48h, 72h ahead observations)
    print("\nCreating test sequences...")
    
    test_sequences = []
    
    for iceberg_id in df_in_range['iceberg_id'].unique():
        iceberg_df = df_in_range[df_in_range['iceberg_id'] == iceberg_id].sort_values('datetime').reset_index(drop=True)
        
        if len(iceberg_df) < 4:  # Need at least 4 observations
            continue
        
        for i in range(len(iceberg_df) - 3):
            start_obs = iceberg_df.iloc[i]
            
            # Find observations at roughly 24h, 48h, 72h
            future_obs = []
            for hours_target in [24, 48, 72]:
                target_time = start_obs['datetime'] + timedelta(hours=hours_target)
                # Find closest observation within ±12 hours
                future_df = iceberg_df.iloc[i+1:]
                if len(future_df) == 0:
                    continue
                time_diffs = (future_df['datetime'] - target_time).abs()
                if len(time_diffs) > 0 and time_diffs.min() < timedelta(hours=12):
                    closest_idx = time_diffs.idxmin()
                    closest_obs = iceberg_df.loc[closest_idx]
                    future_obs.append({
                        'hours': hours_target,
                        'actual_hours': (closest_obs['datetime'] - start_obs['datetime']).total_seconds() / 3600,
                        'lat': closest_obs['lat'],
                        'lon': closest_obs['lon']
                    })
            
            if len(future_obs) >= 1:  # At least one future observation
                # Calculate velocity from recent observations
                if i > 0:
                    prev_obs = iceberg_df.iloc[i-1]
                    time_diff = (start_obs['datetime'] - prev_obs['datetime']).total_seconds() / 3600
                    if time_diff > 0:
                        vel_lat = (start_obs['lat'] - prev_obs['lat']) / time_diff
                        vel_lon = (start_obs['lon'] - prev_obs['lon']) / time_diff
                    else:
                        vel_lat, vel_lon = 0, 0
                else:
                    vel_lat, vel_lon = 0, 0
                
                test_sequences.append({
                    'iceberg_id': iceberg_id,
                    'start_lat': start_obs['lat'],
                    'start_lon': start_obs['lon'],
                    'start_date': start_obs['datetime'],
                    'vel_lat': vel_lat,
                    'vel_lon': vel_lon,
                    'future': future_obs
                })
    
    print(f"Created {len(test_sequences)} test sequences")
    
    if len(test_sequences) == 0:
        print("\nWARNING: No valid test sequences (need observations with 24h/48h/72h follow-up)")
        return
    
    # Evaluate all models
    print("\nEvaluating models...")
    
    results_by_horizon = {24: [], 48: [], 72: []}
    
    for seq_idx, seq in enumerate(test_sequences):
        if (seq_idx + 1) % 10 == 0:
            print(f"  Processing {seq_idx + 1}/{len(test_sequences)}...")
        
        start_lat = seq['start_lat']
        start_lon = seq['start_lon']
        start_date = seq['start_date']
        vel_lat = seq['vel_lat']
        vel_lon = seq['vel_lon']
        
        # Run physics predictor
        try:
            physics_result = predictor.predict_drift(
                lat=start_lat,
                lon=start_lon,
                date=start_date,
                hours=72,
                n_monte_carlo=50  # Reduce for speed
            )
            physics_path = {p['hours']: (p['lat'], p['lon']) for p in physics_result['mean_path']}
        except Exception as e:
            print(f"    Physics predictor failed: {e}")
            continue
        
        # Evaluate at each horizon
        for future_obs in seq['future']:
            hours = future_obs['hours']
            true_lat = future_obs['lat']
            true_lon = future_obs['lon']
            
            # Baseline 1: Stay in place
            pred_stay_lat = start_lat
            pred_stay_lon = start_lon
            error_stay = haversine_distance(pred_stay_lat, pred_stay_lon, true_lat, true_lon)
            
            # Baseline 2: Constant velocity
            pred_vel_lat = start_lat + vel_lat * hours
            pred_vel_lon = start_lon + vel_lon * hours
            error_velocity = haversine_distance(pred_vel_lat, pred_vel_lon, true_lat, true_lon)
            
            # Physics predictor
            if hours in physics_path:
                pred_phys_lat, pred_phys_lon = physics_path[hours]
                error_physics = haversine_distance(pred_phys_lat, pred_phys_lon, true_lat, true_lon)
            else:
                error_physics = np.nan
            
            results_by_horizon[hours].append({
                'error_stay': error_stay,
                'error_velocity': error_velocity,
                'error_physics': error_physics
            })
    
    # Calculate statistics
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    results_table = []
    
    for horizon in [24, 48, 72]:
        results = results_by_horizon[horizon]
        
        if len(results) == 0:
            continue
        
        errors_stay = [r['error_stay'] for r in results if not np.isnan(r['error_stay'])]
        errors_velocity = [r['error_velocity'] for r in results if not np.isnan(r['error_velocity'])]
        errors_physics = [r['error_physics'] for r in results if not np.isnan(r['error_physics'])]
        
        print(f"\n{horizon}h Horizon (n={len(errors_physics)} predictions):")
        print(f"  Stay at Position:    Mean={np.mean(errors_stay):.2f} km, Median={np.median(errors_stay):.2f} km")
        print(f"  Constant Velocity:   Mean={np.mean(errors_velocity):.2f} km, Median={np.median(errors_velocity):.2f} km")
        print(f"  Physics Predictor:   Mean={np.mean(errors_physics):.2f} km, Median={np.median(errors_physics):.2f} km")
        
        results_table.append({
            'horizon': horizon,
            'n': len(errors_physics),
            'stay_mean': np.mean(errors_stay),
            'stay_median': np.median(errors_stay),
            'velocity_mean': np.mean(errors_velocity),
            'velocity_median': np.median(errors_velocity),
            'physics_mean': np.mean(errors_physics),
            'physics_median': np.median(errors_physics)
        })
    
    # Save results
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    
    with open(results_dir / "physics_vs_baselines.md", 'w') as f:
        f.write("# Physics Predictor Evaluation Results\n\n")
        f.write("## Dataset\n\n")
        f.write(f"- **Ocean Current Data**: Oct 2025 - Aug 2026 (monthly, Copernicus Marine)\n")
        f.write(f"- **Iceberg Observations**: {len(df_in_range)} observations in date range\n")
        f.write(f"- **Icebergs**: {df_in_range['iceberg_id'].nunique()} unique icebergs\n")
        f.write(f"- **Test Sequences**: {len(test_sequences)} (with 24h/48h/72h ground truth)\n\n")
        
        f.write("## Error Metrics (Haversine Distance in km)\n\n")
        f.write("| Horizon | N | Model | Mean (km) | Median (km) |\n")
        f.write("|---------|---|-------|-----------|-------------|\n")
        
        for row in results_table:
            f.write(f"| {row['horizon']}h | {row['n']} | Stay at Position | {row['stay_mean']:.2f} | {row['stay_median']:.2f} |\n")
            f.write(f"| {row['horizon']}h | {row['n']} | Constant Velocity | {row['velocity_mean']:.2f} | {row['velocity_median']:.2f} |\n")
            f.write(f"| {row['horizon']}h | {row['n']} | **Physics Predictor** | **{row['physics_mean']:.2f}** | **{row['physics_median']:.2f}** |\n")
        
        f.write("\n## Notes\n\n")
        f.write("- **Physics Predictor**: Monte Carlo simulation with ocean currents, wind, and Coriolis effect\n")
        f.write("- **Baseline 1 (Stay)**: Assumes iceberg remains at starting position\n")
        f.write("- **Baseline 2 (Velocity)**: Assumes constant velocity from previous observation\n")
        f.write("- **Ground Truth**: Real iceberg positions from BYU Antarctic Tracking Database\n")
        f.write("- **Honest Reporting**: All errors calculated using haversine distance (spherical Earth)\n\n")
        
        # Determine winner
        best_24 = min(results_table[0]['stay_mean'], results_table[0]['velocity_mean'], results_table[0]['physics_mean'])
        winner_24 = ('Stay' if best_24 == results_table[0]['stay_mean'] 
                    else 'Velocity' if best_24 == results_table[0]['velocity_mean'] 
                    else 'Physics')
        
        f.write("## Interpretation\n\n")
        if winner_24 == 'Physics':
            f.write("[OK] Physics predictor outperforms both baselines at 24h horizon.\n\n")
        else:
            f.write(f"[WARNING] Physics predictor does NOT outperform baselines. Best model: {winner_24}\n\n")
        
        f.write("**Why physics might not win:**\n")
        f.write("- Monthly ocean currents (not daily) miss short-term dynamics\n")
        f.write("- Limited validation data (few icebergs in Oct 2025 - Aug 2026)\n")
        f.write("- Monte Carlo noise with small sample size\n")
        f.write("- Icebergs respond to local conditions not captured in coarse grid\n\n")
        
        f.write("**Future Improvements:**\n")
        f.write("- Daily ocean current data (not monthly)\n")
        f.write("- Wind speed/direction integration\n")
        f.write("- Iceberg size-dependent drift coefficients\n")
        f.write("- More validation data in correct time period\n")
    
    print(f"\n✅ Results saved to: results/physics_vs_baselines.md")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    evaluate_physics_predictor()
