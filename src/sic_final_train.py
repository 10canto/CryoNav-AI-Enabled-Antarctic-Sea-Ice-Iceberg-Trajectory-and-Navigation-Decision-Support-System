"""Final SIC forecast training - simplified for speed."""
import numpy as np
import netCDF4 as nc
from pathlib import Path
from datetime import datetime, timedelta
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import pickle

print("="*70)
print("SIC FORECAST TRAINING")
print("="*70)

# Load data
data_file = Path("data/sic/sic_synthetic_2018_2023.nc")
with nc.Dataset(data_file, 'r') as ds:
    sic = ds.variables['sic'][:]
    lat = ds.variables['lat'][:]
    lon = ds.variables['lon'][:]
    time = ds.variables['time'][:]
    time_units = ds.variables['time'].units

base_date = datetime(2018, 1, 1)
dates = [base_date + timedelta(days=int(t)) for t in time]

print(f"Data: {sic.shape}, {dates[0].date()} to {dates[-1].date()}")

# Create features efficiently
def make_features_targets(sic, dates, lat, lon, lead):
    """Create X, y for a given lead time."""
    T, nlat, nlon = sic.shape
    
    # Lags
    sic_lag1 = np.concatenate([np.full((1, nlat, nlon), np.nan), sic[:-1]], axis=0)
    sic_lag3 = np.concatenate([np.full((3, nlat, nlon), np.nan), sic[:-3]], axis=0)
    sic_lag7 = np.concatenate([np.full((7, nlat, nlon), np.nan), sic[:-7]], axis=0)
    
    # Target
    sic_future = np.concatenate([sic[lead:], np.full((lead, nlat, nlon), np.nan)], axis=0)
    target = sic_future - sic
    
    # Temporal
    doy = np.array([d.timetuple().tm_yday for d in dates])
    doy_sin = np.sin(2*np.pi*doy/365.25).reshape(-1,1,1)
    doy_cos = np.cos(2*np.pi*doy/365.25).reshape(-1,1,1)
    
    # Spatial
    lat_grid = np.tile(lat.reshape(1,-1,1), (1,1,nlon))
    
    # Stack
    X = np.stack([
        sic.reshape(T,-1),
        sic_lag1.reshape(T,-1),
        sic_lag3.reshape(T,-1),
        sic_lag7.reshape(T,-1),
        np.tile(doy_sin, (1,nlat,nlon)).reshape(T,-1),
        np.tile(doy_cos, (1,nlat,nlon)).reshape(T,-1),
        np.tile(lat_grid, (T,1,1)).reshape(T,-1)
    ], axis=2)
    
    y = target.reshape(T, -1)
    
    # Flatten time-space
    X = X.reshape(-1, 7)
    y = y.ravel()
    
    # Remove NaN
    valid = ~(np.isnan(X).any(axis=1) | np.isnan(y))
    return X[valid], y[valid]

# Train/test split
years = np.array([d.year for d in dates])
train_years = years <= 2021
test_years = years >= 2022

results = []
models_dir = Path("models")
models_dir.mkdir(exist_ok=True)

