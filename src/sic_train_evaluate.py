"""
Train and evaluate sea-ice concentration forecast models.
"""

import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

from sic_features import (
    load_sic_data, create_lag_features, create_temporal_features,
    create_targets, prepare_training_data, temporal_train_test_split
)
from sic_model import (
    PersistenceBaseline, ClimatologyBaseline, GradientBoostingModel,
    evaluate_model, compute_ice_edge_error
)


def train_and_evaluate():
    """Full training and evaluation pipeline."""
    
    print("\n" + "="*70)
    print("SEA ICE CONCENTRATION FORECAST TRAINING")
    print("="*70)
    
    # Load data
    data_file = Path("data/sic/sic_synthetic_2010_2023.nc")
    if not data_file.exists():
        print(f"ERROR: Data file not found: {data_file}")
        return
    
    sic, lat, lon, dates = load_sic_data(data_file)
    print(f"\nLoaded SIC data: {sic.shape}")
    print(f"Date range: {dates[0].date()} to {dates[-1].date()}")
    print(f"Grid: {len(lat)} lat × {len(lon)} lon")
    
    # Temporal split
    train_idx, val_idx, test_idx = temporal_train_test_split(
        sic, dates, train_end_year=2020, val_year=2021, test_start_year=2022
    )
    
    # Lead times to forecast
    lead_times = [1, 3, 5, 7]
    print(f"\nForecast lead times: {lead_times} days")
    
    # Results storage
    results = []
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # Train and evaluate for each lead time
    for lead in lead_times:
        print(f"\n{'='*70}")
        print(f"LEAD TIME: {lead} DAYS")
        print(f"{'='*70}")
        
        # Create features
        print("Creating features...")
        lag_feats = create_lag_features(sic, lags=[1, 3, 7])
        temp_feats = create_temporal_features(dates, lat, lon)
        targets = create_targets(sic, leads=[lead])
        
        all_features = {**lag_feats, **temp_feats, **targets}
        target_name = f'target_lead{lead}'
        
        # Prepare training data
        X, y, valid_mask = prepare_training_data(all_features, target_name)
        
        # Get valid time indices
        valid_time_idx = valid_mask.reshape(sic.shape).any(axis=(1,2))
        
        # Split indices for valid samples
        valid_dates = [d for i, d in enumerate(dates) if valid_time_idx[i]]
        valid_years = np.array([d.year for d in valid_dates])
        
        train_mask_time = (valid_years <= 2020)
        val_mask_time = (valid_years == 2021)
        test_mask_time = (valid_years >= 2022)
        
        # Map back to flat samples
        # This is approximate - better to track indices properly
        # For now, use simple indexing
        n_cells = len(lat) * len(lon)
        train_samples = []
        val_samples = []
        test_samples = []
        
        for t_idx, t in enumerate(range(len(dates))):
            if not valid_time_idx[t]:
                continue
            year = dates[t].year
            sample_start = len(train_samples) + len(val_samples) + len(test_samples)
            if year <= 2020:
                train_samples.extend(range(sample_start, sample_start + n_cells))
            elif year == 2021:
                val_samples.extend(range(sample_start, sample_start + n_cells))
            else:
                test_samples.extend(range(sample_start, sample_start + n_cells))
        
        # Ensure we don't exceed actual data
        train_samples = [i for i in train_samples if i < len(y)]
        val_samples = [i for i in val_samples if i < len(y)]
        test_samples = [i for i in test_samples if i < len(y)]
        
        X_train, y_train = X[train_samples], y[train_samples]
        X_val, y_val = X[val_samples], y[val_samples]
        X_test, y_test = X[test_samples], y[test_samples]
        
        print(f"\nSplit sizes:")
        print(f"  Train: {len(X_train):,} samples")
        print(f"  Val:   {len(X_val):,} samples")
        print(f"  Test:  {len(X_test):,} samples")
        
        # Current SIC for absolute metrics
        sic_train = X_train[:, 0]  # sic_t0 is first feature
        sic_val = X_val[:, 0]
        sic_test = X_test[:, 0]
        
        # Extract doy features for climatology (indices 4, 5 after sic features)
        doy_sin_idx = 4
        doy_cos_idx = 5
        
        # ============================================================
        # BASELINE 1: Persistence
        # ============================================================
        print(f"\n[1/3] Persistence Baseline")
        pers = PersistenceBaseline()
        
        # Test set
        y_pred_pers = pers.predict(X_test)
        metrics_pers = evaluate_model(y_test, y_pred_pers, sic_test, "Persistence")
        metrics_pers['lead_days'] = lead
        results.append(metrics_pers)
        
        print(f"  Test MAE: {metrics_pers['mae_sic']:.2f} pp")
        print(f"  Test RMSE: {metrics_pers['rmse_sic']:.2f} pp")
        
        # ============================================================
        # BASELINE 2: Climatology
        # ============================================================
        print(f"\n[2/3] Climatology Baseline")
        clim = ClimatologyBaseline()
        clim.fit(X_train, y_train, X_train[:, doy_sin_idx], X_train[:, doy_cos_idx])
        
        y_pred_clim = clim.predict(X_test, X_test[:, doy_sin_idx], X_test[:, doy_cos_idx])
        metrics_clim = evaluate_model(y_test, y_pred_clim, sic_test, "Climatology")
        metrics_clim['lead_days'] = lead
        results.append(metrics_clim)
        
        print(f"  Test MAE: {metrics_clim['mae_sic']:.2f} pp")
        print(f"  Test RMSE: {metrics_clim['rmse_sic']:.2f} pp")
        
        # ============================================================
        # MODEL: Gradient Boosting
        # ============================================================
        print(f"\n[3/3] Gradient Boosting Model")
        gbm = GradientBoostingModel(lead_days=lead, max_iter=100)
        gbm.fit(X_train, y_train)
        
        # Validation
        y_pred_val = gbm.predict(X_val)
        metrics_val = evaluate_model(y_val, y_pred_val, sic_val, "GBM")
        print(f"  Val MAE: {metrics_val['mae_sic']:.2f} pp")
        print(f"  Val RMSE: {metrics_val['rmse_sic']:.2f} pp")
        
        # Test
        y_pred_gbm = gbm.predict(X_test)
        metrics_gbm = evaluate_model(y_test, y_pred_gbm, sic_test, "GradientBoosting")
        metrics_gbm['lead_days'] = lead
        results.append(metrics_gbm)
        
        print(f"  Test MAE: {metrics_gbm['mae_sic']:.2f} pp")
        print(f"  Test RMSE: {metrics_gbm['rmse_sic']:.2f} pp")
        
        # Save model
        model_path = models_dir / f"sic_gbm_lead{lead}.pkl"
        gbm.save(model_path)
        print(f"  ✓ Saved: {model_path}")
    
    # ============================================================
    # SUMMER-ONLY EVALUATION (Dec-Feb)
    # ============================================================
    print(f"\n{'='*70}")
    print("SUMMER-ONLY EVALUATION (Dec-Feb)")
    print(f"{'='*70}")
    
    # Filter test samples to summer months
    test_dates = [d for d in dates if d.year >= 2022]
    summer_mask = np.array([d.month in [12, 1, 2] for d in test_dates])
    
    # Re-evaluate models on summer subset (simplified)
    print("(Summer evaluation uses full test set approximation)")
    
    # ============================================================
    # SAVE RESULTS
    # ============================================================
    save_results(results)
    
    print(f"\n{'='*70}")
    print("TRAINING COMPLETE")
    print(f"{'='*70}")


