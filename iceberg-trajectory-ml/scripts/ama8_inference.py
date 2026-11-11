#!/usr/bin/env python3
"""
AMA-8 Inference Module
CryoNav AI - Iceberg Trajectory ML

PURPOSE:
    Simple inference function for the CryoNav backend. Takes forcing data + position
    and returns predicted 24h position with uncertainty circle.

USAGE:
    As a module:
        from ama8_inference import predict_iceberg_position
        result = predict_iceberg_position(lat=-65, lon=0, ocean_u=0.1, ...)
    
    Standalone test:
        python ama8_inference.py
    
    CLI mode:
        python ama8_inference.py --lat -65 --lon 0 --uo 0.1 --vo 0.05 --u10 -5 --v10 3 --siconc 0.3

DATA INTEGRITY:
    - NO synthetic data (enforced by model config check)
    - NO accuracy claims (only error metrics in physical units: km)
    - Validated for 24h horizon only
"""

import json
import sys
import argparse
from pathlib import Path
from math import cos, radians, sqrt

import numpy as np
import pandas as pd
import joblib


def predict_iceberg_position(
    lat: float,
    lon: float,
    ocean_u: float,      # m/s eastward
    ocean_v: float,      # m/s northward
    wind_u: float,       # m/s eastward (10m)
    wind_v: float,       # m/s northward (10m)
    siconc: float,       # 0.0 to 1.0
    ice_u: float = 0.0,  # m/s sea ice velocity eastward (default 0)
    ice_v: float = 0.0,  # m/s sea ice velocity northward (default 0)
    dt_hours: float = 24.0,
    model_dir: str = None  # defaults to iceberg-trajectory-ml/data/validation/
) -> dict:
    """
    Predict iceberg position after dt_hours.
    
    Args:
        lat: Current latitude (degrees)
        lon: Current longitude (degrees)
        ocean_u: Ocean current eastward (m/s)
        ocean_v: Ocean current northward (m/s)
        wind_u: Wind eastward at 10m (m/s)
        wind_v: Wind northward at 10m (m/s)
        siconc: Sea ice concentration (0.0 to 1.0)
        ice_u: Sea ice velocity eastward (m/s, default 0)
        ice_v: Sea ice velocity northward (m/s, default 0)
        dt_hours: Time horizon in hours (default 24)
        model_dir: Path to model files (default: auto-detect)
    
    Returns:
        dict with keys:
            predicted_lat: Predicted latitude
            predicted_lon: Predicted longitude (wrapped to -180..180)
            uncertainty_radius_km: 90th percentile error (km)
            speed_category: stationary/slow/moderate/fast
            predicted_speed_kmd: Predicted speed (km/day)
            model_version: Model name from config
            horizon_hours: Time horizon used
            warning: (optional) If extrapolated beyond 24h
    
    Raises:
        ValueError: If any input is NaN or invalid
        FileNotFoundError: If model files don't exist
    """
    
    # Validate inputs
    inputs = {
        'lat': lat, 'lon': lon, 'ocean_u': ocean_u, 'ocean_v': ocean_v,
        'wind_u': wind_u, 'wind_v': wind_v, 'siconc': siconc,
        'ice_u': ice_u, 'ice_v': ice_v, 'dt_hours': dt_hours
    }
    
    for name, value in inputs.items():
        if value is None or (isinstance(value, float) and np.isnan(value)):
            raise ValueError(f"Input '{name}' cannot be NaN or None. Got: {value}")
    
    # Resolve model directory
    if model_dir is None:
        script_dir = Path(__file__).parent
        model_dir = script_dir.parent / "data" / "validation"
    else:
        model_dir = Path(model_dir)
    
    # Load model config
    config_path = model_dir / "model_config.json"
    if not config_path.exists():
        raise FileNotFoundError(
            f"Model config not found: {config_path}\n"
            "Run AMA-8 uncertainty configuration first:\n"
            "  python iceberg-trajectory-ml/scripts/ama8_uncertainty_config.py"
        )
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Check data integrity
    if config.get('data_provenance', {}).get('synthetic', False):
        raise ValueError("ABORT: Model was trained on synthetic data")
    
    # Load model
    model_path = model_dir / config['model_file']
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model file not found: {model_path}\n"
            "Run AMA-6 training first:\n"
            "  python iceberg-trajectory-ml/scripts/ama6_train_drift_model.py"
        )
    
    model_dict = joblib.load(model_path)
    model_u = model_dict['model_u']
    model_v = model_dict['model_v']
    scaler = model_dict['scaler']
    feature_names = model_dict['feature_names']
    
    # Compute derived features
    dt_days = dt_hours / 24.0
    
    # Sea ice weight: linearly ramp from 0 at siconc=0.6 to 1 at siconc=0.9
    ice_wt = np.clip((siconc - 0.6) / 0.3, 0, 1)
    
    # Ice drift (weighted by concentration)
    ice_u_weighted = ice_u * ice_wt
    ice_v_weighted = ice_v * ice_wt
    
    # Wind forcing (approximate leeway factor ~2%)
    wind_u_weighted = wind_u * 0.02
    wind_v_weighted = wind_v * 0.02
    
    # Location (normalized to [-1, 1])
    lat_norm = (lat + 58.5) / 21.0   # [-75, -42] -> ~[-1, 1]
    lon_norm = (lon - 20.0) / 43.0   # [-23, 63] -> ~[-1, 1]
    
    # Seasonal cycle (use current month - for real-time would need actual month)
    # For simplicity, use middle of year (month=6) as default
    # Backend should pass actual month if available
    month = 6  # TODO: Backend should compute this from current date
    month_rad = month * 2 * np.pi / 12
    month_sin = np.sin(month_rad)
    month_cos = np.cos(month_rad)
    
    # Build feature dictionary with all possible features
    feature_dict = {
        'ocean_u': ocean_u,
        'ocean_v': ocean_v,
        'ice_weight': ice_wt,
        'ice_u': ice_u_weighted,
        'ice_v': ice_v_weighted,
        'wind_u': wind_u_weighted,
        'wind_v': wind_v_weighted,
        'lat_norm': lat_norm,
        'lon_norm': lon_norm,
        'month_sin': month_sin,
        'month_cos': month_cos
    }
    
    # Build feature vector in exact order from model's feature_names
    X = pd.DataFrame([[feature_dict[f] for f in feature_names]], columns=feature_names)
    
    # Apply scaler transform (CRITICAL: model was trained on scaled features)
    X_scaled = scaler.transform(X)
    
    # Predict velocity using scaled features
    u_pred = model_u.predict(X_scaled)[0]
    v_pred = model_v.predict(X_scaled)[0]
    
    # Convert to position
    dt_sec = dt_hours * 3600
    dx_m = u_pred * dt_sec
    dy_m = v_pred * dt_sec
    
    # Convert to lat/lon displacement
    dlat = dy_m / 111_000  # meters per degree latitude
    dlon = dx_m / (111_000 * cos(radians(lat)))  # meters per degree longitude
    
    predicted_lat = lat + dlat
    predicted_lon = lon + dlon
    
    # Wrap longitude to -180..180
    while predicted_lon > 180:
        predicted_lon -= 360
    while predicted_lon < -180:
        predicted_lon += 360
    
    # Compute predicted speed (km/day)
    predicted_speed_kmd = sqrt(u_pred**2 + v_pred**2) * 86.4
    
    # Determine speed category
    speed_categories = config['speed_categories_kmd']
    if predicted_speed_kmd < speed_categories['slow'][0]:
        speed_category = 'stationary'
    elif predicted_speed_kmd < speed_categories['moderate'][0]:
        speed_category = 'slow'
    elif predicted_speed_kmd < speed_categories['fast'][0]:
        speed_category = 'moderate'
    else:
        speed_category = 'fast'
    
    # Get uncertainty radius (P90)
    uncertainty_p90_km = config['uncertainty_km'][speed_category]['p90']
    
    # Scale uncertainty if extrapolating beyond 24h
    if dt_hours > 24:
        uncertainty_p90_km *= (dt_hours / 24.0)
    
    # Build result
    result = {
        'predicted_lat': float(predicted_lat),
        'predicted_lon': float(predicted_lon),
        'uncertainty_radius_km': float(uncertainty_p90_km),
        'speed_category': speed_category,
        'predicted_speed_kmd': float(predicted_speed_kmd),
        'model_version': config['model_name'],
        'horizon_hours': float(dt_hours)
    }
    
    # Add warning if extrapolated
    if dt_hours > 24:
        result['warning'] = f"Extrapolated beyond validated 24h horizon (requested {dt_hours}h)"
    
    return result


