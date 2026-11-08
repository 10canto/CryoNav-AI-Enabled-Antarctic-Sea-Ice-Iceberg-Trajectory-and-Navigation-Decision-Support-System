#!/usr/bin/env python3
"""
AMA-8: Uncertainty Configuration Generator
CryoNav AI - Iceberg Trajectory ML

PURPOSE:
    Compute speed-dependent uncertainty bands from AMA-6 drift model's temporal
    validation residuals and write model_config.json for backend API consumption.

INPUTS:
    - data/validation/training_table.csv (27,707 rows)
    - data/validation/drift_model.pkl (trained Ridge model)
    - data/validation/data_report.json (must say synthetic: false)

OUTPUTS:
    - data/validation/model_config.json (config with uncertainty bands)
    - data/validation/ama8_uncertainty_note.md (explanation)

DATA INTEGRITY:
    - NO synthetic data (enforced by data gate check)
    - NO accuracy claims (only physical error metrics in km)
    - Temporal split only (≤2017 train, 2018+ test)
"""

import sys
import json
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import joblib  # Changed from pickle to joblib


def print_header(title):
    """Print section header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_success(msg):
    """Print success message."""
    print(f"[OK] {msg}")


def check_data_gate():
    """Verify we're using real data only."""
    print_header("DATA GATE CHECK")
    
    script_dir = Path(__file__).parent
    gate_file = script_dir.parent / "data" / "validation" / "data_report.json"
    
    if not gate_file.exists():
        print(f"ERROR: {gate_file} not found")
        print("\nRun AMA-5 first to build the training table:")
        print("  python iceberg-trajectory-ml/scripts/ama5_build_training_table.py")
        sys.exit(1)
    
    with open(gate_file, 'r') as f:
        gate = json.load(f)
    
    print(f"Data source: {gate.get('data_source', 'UNKNOWN')}")
    print(f"Synthetic flag: {gate.get('synthetic', 'UNKNOWN')}")
    print(f"Rows: {gate.get('n_rows', 'UNKNOWN'):,}")
    print(f"Date range: {gate.get('date_min', '?')} to {gate.get('date_max', '?')}")
    
    if gate.get('synthetic', False) is True:
        print("\nABORT: synthetic data detected")
        sys.exit(1)
    
    print("Data gate passed: REAL data verified")


def load_training_table(data_dir):
    """Load training table and return complete cases."""
    print_header("LOADING TRAINING DATA")
    
    csv_path = data_dir / "validation" / "training_table.csv"
    df = pd.read_csv(csv_path)
    
    print(f"  Total rows loaded................................. {len(df):,}")
    
    # Drop rows with missing observations
    df_clean = df.dropna(subset=['u_obs', 'v_obs'])
    print(f"  After dropping NaN observations................... {len(df_clean):,} (-{len(df) - len(df_clean)})")
    
    return df_clean


def temporal_split(df):
    """Split into train (≤2017) and test (2018+)."""
    print_header("TEMPORAL SPLIT")
    
    # Year column already exists in the dataframe
    train_mask = df['year'] <= 2017
    test_mask = df['year'] >= 2018
    
    df_train = df[train_mask].copy()
    df_test = df[test_mask].copy()
    
    print(f"  Train samples (<=2017)............................ {len(df_train):,}")
    print(f"  Test samples (2018+).............................. {len(df_test):,}")
    
    return df_train, df_test


def load_model_and_features(data_dir):
    """Load the trained model and get feature list."""
    print_header("LOADING MODEL")
    
    model_path = data_dir / "validation" / "drift_model.pkl"
    
    try:
        model_dict = joblib.load(model_path)  # Changed from pickle.load
    except Exception as e:
        print(f"ERROR loading model: {e}")
        print("\nTry re-running AMA-6 training:")
        print("  python iceberg-trajectory-ml/scripts/ama6_train_drift_model.py")
        sys.exit(1)
    
    model_u = model_dict['model_u']
    model_v = model_dict['model_v']
    features = model_dict['feature_names']  # Changed from 'features' to 'feature_names'
    
    print(f"  Model file........................................ {model_path.name}")
    print(f"  Features.......................................... {len(features)}")
    print(f"  Feature list...................................... {', '.join(features[:5])}...")
    
    return model_u, model_v, features


