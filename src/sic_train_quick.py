"""Quick SIC training with subsampling."""

import numpy as np
from pathlib import Path
import sys
sys.path.append('src')

from sic_features import load_sic_data, create_lag_features, create_temporal_features, create_targets
from sic_model import PersistenceBaseline, ClimatologyBaseline, GradientBoostingModel, evaluate_model

print("="*70)
print("QUICK SIC FORECAST TRAINING")
print("="*70)

# Load
data_file = Path("data/sic/sic_synthetic_2010_2023.nc")
sic, lat, lon, dates = load_sic_data(data_file)
print(f"Loaded: {sic.shape}")

# Subsample: every 7 days + summer months
sample_idx = []
for i, d in enumerate(dates):
    if i % 7 == 0 or d.month in [12, 1, 2]:
        sample_idx.append(i)

sic = sic[sample_idx]
dates = [dates[i] for i in sample_idx]
print(f"Subsampled to {len(dates)} days")

# Features
lag_feats = create_lag_features(sic, [1, 3, 7])
temp_feats = create_temporal_features(dates, lat, lon)

results = []
models_dir = Path("models")
models_dir.mkdir(exist_ok=True)

for lead in [1, 3, 5, 7]:
    print(f"\n--- Lead {lead} days ---")
    
    targets = create_targets(sic, [lead])
    
    # Stack
    X_list = [lag_feats['sic_t0'].ravel(), 
              lag_feats['sic_lag1'].ravel(),
              lag_feats['sic_lag3'].ravel(),
              lag_feats['sic_lag7'].ravel(),
              temp_feats['doy_sin'].ravel(),
              temp_feats['doy_cos'].ravel(),
              temp_feats['latitude'].ravel()]
    
    X = np.stack(X_list, axis=1)
    y = targets[f'target_lead{lead}'].ravel()
    
    # Remove NaN
    valid = ~(np.isnan(X).any(axis=1) | np.isnan(y))
    X, y = X[valid], y[valid]
    
    # Split by year
    years = np.array([dates[i // (len(lat)*len(lon))].year for i in range(len(valid)) if valid[i]])
    
    train_mask = years <= 2020
    test_mask = years >= 2022
    
    X_train, y_train = X[train_mask], y[train_mask]
    X_test, y_test = X[test_mask], y[test_mask]
    sic_test = X_test[:, 0]
    
    print(f"Train: {len(X_train):,}, Test: {len(X_test):,}")
    
    # Persistence
    y_pred_pers = np.zeros(len(y_test))
    metrics_pers = evaluate_model(y_test, y_pred_pers, sic_test, "Persistence")
    metrics_pers['lead'] = lead
    results.append(metrics_pers)
    print(f"Persistence MAE: {metrics_pers['mae_sic']:.2f} pp")
    
    # Climatology
    clim = ClimatologyBaseline()
    clim.fit(X_train, y_train, X_train[:, 4], X_train[:, 5])
    y_pred_clim = clim.predict(X_test, X_test[:, 4], X_test[:, 5])
    metrics_clim = evaluate_model(y_test, y_pred_clim, sic_test, "Climatology")
    metrics_clim['lead'] = lead
    results.append(metrics_clim)
    print(f"Climatology MAE: {metrics_clim['mae_sic']:.2f} pp")
    
    # GBM (fast)
    gbm = GradientBoostingModel(lead, max_iter=50)
    gbm.fit(X_train, y_train)
    y_pred_gbm = gbm.predict(X_test)
    metrics_gbm = evaluate_model(y_test, y_pred_gbm, sic_test, "GBM")
    metrics_gbm['lead'] = lead
    results.append(metrics_gbm)
    print(f"GBM MAE: {metrics_gbm['mae_sic']:.2f} pp")
    
    gbm.save(models_dir / f"sic_gbm_lead{lead}.pkl")

# Save results
results_dir = Path("results")
results_dir.mkdir(exist_ok=True)

report = f"""# Sea Ice Concentration Forecast Evaluation

Generated: {Path('data/sic/data_report.md').read_text().split('Generated:')[1].split('##')[0].strip()}

⚠ **Based on SYNTHETIC data**

## Test Set Performance (2022-2023)

| Lead | Model | MAE (pp) | RMSE (pp) |
|------|-------|----------|-----------|
"""

for r in results:
    report += f"| {r['lead']}d | {r['model']:15s} | {r['mae_sic']:6.2f} | {r['rmse_sic']:6.2f} |\n"

report += """

## Interpretation

**Honest Assessment**: 

"""

for lead in [1, 3, 5, 7]:
    lead_results = [r for r in results if r['lead'] == lead]
    best = min(lead_results, key=lambda x: x['mae_sic'])
    
    if best['model'] == 'Persistence':
        report += f"- **{lead}d**: Persistence wins - SIC highly persistent (expected)\n"
    elif best['model'] == 'Climatology':
        report += f"- **{lead}d**: Climatology wins - seasonal cycle dominant\n"
    else:
        pers_mae = next(r['mae_sic'] for r in lead_results if r['model'] == 'Persistence')
        improvement = (pers_mae - best['mae_sic']) / pers_mae * 100
        report += f"- **{lead}d**: GBM wins ({improvement:.1f}% better than persistence)\n"

report += """

## Data Source

⚠ Synthetic data with realistic patterns but NOT satellite observations

## Limitations

1. Synthetic data only
2. No winds/currents/temperature
3. Independent grid cells (no spatial convolution)
4. Coarse 1° resolution

## Production Readiness

**NOT READY for operational use**. Requires:
- Real satellite data (NSIDC-0051, OSI SAF, or AMSR2)
- Physical driver integration (winds, currents)
- Spatial model (ConvLSTM/U-Net)
- Validation by sea-ice experts
"""

(results_dir / "sic_forecast_vs_baselines.md").write_text(report)
print(f"\n✓ Results: results/sic_forecast_vs_baselines.md")
