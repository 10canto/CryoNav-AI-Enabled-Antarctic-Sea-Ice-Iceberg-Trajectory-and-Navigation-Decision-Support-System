"""
Feature engineering for sea-ice concentration forecasting.
"""

import numpy as np
import netCDF4 as nc
from pathlib import Path
from datetime import datetime, timedelta
from typing import Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


def load_sic_data(data_file: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray, list]:
    """Load SIC data from netCDF file.
    
    Returns:
        sic: (time, lat, lon) array
        lat: latitude array
        lon: longitude array
        dates: list of datetime objects
    """
    with nc.Dataset(data_file, 'r') as ds:
        sic = ds.variables['sic'][:]
        lat = ds.variables['lat'][:]
        lon = ds.variables['lon'][:]
        time = ds.variables['time'][:]
        time_units = ds.variables['time'].units
        
        # Parse dates
        if 'since' in time_units:
            base_str = time_units.split('since')[1].strip().split()[0]
            base_date = datetime.fromisoformat(base_str)
            dates = [base_date + timedelta(days=int(t)) for t in time]
        else:
            dates = [datetime(2010, 1, 1) + timedelta(days=int(t)) for t in time]
    
    return sic, lat, lon, dates


def create_lag_features(sic: np.ndarray, lags: list = [1, 3, 7]) -> dict:
    """Create lagged SIC features.
    
    Args:
        sic: (time, lat, lon) SIC array
        lags: list of lag days
    
    Returns:
        dict with lag features
    """
    features = {'sic_t0': sic}
    
    for lag in lags:
        # Shift forward (past values)
        lagged = np.full_like(sic, np.nan)
        lagged[lag:] = sic[:-lag]
        features[f'sic_lag{lag}'] = lagged
    
    return features


def create_temporal_features(dates: list, lat: np.ndarray, lon: np.ndarray) -> dict:
    """Create temporal features (day of year encoding).
    
    Args:
        dates: list of datetime objects
        lat, lon: coordinate arrays
    
    Returns:
        dict with temporal features
    """
    doy = np.array([d.timetuple().tm_yday for d in dates])
    
    # Cyclic encoding
    doy_sin = np.sin(2 * np.pi * doy / 365.25)
    doy_cos = np.cos(2 * np.pi * doy / 365.25)
    
    # Broadcast to full grid
    doy_sin_grid = np.repeat(doy_sin[:, np.newaxis, np.newaxis], len(lat), axis=1)
    doy_sin_grid = np.repeat(doy_sin_grid, len(lon), axis=2)
    
    doy_cos_grid = np.repeat(doy_cos[:, np.newaxis, np.newaxis], len(lat), axis=1)
    doy_cos_grid = np.repeat(doy_cos_grid, len(lon), axis=2)
    
    # Latitude (spatial feature)
    lat_grid = np.tile(lat[:, np.newaxis], (1, len(lon)))
    lat_grid = np.repeat(lat_grid[np.newaxis, :, :], len(dates), axis=0)
    
    return {
        'doy_sin': doy_sin_grid,
        'doy_cos': doy_cos_grid,
        'latitude': lat_grid
    }


def create_targets(sic: np.ndarray, leads: list = [1, 3, 5, 7]) -> dict:
    """Create target variables (future SIC change).
    
    Args:
        sic: (time, lat, lon) SIC array
        leads: list of forecast lead days
    
    Returns:
        dict with targets for each lead time
    """
    targets = {}
    
    for lead in leads:
        # Future SIC
        future_sic = np.full_like(sic, np.nan)
        future_sic[:-lead] = sic[lead:]
        
        # Change from current
        sic_change = future_sic - sic
        targets[f'target_lead{lead}'] = sic_change
    
    return targets


def prepare_training_data(features: dict, target_name: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Prepare flat training arrays from feature dict.
    
    Args:
        features: dict with all features and target
        target_name: name of target variable
    
    Returns:
        X: (n_samples, n_features) feature array
        y: (n_samples,) target array
        valid_mask: boolean mask of valid samples
    """
    # Extract target
    y_grid = features[target_name]
    
    # Stack all features
    feature_names = [k for k in features.keys() if k != target_name and not k.startswith('target_')]
    X_grids = [features[k] for k in feature_names]
    
    # Flatten
    X = np.stack([grid.ravel() for grid in X_grids], axis=1)
    y = y_grid.ravel()
    
    # Valid samples (no NaN in features or target)
    valid_mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
    
    X = X[valid_mask]
    y = y[valid_mask]
    
    print(f"  Features: {X.shape[1]}, Samples: {X.shape[0]:,}")
    print(f"  Feature names: {feature_names}")
    
    return X, y, valid_mask


def temporal_train_test_split(sic: np.ndarray, dates: list, 
                               train_end_year: int = 2020,
                               val_year: int = 2021,
                               test_start_year: int = 2022):
    """Split data by year.
    
    Args:
        sic, dates: data arrays
        train_end_year: last year of training (inclusive)
        val_year: validation year
        test_start_year: first test year
    
    Returns:
        train_idx, val_idx, test_idx: boolean masks
    """
    years = np.array([d.year for d in dates])
    
    train_idx = years <= train_end_year
    val_idx = years == val_year
    test_idx = years >= test_start_year
    
    n_train = train_idx.sum()
    n_val = val_idx.sum()
    n_test = test_idx.sum()
    
    print(f"Split: Train {n_train} days (≤{train_end_year}), "
          f"Val {n_val} days ({val_year}), "
          f"Test {n_test} days (≥{test_start_year})")
    
    return train_idx, val_idx, test_idx


if __name__ == "__main__":
    # Test
    data_file = Path("data/sic/sic_synthetic_2010_2023.nc")
    sic, lat, lon, dates = load_sic_data(data_file)
    
    print(f"Loaded: {sic.shape} SIC data")
    print(f"Date range: {dates[0].date()} to {dates[-1].date()}")
    
    # Create features
    lag_feats = create_lag_features(sic, lags=[1, 3, 7])
    temp_feats = create_temporal_features(dates, lat, lon)
    targets = create_targets(sic, leads=[1, 3, 5, 7])
    
    all_features = {**lag_feats, **temp_feats, **targets}
    
    print(f"\nFeatures created: {list(all_features.keys())}")
    
    # Prepare for lead=1
    X, y, mask = prepare_training_data(all_features, 'target_lead1')
    print(f"Training data ready: X {X.shape}, y {y.shape}")
