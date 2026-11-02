"""
Sea-ice concentration forecast interface.

Production API for forecasting sea-ice concentration.
"""

import numpy as np
import netCDF4 as nc
from pathlib import Path
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict
import pickle
import warnings
warnings.filterwarnings('ignore')


class SICForecaster:
    """Sea-ice concentration forecaster."""
    
    def __init__(self, data_dir: Path = Path("data/sic"), models_dir: Path = Path("models")):
        self.data_dir = Path(data_dir)
        self.models_dir = Path(models_dir)
        
        # Load climatology data
        self.climatology = self._load_climatology()
        
        # Load trained models (lazy loaded)
        self.models = {}
    
    def _load_climatology(self) -> Dict:
        """Load or compute climatology from historical data."""
        data_file = self.data_dir / "sic_synthetic_2018_2023.nc"
        
        if not data_file.exists():
            print(f"Warning: Data file not found: {data_file}")
            return {'mean_sic': 25.0, 'lat': np.array([-65]), 'lon': np.array([10])}
        
        with nc.Dataset(data_file, 'r') as ds:
            sic = ds.variables['sic'][:]
            lat = ds.variables['lat'][:]
            lon = ds.variables['lon'][:]
        
        # Compute mean SIC per grid cell
        mean_sic = np.nanmean(sic, axis=0)
        
        return {
            'mean_sic': mean_sic,
            'lat': lat,
            'lon': lon
        }
    
    def _load_model(self, lead_days: int):
        """Load model for specific lead time."""
        if lead_days in self.models:
            return self.models[lead_days]
        
        model_file = self.models_dir / f"sic_gbm_lead{lead_days}.pkl"
        
        if not model_file.exists():
            return None
        
        with open(model_file, 'rb') as f:
            model = pickle.load(f)
        
        self.models[lead_days] = model
        return model
    
    def forecast_sea_ice(self, date: datetime, lead_days: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, str]:
        """
        Forecast sea-ice concentration.
        
        Args:
            date: Current date
            lead_days: Forecast lead time in days (1, 3, 5, or 7)
        
        Returns:
            sic_grid: (lat, lon) SIC forecast (0-100%)
            lat: latitude array
            lon: longitude array
            method: forecasting method used ("ML", "climatology", or "persistence")
        """
        # Try ML model first
        model = self._load_model(lead_days)
        
        if model is not None:
            try:
                sic_grid = self._forecast_ml(model, date, lead_days)
                return sic_grid, self.climatology['lat'], self.climatology['lon'], "ML"
            except Exception as e:
                print(f"ML forecast failed: {e}, falling back to climatology")
        
        # Fallback to climatology
        sic_grid = self._forecast_climatology(date)
        return sic_grid, self.climatology['lat'], self.climatology['lon'], "climatology"
    
    def _forecast_ml(self, model, date: datetime, lead_days: int) -> np.ndarray:
        """Generate ML forecast."""
        # Get current SIC (or use climatology as proxy)
        current_sic = self.climatology['mean_sic'].copy()
        
        # Adjust for season
        month = date.month
        if month in [12, 1, 2]:  # Summer
            current_sic *= 0.7
        elif month in [6, 7, 8]:  # Winter
            current_sic *= 1.3
        
        current_sic = np.clip(current_sic, 0, 100)
        
        # Prepare features
        nlat, nlon = current_sic.shape
        lat_grid = np.tile(self.climatology['lat'][:, np.newaxis], (1, nlon))
        
        X = np.column_stack([
            current_sic.ravel(),
            lat_grid.ravel()
        ])
        
        # Predict
        forecast = model.predict(X)
        forecast_grid = forecast.reshape(nlat, nlon)
        forecast_grid = np.clip(forecast_grid, 0, 100)
        
        return forecast_grid
    
    def _forecast_climatology(self, date: datetime) -> np.ndarray:
        """Generate climatology forecast."""
        clim = self.climatology['mean_sic'].copy()
        
        # Adjust for season
        month = date.month
        if month in [12, 1, 2]:  # Summer
            clim *= 0.7
        elif month in [6, 7, 8]:  # Winter
            clim *= 1.3
        
        return np.clip(clim, 0, 100)