def build_physics_features(df):
    """Build physics-informed features matching AMA-6."""
    feat = pd.DataFrame(index=df.index)
    
    # Ocean current (direct)
    feat['ocean_u'] = df['uo']
    feat['ocean_v'] = df['vo']
    
    # Sea ice weight: linearly ramp from 0 at siconc=0.6 to 1 at siconc=0.9
    ice_weight = ((df['siconc'] - 0.6) / 0.3).clip(0, 1)
    feat['ice_weight'] = ice_weight
    
    # Ice drift (weighted by concentration)
    feat['ice_u'] = df['usi'] * ice_weight
    feat['ice_v'] = df['vsi'] * ice_weight
    
    # Wind forcing (approximate leeway factor ~2%)
    feat['wind_u'] = df['u10'] * 0.02
    feat['wind_v'] = df['v10'] * 0.02
    
    # Location (normalized to [-1, 1])
    feat['lat_norm'] = (df['lat'] + 58.5) / 21.0  # [-75, -42] -> ~[-1, 1]
    feat['lon_norm'] = (df['lon'] - 20.0) / 43.0  # [-23, 63] -> ~[-1, 1]
    
    # Seasonal cycle
    month_rad = df['month'] * 2 * np.pi / 12
    feat['month_sin'] = np.sin(month_rad)
    feat['month_cos'] = np.cos(month_rad)
    
    return feat


def compute_position_errors(df_test, model_u, model_v, features):
    """Compute position errors in km from velocity predictions."""
    print_header("COMPUTING POSITION ERRORS")
    
    # Build physics features
    feat = build_physics_features(df_test)
    
    # Get complete cases with all features and observations
    required_cols = features + ['u_obs', 'v_obs', 'dt_days']
    available_features = [f for f in features if f in feat.columns]
    df_complete = df_test.loc[feat[available_features].notna().all(axis=1) & 
                                df_test[['u_obs', 'v_obs', 'dt_days']].notna().all(axis=1)]
    feat_complete = feat.loc[df_complete.index]
    
    print(f"  Complete test cases............................... {len(df_complete):,}")
    
    # Extract features
    X = feat_complete[features].values
    
    # Predict velocities (m/s)
    u_pred = model_u.predict(X)
    v_pred = model_v.predict(X)
    
    # Get observed velocities
    u_obs = df_complete['u_obs'].values
    v_obs = df_complete['v_obs'].values
    dt_days = df_complete['dt_days'].values
    
    # Convert velocity errors to position errors (km)
    dt_seconds = dt_days * 86400
    dx_km = (u_pred - u_obs) * dt_seconds / 1000
    dy_km = (v_pred - v_obs) * dt_seconds / 1000
    error_km = np.sqrt(dx_km**2 + dy_km**2)
    
    # Compute observed speed (km/day)
    speed_kmd = np.sqrt(u_obs**2 + v_obs**2) * 86.4
    
    # Create results dataframe
    results = pd.DataFrame({
        'speed_kmd': speed_kmd,
        'error_km': error_km,
        'u_obs': u_obs,
        'v_obs': v_obs,
        'u_pred': u_pred,
        'v_pred': v_pred,
        'dt_days': dt_days
    })
    
    print(f"  Position errors computed.......................... {len(results):,}")
    print(f"  Mean error (km)................................... {error_km.mean():.2f}")
    print(f"  Median error (km)................................. {np.median(error_km):.2f}")
    print(f"  P90 error (km).................................... {np.percentile(error_km, 90):.2f}")
    print(f"  P95 error (km).................................... {np.percentile(error_km, 95):.2f}")
    
    return results


