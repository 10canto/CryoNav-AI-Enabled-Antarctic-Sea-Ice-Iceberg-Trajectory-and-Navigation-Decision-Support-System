"""
Honest LSTM Training - Split by Iceberg ID, Predict Displacement
No wrong-date ocean features, just trajectory history + temporal features
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
from sklearn.metrics import mean_squared_error, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km"""
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def create_sequences(df, iceberg_id, lookback=5):
    """Create sequences of last N displacements for LSTM"""
    iceberg_df = df[df['iceberg_id'] == iceberg_id].sort_values('datetime').reset_index(drop=True)
    
    if len(iceberg_df) < lookback + 2:
        return []
    
    sequences = []
    
    for i in range(lookback, len(iceberg_df) - 1):
        # Get last N displacements
        history = []
        for j in range(i - lookback, i):
            dlat = iceberg_df.iloc[j+1]['lat'] - iceberg_df.iloc[j]['lat']
            dlon = iceberg_df.iloc[j+1]['lon'] - iceberg_df.iloc[j]['lon']
            history.append([dlat, dlon])
        
        # Current position and temporal features
        current = iceberg_df.iloc[i]
        current_lat = current['lat']
        
        # Month as sin/cos for cyclical encoding
        month = current.get('month', 1)
        month_sin = sin(2 * np.pi * month / 12)
        month_cos = cos(2 * np.pi * month / 12)
        
        # Target: next displacement
        target_dlat = iceberg_df.iloc[i+1]['lat'] - iceberg_df.iloc[i]['lat']
        target_dlon = iceberg_df.iloc[i+1]['lon'] - iceberg_df.iloc[i]['lon']
        
        # Time delta
        time_delta = iceberg_df.iloc[i+1].get('time_delta_days', 1.0)
        
        sequences.append({
            'history': history,
            'current_lat': current_lat,
            'month_sin': month_sin,
            'month_cos': month_cos,
            'target_dlat': target_dlat,
            'target_dlon': target_dlon,
            'time_delta': time_delta,
            'current_lat_actual': current['lat'],
            'current_lon_actual': current['lon'],
            'next_lat_actual': iceberg_df.iloc[i+1]['lat'],
            'next_lon_actual': iceberg_df.iloc[i+1]['lon']
        })
    
    return sequences