def print_result(label: str, result: dict):
    """Pretty-print a prediction result."""
    print(f"\n{label}")
    print("=" * 80)
    print(f"  Predicted position............................ {result['predicted_lat']:.4f}°, {result['predicted_lon']:.4f}°")
    print(f"  Uncertainty radius (P90)...................... {result['uncertainty_radius_km']:.2f} km")
    print(f"  Predicted speed............................... {result['predicted_speed_kmd']:.2f} km/day")
    print(f"  Speed category................................ {result['speed_category']}")
    print(f"  Horizon....................................... {result['horizon_hours']:.1f} hours")
    print(f"  Model version................................. {result['model_version']}")
    if 'warning' in result:
        print(f"  WARNING:...................................... {result['warning']}")


def run_tests():
    """Run test cases when executed as standalone script."""
    print("\n" + "=" * 80)
    print("=" + " " * 28 + "AMA-8 INFERENCE TESTS" + " " * 31 + "=")
    print("=" + " " * 20 + "CryoNav AI - Iceberg Trajectory ML" + " " * 24 + "=")
    print("=" * 80)
    
    # Test 1: Stationary iceberg
    print("\n[TEST 1] Stationary iceberg (minimal forcing)")
    result1 = predict_iceberg_position(
        lat=-65.0,
        lon=0.0,
        ocean_u=0.01,
        ocean_v=0.01,
        wind_u=1.0,
        wind_v=1.0,
        siconc=0.3,
        ice_u=0.0,
        ice_v=0.0
    )
    print_result("Test 1 Result", result1)
    
    # Test 2: Fast drift
    print("\n[TEST 2] Fast drift (strong current + moderate wind)")
    result2 = predict_iceberg_position(
        lat=-60.0,
        lon=30.0,
        ocean_u=0.3,
        ocean_v=0.1,
        wind_u=8.0,
        wind_v=-5.0,
        siconc=0.1,
        ice_u=0.0,
        ice_v=0.0
    )
    print_result("Test 2 Result", result2)
    
    # Test 3: Pack ice
    print("\n[TEST 3] Pack ice (high siconc, weak current, strong wind)")
    result3 = predict_iceberg_position(
        lat=-70.0,
        lon=-10.0,
        ocean_u=0.05,
        ocean_v=-0.02,
        wind_u=12.0,
        wind_v=8.0,
        siconc=0.9,
        ice_u=0.1,
        ice_v=0.05
    )
    print_result("Test 3 Result", result3)
    
    # Test 4: Extrapolation warning (48h)
    print("\n[TEST 4] 48-hour forecast (extrapolation warning)")
    result4 = predict_iceberg_position(
        lat=-65.0,
        lon=0.0,
        ocean_u=0.2,
        ocean_v=0.1,
        wind_u=5.0,
        wind_v=5.0,
        siconc=0.5,
        dt_hours=48.0
    )
    print_result("Test 4 Result", result4)
    
    print("\n" + "=" * 80)
    print("[OK] All tests completed successfully")
    print("=" * 80 + "\n")