def forecast_sea_ice(date: datetime, lead_days: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    """
    Convenience function for forecasting sea-ice concentration.
    
    Args:
        date: Current date
        lead_days: Forecast lead time in days (1, 3, 5, or 7)
    
    Returns:
        sic_grid: (lat, lon) SIC forecast (0-100%)
        lat: latitude array
        lon: longitude array
        method: forecasting method used
    
    Example:
        >>> from datetime import datetime
        >>> sic, lat, lon, method = forecast_sea_ice(datetime(2024, 1, 15), lead_days=3)
        >>> print(f"Forecast shape: {sic.shape}, method: {method}")
    """
    forecaster = SICForecaster()
    return forecaster.forecast_sea_ice(date, lead_days)


def export_forecast_to_json(sic_grid: np.ndarray, lat: np.ndarray, lon: np.ndarray,
                            output_file: Path, target_resolution: float = 0.25) -> Dict:
    """
    Export SIC forecast to JSON at reduced resolution.
    
    Args:
        sic_grid: (lat, lon) SIC array
        lat, lon: coordinate arrays
        output_file: output JSON file path
        target_resolution: target grid resolution in degrees
    
    Returns:
        dict with forecast data
    """
    import json
    
    # Downsample if needed
    current_res = abs(lat[1] - lat[0]) if len(lat) > 1 else 1.0
    
    if current_res < target_resolution:
        # Downsample by averaging
        factor = int(target_resolution / current_res)
        
        nlat_new = len(lat) // factor
        nlon_new = len(lon) // factor
        
        sic_downsampled = np.zeros((nlat_new, nlon_new))
        lat_downsampled = np.zeros(nlat_new)
        lon_downsampled = np.zeros(nlon_new)
        
        for i in range(nlat_new):
            for j in range(nlon_new):
                sic_downsampled[i, j] = sic_grid[i*factor:(i+1)*factor, j*factor:(j+1)*factor].mean()
                lat_downsampled[i] = lat[i*factor:(i+1)*factor].mean()
                lon_downsampled[j] = lon[j*factor:(j+1)*factor].mean()
    else:
        sic_downsampled = sic_grid
        lat_downsampled = lat
        lon_downsampled = lon
    
    # Build output structure
    forecast_data = {
        'lat': lat_downsampled.tolist(),
        'lon': lon_downsampled.tolist(),
        'sic': sic_downsampled.tolist(),
        'units': 'percent',
        'resolution': f"{abs(lat_downsampled[1]-lat_downsampled[0]):.2f} degrees",
        'grid_shape': [len(lat_downsampled), len(lon_downsampled)]
    }
    
    # Save
    with open(output_file, 'w') as f:
        json.dump(forecast_data, f, indent=2)
    
    print(f"Exported forecast: {output_file}")
    print(f"  Grid: {len(lat_downsampled)} x {len(lon_downsampled)}")
    print(f"  Resolution: ~{abs(lat_downsampled[1]-lat_downsampled[0]):.2f}°")
    
    return forecast_data


# Test
if __name__ == "__main__":
    print("="*70)
    print("SIC FORECAST API TEST")
    print("="*70)
    
    # Test forecast
    test_date = datetime(2024, 1, 15)
    
    for lead in [1, 3, 5, 7]:
        print(f"\nForecast for {test_date.date()} + {lead} days:")
        sic, lat, lon, method = forecast_sea_ice(test_date, lead_days=lead)
        
        print(f"  Method: {method}")
        print(f"  Grid: {sic.shape}")
        print(f"  SIC range: {sic.min():.1f}% to {sic.max():.1f}%")
        print(f"  Mean SIC: {sic.mean():.1f}%")
    
    # Test export
    print(f"\nExporting sample forecast...")
    sic, lat, lon, method = forecast_sea_ice(test_date, lead_days=3)
    
    output_file = Path("results/sic_forecast_sample.json")
    export_forecast_to_json(sic, lat, lon, output_file, target_resolution=0.25)
    
    print("\n" + "="*70)
    print("✓ API tests complete")
    print("="*70)