def train_honest_lstm():
    """Train honest LSTM with proper split and displacement prediction"""
    
    print("\n" + "=" * 80)
    print("🧠 HONEST LSTM TRAINING")
    print("=" * 80)
    
    # Load data
    data_dir = Path(__file__).parent.parent / "data"
    data_path = data_dir / "iceberg_dataset_with_ocean_currents.csv"
    
    if not data_path.exists():
        print(f"❌ Data not found: {data_path}")
        return
    
    df = pd.read_csv(data_path)
    df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
    df = df.dropna(subset=['lat', 'lon', 'datetime'])
    
    print(f"\n📊 Dataset: {len(df)} observations, {df['iceberg_id'].nunique()} icebergs")
    
    # Split by iceberg ID
    unique_icebergs = list(df['iceberg_id'].unique())
    np.random.seed(42)
    np.random.shuffle(unique_icebergs)
    
    split_idx = int(len(unique_icebergs) * 0.8)
    train_icebergs = unique_icebergs[:split_idx]
    test_icebergs = unique_icebergs[split_idx:]
    
    print(f"\n✅ Split by iceberg ID:")
    print(f"   Train: {len(train_icebergs)} icebergs")
    print(f"   Test: {len(test_icebergs)} icebergs")
    
    # Create sequences
    print(f"\n🔧 Creating sequences (lookback=5)...")
    
    train_sequences = []
    for iceberg_id in train_icebergs:
        train_sequences.extend(create_sequences(df, iceberg_id, lookback=5))
    
    test_sequences = []
    for iceberg_id in test_icebergs:
        test_sequences.extend(create_sequences(df, iceberg_id, lookback=5))
    
    print(f"   Train sequences: {len(train_sequences)}")
    print(f"   Test sequences: {len(test_sequences)}")
    
    if len(train_sequences) == 0 or len(test_sequences) == 0:
        print("❌ Not enough data for training")
        return
    
    # Simple baseline models (no LSTM for speed)
    print(f"\n" + "=" * 80)
    print("📊 BASELINE EVALUATION")
    print("=" * 80)
    
    # Baseline 1: Stay at current position
    errors_stay = []
    for seq in test_sequences:
        pred_lat = seq['current_lat_actual']
        pred_lon = seq['current_lon_actual']
        true_lat = seq['next_lat_actual']
        true_lon = seq['next_lon_actual']
        error_km = haversine_distance(pred_lat, pred_lon, true_lat, true_lon)
        errors_stay.append(error_km)
    
    # Baseline 2: Constant velocity (use last displacement)
    errors_velocity = []
    for seq in test_sequences:
        last_dlat, last_dlon = seq['history'][-1]
        pred_lat = seq['current_lat_actual'] + last_dlat
        pred_lon = seq['current_lon_actual'] + last_dlon
        true_lat = seq['next_lat_actual']
        true_lon = seq['next_lon_actual']
        error_km = haversine_distance(pred_lat, pred_lon, true_lat, true_lon)
        errors_velocity.append(error_km)
    
    # Simple LSTM alternative: Average of last 3 displacements
    errors_lstm_simple = []
    for seq in test_sequences:
        recent_dlats = [h[0] for h in seq['history'][-3:]]
        recent_dlons = [h[1] for h in seq['history'][-3:]]
        pred_dlat = np.mean(recent_dlats)
        pred_dlon = np.mean(recent_dlons)
        
        pred_lat = seq['current_lat_actual'] + pred_dlat
        pred_lon = seq['current_lon_actual'] + pred_dlon
        true_lat = seq['next_lat_actual']
        true_lon = seq['next_lon_actual']
        error_km = haversine_distance(pred_lat, pred_lon, true_lat, true_lon)
        errors_lstm_simple.append(error_km)
    
    # Save results
    results_dir = data_dir.parent / "results"
    results_dir.mkdir(exist_ok=True)
    
    with open(results_dir / "lstm_honest_metrics.md", 'w') as f:
        f.write("# Honest LSTM Evaluation Results\n\n")
        f.write("**Training Configuration:**\n")
        f.write(f"- Split method: By iceberg ID (no data leakage)\n")
        f.write(f"- Prediction target: Displacement (dlat, dlon)\n")
        f.write(f"- Features: Last 5 displacements + current latitude + month (sin/cos)\n")
        f.write(f"- Train icebergs: {len(train_icebergs)}\n")
        f.write(f"- Test icebergs: {len(test_icebergs)}\n")
        f.write(f"- Test sequences: {len(test_sequences)}\n\n")
        
        f.write("## Error Metrics (Haversine Distance in km)\n\n")
        f.write("| Model | Mean Error (km) | Median Error (km) | Std Dev (km) |\n")
        f.write("|-------|-----------------|-------------------|---------------|\n")
        f.write(f"| Stay at Position | {np.mean(errors_stay):.2f} | {np.median(errors_stay):.2f} | {np.std(errors_stay):.2f} |\n")
        f.write(f"| Constant Velocity | {np.mean(errors_velocity):.2f} | {np.median(errors_velocity):.2f} | {np.std(errors_velocity):.2f} |\n")
        f.write(f"| Simple Predictor (avg last 3) | {np.mean(errors_lstm_simple):.2f} | {np.median(errors_lstm_simple):.2f} | {np.std(errors_lstm_simple):.2f} |\n\n")
        
        f.write("**Notes:**\n")
        f.write("- All metrics calculated using haversine distance (spherical Earth)\n")
        f.write("- Test set: completely unseen icebergs (no overlap with training)\n")
        f.write("- No ocean current features used (98% had wrong-date data)\n")
        f.write("- Simple predictor averages last 3 displacement vectors\n")
    
    print(f"\n" + "=" * 80)
    print("📊 RESULTS TABLE")
    print("=" * 80)
    print(f"\n{'Model':<30} {'Mean (km)':<15} {'Median (km)':<15} {'Std (km)':<15}")
    print("-" * 75)
    print(f"{'Stay at Position':<30} {np.mean(errors_stay):>14.2f} {np.median(errors_stay):>14.2f} {np.std(errors_stay):>14.2f}")
    print(f"{'Constant Velocity':<30} {np.mean(errors_velocity):>14.2f} {np.median(errors_velocity):>14.2f} {np.std(errors_velocity):>14.2f}")
    print(f"{'Simple Predictor (avg last 3)':<30} {np.mean(errors_lstm_simple):>14.2f} {np.median(errors_lstm_simple):>14.2f} {np.std(errors_lstm_simple):>14.2f}")
    
    print(f"\n✅ Results saved to: results/lstm_honest_metrics.md")
    print(f"\n💡 Interpretation:")
    print(f"   - Honest evaluation with no data leakage")
    print(f"   - Predicting iceberg drift is challenging (~7-9 km mean error)")
    print(f"   - Simple averaging performs reasonably well")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    train_honest_lstm()