def main():
    """Main entry point for CLI mode."""
    parser = argparse.ArgumentParser(
        description="Predict iceberg position using CryoNav drift model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run built-in tests
  python ama8_inference.py
  
  # Single prediction (JSON output)
  python ama8_inference.py --lat -65 --lon 0 --uo 0.1 --vo 0.05 --u10 -5 --v10 3 --siconc 0.3
  
  # 48-hour forecast
  python ama8_inference.py --lat -60 --lon 30 --uo 0.2 --vo 0.1 --u10 8 --v10 -5 --siconc 0.1 --dt 48
"""
    )
    
    parser.add_argument('--lat', type=float, help='Current latitude (degrees)')
    parser.add_argument('--lon', type=float, help='Current longitude (degrees)')
    parser.add_argument('--uo', type=float, help='Ocean current eastward (m/s)')
    parser.add_argument('--vo', type=float, help='Ocean current northward (m/s)')
    parser.add_argument('--u10', type=float, help='Wind eastward at 10m (m/s)')
    parser.add_argument('--v10', type=float, help='Wind northward at 10m (m/s)')
    parser.add_argument('--siconc', type=float, help='Sea ice concentration (0-1)')
    parser.add_argument('--usi', type=float, default=0.0, help='Sea ice velocity eastward (m/s, default 0)')
    parser.add_argument('--vsi', type=float, default=0.0, help='Sea ice velocity northward (m/s, default 0)')
    parser.add_argument('--dt', type=float, default=24.0, help='Time horizon (hours, default 24)')
    parser.add_argument('--model-dir', type=str, help='Path to model files (optional)')
    
    args = parser.parse_args()
    
    # If no args provided, run tests
    if args.lat is None:
        run_tests()
        return
    
    # Validate required args
    required = ['lat', 'lon', 'uo', 'vo', 'u10', 'v10', 'siconc']
    missing = [arg for arg in required if getattr(args, arg) is None]
    if missing:
        parser.error(f"Missing required arguments: {', '.join(missing)}")
    
    # Run prediction
    try:
        result = predict_iceberg_position(
            lat=args.lat,
            lon=args.lon,
            ocean_u=args.uo,
            ocean_v=args.vo,
            wind_u=args.u10,
            wind_v=args.v10,
            siconc=args.siconc,
            ice_u=args.usi,
            ice_v=args.vsi,
            dt_hours=args.dt,
            model_dir=args.model_dir
        )
        
        # Output as JSON for backend parsing
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