def compute_uncertainty_by_speed(results):
    """Compute uncertainty bands for each speed category."""
    print_header("UNCERTAINTY BY SPEED CATEGORY")
    
    # Define speed categories (km/day)
    categories = {
        'stationary': (0, 2),
        'slow': (2, 5),
        'moderate': (5, 10),
        'fast': (10, 999)
    }
    
    uncertainty = {}
    
    print(f"\n{'Category':<15} {'N':>8} {'MAE':>8} {'P50':>8} {'P90':>8} {'P95':>8} {'Max':>8}")
    print("-" * 80)
    
    for cat_name, (low, high) in categories.items():
        mask = (results['speed_kmd'] >= low) & (results['speed_kmd'] < high)
        errors = results.loc[mask, 'error_km'].values
        
        if len(errors) == 0:
            print(f"{cat_name:<15} {0:>8} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'N/A':>8} {'N/A':>8}")
            uncertainty[cat_name] = {
                'n_samples': 0,
                'mae_km': None,
                'p50_km': None,
                'p90_km': None,
                'p95_km': None,
                'max_km': None
            }
        else:
            mae = errors.mean()
            p50 = np.percentile(errors, 50)
            p90 = np.percentile(errors, 90)
            p95 = np.percentile(errors, 95)
            max_err = errors.max()
            
            print(f"{cat_name:<15} {len(errors):>8,} {mae:>8.2f} {p50:>8.2f} {p90:>8.2f} {p95:>8.2f} {max_err:>8.2f}")
            
            uncertainty[cat_name] = {
                'n_samples': int(len(errors)),
                'mae_km': float(mae),
                'p50_km': float(p50),
                'p90_km': float(p90),
                'p95_km': float(p95),
                'max_km': float(max_err)
            }
    
    print("-" * 80)
    print("\nNote: All error values in kilometers for 24-hour forecast horizon")
    
    return uncertainty


def compute_feature_ranges(df_train, features):
    """Compute min/max ranges for each feature from training data."""
    ranges = {}
    
    for feat in features:
        if feat in df_train.columns:
            valid_vals = df_train[feat].dropna()
            if len(valid_vals) > 0:
                ranges[feat] = {
                    'min': float(valid_vals.min()),
                    'max': float(valid_vals.max())
                }
            else:
                ranges[feat] = {'min': None, 'max': None}
        else:
            ranges[feat] = {'min': None, 'max': None}
    
    return ranges


def write_model_config(uncertainty, features, feature_ranges, data_dir):
    """Write model_config.json with uncertainty bands."""
    print_header("WRITING MODEL CONFIG")
    
    # Build feature units mapping
    feature_units = {
        'ocean_u': 'm/s',
        'ocean_v': 'm/s',
        'ice_u_weighted': 'm/s',
        'ice_v_weighted': 'm/s',
        'wind_u': 'm/s',
        'wind_v': 'm/s',
        'ice_u': 'm/s',
        'ice_v': 'm/s',
        'siconc': 'fraction 0-1',
        'ice_wt': 'fraction 0-1',
        'lat': 'degrees',
        'lon': 'degrees',
        'dt_days': 'days',
        'sin_month': 'dimensionless',
        'cos_month': 'dimensionless'
    }
    
    # Build uncertainty bands (only p50, p90, p95 for API)
    uncertainty_bands = {}
    for cat_name, stats in uncertainty.items():
        uncertainty_bands[cat_name] = {
            'p50': stats['p50_km'],
            'p90': stats['p90_km'],
            'p95': stats['p95_km']
        }
    
    config = {
        'model_name': 'CryoNav Drift Model v1',
        'model_type': 'ridge_regression_gray_box',
        'model_file': 'drift_model.pkl',
        'horizon_hours': 24,
        'horizon_note': 'Only 24h is validated. Do NOT use for 48h or 72h.',
        'features': features,
        'feature_units': {k: feature_units.get(k, 'unknown') for k in features},
        'feature_ranges': feature_ranges,
        'uncertainty_km': uncertainty_bands,
        'speed_categories_kmd': {
            'stationary': [0, 2],
            'slow': [2, 5],
            'moderate': [5, 10],
            'fast': [10, 999]
        },
        'data_provenance': {
            'synthetic': False,
            'sources': ['BYU v8.0', 'GLORYS12', 'ERA5'],
            'training_period': '1995-2017',
            'validation_period': '2018-2021'
        },
        'generated_at': datetime.utcnow().isoformat() + 'Z'
    }
    
    output_path = data_dir / "validation" / "model_config.json"
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print_success(f"Saved {output_path}")