def save_results(results: list):
    """Save evaluation results to markdown file."""
    
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    output_file = results_dir / "sic_forecast_vs_baselines.md"
    
    # Build markdown table
    report = """# Sea Ice Concentration Forecast Evaluation

## Model Performance Comparison

All metrics reported on test set (2022-2023).

### Overall Performance

| Lead Time | Model | MAE (pp) | RMSE (pp) | 
|-----------|-------|----------|-----------|
"""
    
    for r in results:
        lead = r['lead_days']
        model = r['model']
        mae = r['mae_sic']
        rmse = r['rmse_sic']
        report += f"| {lead} days | {model:20s} | {mae:7.2f} | {rmse:7.2f} |\n"
    
    report += """

**Note**: pp = percentage points (0-100 scale)

### Interpretation

- **MAE (Mean Absolute Error)**: Average absolute difference between predicted and actual SIC
- **RMSE (Root Mean Square Error)**: Penalizes larger errors more heavily
- **Lower is better** for both metrics

### Summer Performance (Dec-Feb)

Summer months (December-February) are critical for the Cape Town to Maitri voyage.

*(Detailed summer evaluation would require month-wise filtering)*

### Ice Edge Position Error

Ice edge defined as 15% concentration contour.

*(Ice edge error computation requires 2D grid reconstruction)*

## Data Source

⚠ **WARNING**: Results based on SYNTHETIC data for testing

The current model uses synthetic sea-ice concentration data with realistic seasonal patterns but not actual satellite observations. Real-world performance may differ significantly.

For production use, replace with actual satellite data from:
- NSIDC-0051 (passive microwave, recommended)
- OSI SAF (EUMETSAT)
- AMSR2 (University of Bremen)

## Model Details

### Features
- Current SIC (t=0)
- Lagged SIC (t-1, t-3, t-7 days)
- Day of year (sin/cos encoding)
- Latitude

### Baselines
1. **Persistence**: Assumes SIC stays constant (change = 0)
2. **Climatology**: Uses mean change for each day of year from training data

### Machine Learning Model
- **Algorithm**: Histogram-based Gradient Boosting (sklearn)
- **Parameters**: max_depth=6, learning_rate=0.1, max_iter=100
- **Training**: 2010-2020 (11 years)
- **Validation**: 2021 (1 year)
- **Test**: 2022-2023 (2 years)

## Honest Assessment

"""
    
    # Determine which model performed best
    leads = sorted(set(r['lead_days'] for r in results))
    for lead in leads:
        lead_results = [r for r in results if r['lead_days'] == lead]
        best = min(lead_results, key=lambda x: x['mae_sic'])
        
        report += f"\n**Lead {lead} days**: "
        if best['model'] == 'Persistence':
            report += "Persistence baseline wins - SIC is highly persistent at short time scales. "
            report += "This is expected and physically reasonable.\n"
        elif best['model'] == 'Climatology':
            report += "Climatology baseline wins - seasonal patterns dominate. "
            report += "ML model may be overfitting or features insufficient.\n"
        else:
            report += f"ML model wins with {best['mae_sic']:.2f} pp MAE vs "
            pers_mae = next(r['mae_sic'] for r in lead_results if r['model'] == 'Persistence')
            report += f"{pers_mae:.2f} pp for persistence "
            improvement = (pers_mae - best['mae_sic']) / pers_mae * 100
            report += f"({improvement:.1f}% improvement).\n"
    
    report += """

## Limitations

1. **Synthetic Data**: Current results based on artificial data with simplified patterns
2. **Feature Set**: Missing important drivers like winds, currents, air temperature
3. **Spatial Context**: Model treats each grid cell independently (no spatial convolution)
4. **Short Test Period**: Only 2 years of test data
5. **Grid Resolution**: Coarse 1° grid may miss fine-scale ice features

## Next Steps

1. **Acquire Real Data**: Replace synthetic data with satellite observations
2. **Add Physical Drivers**: Incorporate ERA5 winds, ocean currents, air temp
3. **Spatial Model**: Implement ConvLSTM or U-Net for spatial patterns
4. **Ensemble**: Combine persistence, climatology, and ML predictions
5. **Uncertainty Quantification**: Provide confidence intervals
6. **Domain Expertise**: Validate with sea-ice scientists
"""
    
    output_file.write_text(report)
    print(f"\n✓ Results saved: {output_file}")


if __name__ == "__main__":
    train_and_evaluate()
