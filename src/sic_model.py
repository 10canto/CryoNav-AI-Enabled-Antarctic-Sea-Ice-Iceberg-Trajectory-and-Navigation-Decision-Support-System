"""
Sea-ice concentration forecast models and baselines.
"""

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from typing import Tuple, Optional
import pickle
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


class PersistenceBaseline:
    """Persistence forecast: SIC stays the same."""
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict zero change (SIC persists)."""
        return np.zeros(X.shape[0])


class ClimatologyBaseline:
    """Climatology forecast: mean SIC change for each day of year."""
    
    def __init__(self):
        self.doy_means = {}
    
    def fit(self, X: np.ndarray, y: np.ndarray, doy_sin: np.ndarray, doy_cos: np.ndarray):
        """Learn mean change per day of year from training data."""
        # Convert sin/cos back to day of year (approximate)
        doy = np.round((np.arctan2(doy_sin, doy_cos) / (2 * np.pi) * 365.25) % 365.25).astype(int)
        
        for d in range(366):
            mask = doy == d
            if mask.sum() > 0:
                self.doy_means[d] = y[mask].mean()
            else:
                self.doy_means[d] = 0.0
        
        return self
    
    def predict(self, X: np.ndarray, doy_sin: np.ndarray, doy_cos: np.ndarray) -> np.ndarray:
        """Predict based on day of year climatology."""
        doy = np.round((np.arctan2(doy_sin, doy_cos) / (2 * np.pi) * 365.25) % 365.25).astype(int)
        
        predictions = np.array([self.doy_means.get(d, 0.0) for d in doy])
        return predictions


class GradientBoostingModel:
    """Gradient boosting model for SIC forecasting."""
    
    def __init__(self, lead_days: int, max_iter: int = 100):
        self.lead_days = lead_days
        self.model = HistGradientBoostingRegressor(
            max_iter=max_iter,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            early_stopping=True,
            n_iter_no_change=10,
            validation_fraction=0.1
        )
    
    def fit(self, X_train: np.ndarray, y_train: np.ndarray):
        """Train the model."""
        print(f"  Training gradient boosting (lead={self.lead_days} days)...")
        self.model.fit(X_train, y_train)
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict SIC change."""
        return self.model.predict(X)
    
    def save(self, path: Path):
        """Save model to file."""
        with open(path, 'wb') as f:
            pickle.dump(self, f)
    
    @staticmethod
    def load(path: Path):
        """Load model from file."""
        with open(path, 'rb') as f:
            return pickle.load(f)


def evaluate_model(y_true: np.ndarray, y_pred: np.ndarray, 
                   sic_current: np.ndarray, 
                   model_name: str = "Model") -> dict:
    """Evaluate forecast performance.
    
    Args:
        y_true: true SIC change
        y_pred: predicted SIC change
        sic_current: current SIC values
        model_name: name for reporting
    
    Returns:
        dict with metrics
    """
    # Basic metrics on change
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    
    # Convert to absolute SIC
    sic_true = sic_current + y_true
    sic_pred = np.clip(sic_current + y_pred, 0, 100)
    
    mae_sic = mean_absolute_error(sic_true, sic_pred)
    rmse_sic = np.sqrt(mean_squared_error(sic_true, sic_pred))
    
    return {
        'model': model_name,
        'mae_change': mae,
        'rmse_change': rmse,
        'mae_sic': mae_sic,
        'rmse_sic': rmse_sic
    }


def compute_ice_edge_error(sic_true: np.ndarray, sic_pred: np.ndarray, 
                           lat: np.ndarray, lon: np.ndarray,
                           threshold: float = 15.0) -> Optional[float]:
    """Compute ice edge position error in km.
    
    Args:
        sic_true, sic_pred: (lat, lon) SIC grids
        lat, lon: coordinate arrays
        threshold: concentration threshold for ice edge (%)
    
    Returns:
        mean edge position error in km, or None if edge not found
    """
    # Find edge in both
    edge_true = np.abs(sic_true - threshold) < 5
    edge_pred = np.abs(sic_pred - threshold) < 5
    
    if not edge_true.any() or not edge_pred.any():
        return None
    
    # Get edge positions
    lat_grid, lon_grid = np.meshgrid(lat, lon, indexing='ij')
    
    lat_true_edge = lat_grid[edge_true].mean()
    lat_pred_edge = lat_grid[edge_pred].mean()
    
    # Approximate distance in km (1 degree ~111 km)
    dist_km = abs(lat_true_edge - lat_pred_edge) * 111
    
    return dist_km


if __name__ == "__main__":
    # Test
    print("Testing models...")
    
    X_dummy = np.random.randn(1000, 6)
    y_dummy = np.random.randn(1000) * 5
    
    # Persistence
    pers = PersistenceBaseline()
    y_pers = pers.predict(X_dummy)
    print(f"Persistence: {y_pers.shape}, mean={y_pers.mean():.3f}")
    
    # Climatology
    clim = ClimatologyBaseline()
    doy_sin = X_dummy[:, 3]  # assume these are doy features
    doy_cos = X_dummy[:, 4]
    clim.fit(X_dummy, y_dummy, doy_sin, doy_cos)
    y_clim = clim.predict(X_dummy, doy_sin, doy_cos)
    print(f"Climatology: {y_clim.shape}, mean={y_clim.mean():.3f}")
    
    # GBM
    gbm = GradientBoostingModel(lead_days=1, max_iter=50)
    gbm.fit(X_dummy, y_dummy)
    y_gbm = gbm.predict(X_dummy)
    print(f"GBM: {y_gbm.shape}, mean={y_gbm.mean():.3f}")
    
    print("✓ Models working")