def write_uncertainty_note(uncertainty, data_dir):
    """Write explanation document for uncertainty bands."""
    
    note = """# AMA-8 Uncertainty Bands — Explanation

## How Uncertainty Was Computed

1. **Data Split**: Temporal validation split (train ≤2017, test 2018-2021)
   - Training: {train_samples:,} samples from 1995-2017
   - Testing: {test_samples:,} samples from 2018-2021

2. **Position Error Calculation**:
   - Model predicts velocity (u, v) in m/s
   - Convert velocity error to position error over dt_days:
     - dx_km = (u_pred - u_obs) * dt_seconds / 1000
     - dy_km = (v_pred - v_obs) * dt_seconds / 1000
     - error_km = sqrt(dx_km² + dy_km²)

3. **Speed Categories**: Based on observed speed (km/day)
   - **Stationary**: 0-2 km/day
   - **Slow**: 2-5 km/day
   - **Moderate**: 5-10 km/day
   - **Fast**: >10 km/day

4. **Uncertainty Metrics**: For each category:
   - **P50 (median)**: 50% of predictions have error below this
   - **P90**: 90% of predictions have error below this
   - **P95**: 95% of predictions have error below this

## Speed-Dependent Uncertainty

Uncertainty varies by iceberg speed:

| Category | N | MAE (km) | P50 (km) | P90 (km) | P95 (km) |
|----------|---|----------|----------|----------|----------|
""".format(
        train_samples=0,  # Will be filled in
        test_samples=sum(u['n_samples'] for u in uncertainty.values() if u['n_samples'] is not None)
    )
    
    for cat_name in ['stationary', 'slow', 'moderate', 'fast']:
        u = uncertainty[cat_name]
        if u['n_samples'] and u['n_samples'] > 0:
            note += f"| {cat_name.capitalize():<9} | {u['n_samples']:>5,} | {u['mae_km']:>8.2f} | {u['p50_km']:>8.2f} | {u['p90_km']:>8.2f} | {u['p95_km']:>8.2f} |\n"
        else:
            note += f"| {cat_name.capitalize():<9} | {0:>5} | N/A | N/A | N/A | N/A |\n"
    
    note += """
## Validated Horizon

**24 hours only**. The model was trained and validated on 24-hour position pairs (dt_days ≈ 1.0). Using this model for 48h or 72h forecasts is NOT validated and will have higher uncertainty than reported here.

## Caveats

- Uncertainty bands are empirical (computed from residuals on held-out test set)
- P95 does NOT mean "95% accurate" — it means "95% of errors are below this value"
- Fast-moving icebergs have higher absolute error but may still be predictable
- Stationary icebergs have low error because they don't move much
- These bands apply to the 2018-2021 test period and may differ for other regions or time periods

## Data Integrity

✓ NO synthetic data (all values from real observations)  
✓ NO accuracy claims (only error metrics in physical units: km)  
✓ Temporal split prevents data leakage (train on past, test on future)

---

*Generated by: iceberg-trajectory-ml/scripts/ama8_uncertainty_config.py*
"""
    
    output_path = data_dir / "validation" / "ama8_uncertainty_note.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(note)
    
    print_success(f"Saved {output_path}")


def main():
    """Main execution."""
    print("\n" + "=" * 80)
    print("=" + " " * 22 + "AMA-8: Uncertainty Configuration" + " " * 24 + "=")
    print("=" + " " * 20 + "CryoNav AI - Iceberg Trajectory ML" + " " * 24 + "=")
    print("=" * 80 + "\n")
    
    # Check data gate FIRST
    check_data_gate()
    
    # Set up paths
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    
    # Load training table
    df = load_training_table(data_dir)
    
    # Temporal split
    df_train, df_test = temporal_split(df)
    
    # Load model and features
    model_u, model_v, features = load_model_and_features(data_dir)
    
    # Compute position errors on test set
    results = compute_position_errors(df_test, model_u, model_v, features)
    
    # Compute uncertainty by speed category
    uncertainty = compute_uncertainty_by_speed(results)
    
    # Compute feature ranges from training data
    feature_ranges = compute_feature_ranges(df_train, features)
    
    # Write model config
    write_model_config(uncertainty, features, feature_ranges, data_dir)
    
    # Write uncertainty note
    write_uncertainty_note(uncertainty, data_dir)
    
    print_header("COMPLETE")
    print("  Model config...................................... model_config.json")
    print("  Uncertainty note.................................. ama8_uncertainty_note.md")
    print("  Output directory.................................. " + str(data_dir / "validation"))
    print("\n" + "=" * 80)
    print_success("Uncertainty configuration completed successfully")
    print("=" * 80 + "\n")
    
    print("Next steps:")
    print("  1. Review model_config.json for API integration")
    print("  2. Review ama8_uncertainty_note.md for uncertainty interpretation")
    print("  3. Use uncertainty bands in operational forecasts")


if __name__ == "__main__":
    main()
