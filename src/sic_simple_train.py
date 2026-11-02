"""Simplified SIC training."""
import numpy as np
import netCDF4 as nc
import pickle
from pathlib import Path
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

Path('models').mkdir(exist_ok=True)
Path('results').mkdir(exist_ok=True)

# Load
with nc.Dataset('data/sic/sic_synthetic_2018_2023.nc', 'r') as ds:
    sic = ds.variables['sic'][:]
    lat = ds.variables['lat'][:]
    lon = ds.variables['lon'][:]

T, nlat, nlon = sic.shape
print(f'Data: {sic.shape}')

results = []

for lead in [1, 3, 5, 7]:
    print(f'\nLead {lead}d:')
    
    # Prepare data (simple: current SIC + lat)
    X_train = []
    y_train = []
    
    for t in range(0, 1500-lead):  # Train on first 1500 days
        for i in range(nlat):
            for j in range(nlon):
                if not np.isnan(sic[t,i,j]) and not np.isnan(sic[t+lead,i,j]):
                    X_train.append([sic[t,i,j], lat[i]])
                    y_train.append(sic[t+lead,i,j])
    
    X_train = np.array(X_train)
    y_train = np.array(y_train)
    
    # Test data
    X_test = []
    y_test = []
    for t in range(1500, min(2000, T-lead)):
        for i in range(nlat):
            for j in range(nlon):
                if not np.isnan(sic[t,i,j]) and not np.isnan(sic[t+lead,i,j]):
                    X_test.append([sic[t,i,j], lat[i]])
                    y_test.append(sic[t+lead,i,j])
    
    X_test = np.array(X_test)
    y_test = np.array(y_test)
    
    print(f'  Train: {len(X_train)}, Test: {len(X_test)}')
    
    # Persistence
    y_pred_pers = X_test[:, 0]  # Current SIC
    mae_pers = mean_absolute_error(y_test, y_pred_pers)
    rmse_pers = np.sqrt(mean_squared_error(y_test, y_pred_pers))
    results.append((f'Lead{lead}d', 'Persistence', mae_pers, rmse_pers))
    print(f'  Persistence: MAE={mae_pers:.2f}pp')
    
    # Climatology (mean of training)
    mean_sic = y_train.mean()
    y_pred_clim = np.full(len(y_test), mean_sic)
    mae_clim = mean_absolute_error(y_test, y_pred_clim)
    rmse_clim = np.sqrt(mean_squared_error(y_test, y_pred_clim))
    results.append((f'Lead{lead}d', 'Climatology', mae_clim, rmse_clim))
    print(f'  Climatology: MAE={mae_clim:.2f}pp')
    
    # GBM
    gbm = HistGradientBoostingRegressor(
        max_iter=50,
        max_depth=4,
        learning_rate=0.1,
        random_state=42
    )
    gbm.fit(X_train, y_train)
    
    y_pred_gbm = gbm.predict(X_test)
    mae_gbm = mean_absolute_error(y_test, y_pred_gbm)
    rmse_gbm = np.sqrt(mean_squared_error(y_test, y_pred_gbm))
    results.append((f'Lead{lead}d', 'GBM', mae_gbm, rmse_gbm))
    print(f'  GBM: MAE={mae_gbm:.2f}pp')
    
    # Save model
    with open(f'models/sic_gbm_lead{lead}.pkl', 'wb') as f:
        pickle.dump(gbm, f)

# Save results
report = """# Sea Ice Concentration Forecast Results

**WARNING: SYNTHETIC DATA - NOT FOR PRODUCTION USE**

## Test Performance

| Lead Time | Model | MAE (pp) | RMSE (pp) |
|-----------|-------|----------|-----------|
"""

for lead, model, mae_val, rmse_val in results:
    report += f"| {lead:9s} | {model:12s} | {mae_val:7.2f} | {rmse_val:7.2f} |\n"

report += """

## Data Source

SYNTHETIC sea-ice concentration data with realistic patterns.

## Honest Assessment

"""

# Analysis
for lead_num in [1, 3, 5, 7]:
    lead_str = f'Lead{lead_num}d'
    lead_results = [(m, mae_val) for l, m, mae_val, _ in results if l == lead_str]
    best = min(lead_results, key=lambda x: x[1])
    
    if best[0] == 'Persistence':
        report += f"- **{lead_num} days**: Persistence wins (expected - SIC is highly persistent)\n"
    else:
        pers_mae = next(mae_val for m, mae_val in lead_results if m == 'Persistence')
        improvement = (pers_mae - best[1]) / pers_mae * 100
        report += f"- **{lead_num} days**: {best[0]} wins, {improvement:.1f}% better than persistence\n"

report += """

## Limitations

1. **Synthetic data** - not real satellite observations
2. **Simple features** - only current SIC and latitude
3. **No physical drivers** - missing winds, currents, temperature
4. **Independent cells** - no spatial context
5. **Short period** - only 6 years of data

## Production Requirements

For real navigation use, need:
- Real satellite data (NSIDC-0051 or OSI SAF)
- Physical drivers (ERA5 winds, ocean currents)
- Spatial model (ConvLSTM/U-Net)
- 10+ years training data
- Expert validation

**DO NOT USE FOR NAVIGATION DECISIONS**
"""

Path('results/sic_forecast_vs_baselines.md').write_text(report)
print('\n' + '='*70)
print('✓ Saved: results/sic_forecast_vs_baselines.md')
print('✓ Saved: models/sic_gbm_lead*.pkl')
print('='*70)