for lead in [1, 3, 5, 7]:
    print(f"\n--- Lead {lead} days ---")
    
    X, y = make_features_targets(sic, dates, lat, lon, lead)
    print(f"Total samples: {len(X):,}")
    
    # Split (approximate by time blocks)
    n_per_day = len(lat) * len(lon)
    n_train_days = train_years.sum()
    n_test_days = test_years.sum()
    
    # Simple split: first N days train, last M days test
    split_idx = n_train_days * n_per_day
    X_train, y_train = X[:split_idx], y[:split_idx]
    X_test, y_test = X[split_idx:], y[split_idx:]
    
    print(f"Train: {len(X_train):,}, Test: {len(X_test):,}")
    
    if len(X_test) == 0:
        print("No test samples, skipping")
        continue
    
    sic_test = X_test[:, 0]
    
    # PERSISTENCE
    y_pred_pers = np.zeros(len(y_test))
    mae_pers = mean_absolute_error(sic_test + y_test, sic_test + y_pred_pers)
    rmse_pers = np.sqrt(mean_squared_error(sic_test + y_test, sic_test + y_pred_pers))
    results.append(('Persistence', lead, mae_pers, rmse_pers))
    print(f"Persistence: MAE={mae_pers:.2f} pp")
    
    # CLIMATOLOGY (simplified: mean change in training set)
    mean_change = y_train.mean()
    y_pred_clim = np.full(len(y_test), mean_change)
    mae_clim = mean_absolute_error(sic_test + y_test, sic_test + y_pred_clim)
    rmse_clim = np.sqrt(mean_squared_error(sic_test + y_test, sic_test + y_pred_clim))
    results.append(('Climatology', lead, mae_clim, rmse_clim))
    print(f"Climatology: MAE={mae_clim:.2f} pp")
    
    # GRADIENT BOOSTING
    print("Training GBM...")
    gbm = HistGradientBoostingRegressor(
        max_iter=80,
        max_depth=5,
        learning_rate=0.1,
        random_state=42
    )
    gbm.fit(X_train, y_train)
    
    y_pred_gbm = gbm.predict(X_test)
    mae_gbm = mean_absolute_error(sic_test + y_test, sic_test + y_pred_gbm)
    rmse_gbm = np.sqrt(mean_squared_error(sic_test + y_test, sic_test + y_pred_gbm))
    results.append(('GBM', lead, mae_gbm, rmse_gbm))
    print(f"GBM: MAE={mae_gbm:.2f} pp")
    
    # Save
    model_path = models_dir / f"sic_gbm_lead{lead}.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(gbm, f)
    print(f"Saved: {model_path}")

# Save results
results_dir = Path("results")
results_dir.mkdir(exist_ok=True)

report = """# Sea Ice Concentration Forecast Evaluation

**WARNING**: Results based on SYNTHETIC data (not satellite observations)

## Test Performance (2022-2023)

| Lead | Model | MAE (pp) | RMSE (pp) |
|------|-------|----------|-----------|
"""

for model, lead, mae, rmse in results:
    report += f"| {lead}d   | {model:15s} | {mae:7.2f} | {rmse:7.2f} |\n"

report += """

## Interpretation

pp = percentage points (0-100 scale)

### Honest Assessment

"""

for lead in [1, 3, 5, 7]:
    lead_res = [(m,mae,rmse) for m,l,mae,rmse in results if l==lead]
    if not lead_res:
        continue
    best = min(lead_res, key=lambda x: x[1])
    
    if best[0] == 'Persistence':
        report += f"- **{lead}d**: Persistence wins (MAE={best[1]:.2f}pp) - SIC highly persistent\n"
    elif best[0] == 'Climatology':
        report += f"- **{lead}d**: Climatology wins (MAE={best[1]:.2f}pp)\n"
    else:
        pers_mae = next(mae for m,mae,_ in lead_res if m=='Persistence')
        improvement = (pers_mae - best[1])/pers_mae*100
        report += f"- **{lead}d**: GBM wins (MAE={best[1]:.2f}pp, {improvement:.1f}% better than persistence)\n"

report += """

## Data Source

SYNTHETIC data with realistic seasonal patterns.
NOT suitable for operational use.

## Model Details

- **Features**: SIC(t), SIC(t-1), SIC(t-3), SIC(t-7), day-of-year(sin/cos), latitude
- **Training**: 2018-2021 (4 years)
- **Test**: 2022-2023 (2 years)
- **Algorithm**: Histogram Gradient Boosting
- **Grid**: 2° resolution, 11×28 = 308 cells

## Limitations

1. SYNTHETIC DATA - not real satellite observations
2. Missing physical drivers (winds, currents, temperature)
3. Independent grid cells (no spatial convolution)
4. Coarse resolution
5. Short training period

## Requirements for Production

1. Real satellite data (NSIDC-0051, OSI SAF, AMSR2)
2. Physical drivers integration
3. Spatial model (ConvLSTM/U-Net)
4. Longer training period (10+ years)
5. Expert validation

## Conclusion

This is a PROOF-OF-CONCEPT only. Do NOT use for real navigation decisions.
"""

(results_dir / "sic_forecast_vs_baselines.md").write_text(report)
print(f"\nResults saved: results/sic_forecast_vs_baselines.md")
print("="*70)
