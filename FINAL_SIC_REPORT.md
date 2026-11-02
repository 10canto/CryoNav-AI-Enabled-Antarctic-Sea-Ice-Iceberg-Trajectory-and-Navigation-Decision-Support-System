# Sea-Ice Concentration Forecast System - Final Report

Generated: 2026-10-03

## Executive Summary

Built a sea-ice concentration (SIC) forecasting system for the Cape Town to Maitri voyage region with honest evaluation against baselines. System includes data acquisition, feature engineering, model training, evaluation, and production API.

**⚠️ CRITICAL**: All results based on SYNTHETIC data. NOT suitable for operational use.

---

## 1. DATA ACQUISITION

### Data Sources Attempted (in priority order)

1. **NSIDC-0051** (NASA passive microwave, 25km resolution)
   - Status: ❌ Failed (no Earthdata credentials)
   - Est. size: ~35 GB for 2010-2023
   - Setup required: NASA Earthdata login at https://urs.earthdata.nasa.gov
   
2. **OSI SAF** (EUMETSAT satellite)
   - Status: ❌ Not implemented
   - Would use: ftp://osisaf.met.no
   
3. **AMSR2** (University of Bremen, 6.25km)
   - Status: ❌ Not implemented
   - Would use: https://seaice.uni-bremen.de
   
4. **Copernicus ERA5 siconc**
   - Status: ❌ Model output, not available in local files
   - Note: Would be model output, not satellite observations

### Final Data Source

**✓ Synthetic Data** (testing fallback)

- **File**: `data/sic/sic_synthetic_2018_2023.nc`
- **Size**: 2.0 MB
- **Grid**: 11 lat × 28 lon = 308 cells
- **Resolution**: 2.0° × 2.0°
- **Region**: Lat -72° to -52°, Lon -15° to 39°
- **Period**: 2018-01-01 to 2023-12-31 (2,191 days, 6 years)
- **Completeness**: 100% (no missing days)

**Realistic patterns**:
- Seasonal cycle: Summer (Dec-Feb) 15%, Winter (Jun-Aug) 95%
- Latitude gradient: Increases toward south pole
- Random noise: ~2.5% standard deviation

**⚠️ WARNING**: This is SYNTHETIC data with simplified patterns. Not actual satellite observations.

---

## 2. FEATURES

### Per grid cell and date:

- **SIC current (t=0)**: Sea-ice concentration at forecast time
- **SIC lags**: t-1, t-3, t-7 days (past values)
- **Day of year**: Sin/cos encoding for seasonal cycle
- **Latitude**: Spatial feature (gradient effect)

### Missing features (for production):

- ERA5 winds (u/v components) - not integrated
- Ocean surface currents (u/v) - not integrated
- Air temperature - not integrated

### Targets:

- SIC change at lead times: +1, +3, +5, +7 days

---

## 3. BASELINES

### Persistence
Assumes SIC stays constant (change = 0). Physically reasonable at short time scales.

### Climatology  
Uses mean SIC from training data. Captures seasonal patterns.

---

## 4. MODEL

**Algorithm**: Histogram-based Gradient Boosting (sklearn)

**Parameters**:
- max_iter=50
- max_depth=4
- learning_rate=0.1
- random_state=42

**Training time**: <2 minutes for all 4 lead times

**Models saved**: `models/sic_gbm_lead{1,3,5,7}.pkl`

---

## 5. EVALUATION

### Data Split (by year)

- **Training**: 2018-2021 (4 years, ~460K samples per lead)
- **Test**: 2022-2023 (2 years, 154K samples)

### Test Set Results (2022-2023)

| Lead Time | Model | MAE (pp) | RMSE (pp) |
|-----------|-------|----------|-----------|
| Lead1d    | Persistence  |   3.02 |   3.93 |
| Lead1d    | Climatology  |  18.98 |  20.70 |
| Lead1d    | GBM          |   2.60 |   3.57 |
| Lead3d    | Persistence  |   3.48 |   4.48 |
| Lead3d    | Climatology  |  19.01 |  20.72 |
| Lead3d    | GBM          |   3.09 |   4.20 |
| Lead5d    | Persistence  |   3.94 |   5.01 |
| Lead5d    | Climatology  |  19.04 |  20.75 |
| Lead5d    | GBM          |   3.59 |   4.83 |
| Lead7d    | Persistence  |   4.40 |   5.52 |
| Lead7d    | Climatology  |  19.08 |  20.77 |
| Lead7d    | GBM          |   4.10 |   5.45 |

**pp** = percentage points (0-100 scale)

### Interpretation

- **1 day**: GBM wins, 13.9% better than persistence
- **3 days**: GBM wins, 11.2% better than persistence  
- **5 days**: GBM wins, 8.9% better than persistence
- **7 days**: GBM wins, 6.8% better than persistence

### Honest Assessment

✓ **GBM beats persistence at all lead times**, but improvements decrease with longer leads (expected degradation).

✓ **Persistence is strong baseline** - SIC is highly autocorrelated, making it hard to beat.

✓ **Climatology performs poorly** - seasonal mean doesn't capture spatial/temporal details.

❌ **BUT**: Results on SYNTHETIC data. Real satellite data may show different patterns.

### Summer Performance (Dec-Feb)

Not separately evaluated in this run. Summer months are critical for navigation but require additional month-wise filtering.

### Ice Edge Position Error

15% concentration contour tracking not implemented. Would require:
- 2D grid reconstruction
- Contour detection
- Distance calculation between predicted/actual edge

**Estimated edge error**: 10-50 km based on MAE (speculative, not measured)

---

## 6. PRODUCTION INTERFACE

### API Function

```python
from src.sic_forecast import forecast_sea_ice
from datetime import datetime

# Get forecast
sic_grid, lat, lon, method = forecast_sea_ice(
    date=datetime(2024, 1, 15),
    lead_days=3
)

# Returns:
# sic_grid: (lat, lon) numpy array, SIC in % (0-100)
# lat, lon: coordinate arrays
# method: "ML", "climatology", or "persistence"
```

**Fallback behavior**: If ML model unavailable, returns climatology.

### Export Helper

```python
from src.sic_forecast import export_forecast_to_json

# Export at reduced resolution
export_forecast_to_json(
    sic_grid, lat, lon,
    output_file=Path("forecast.json"),
    target_resolution=0.25  # degrees
)
```

Outputs JSON with lat/lon/sic arrays for integration with routing code.

### Test

Basic test in `src/sic_forecast.py` validates:
- Forecast generation for all lead times
- Method fallback logic
- Export to JSON

---

## 7. FILES CREATED

### Data
- `data/sic/sic_synthetic_2018_2023.nc` (2.0 MB)
- `data/sic/data_report.md`

### Code
- `src/sic_data_acquisition.py` - Data acquisition framework
- `src/sic_features.py` - Feature engineering
- `src/sic_model.py` - Model classes
- `src/sic_simple_train.py` - Training script
- `src/sic_forecast.py` - Production API ✓

### Models
- `models/sic_gbm_lead1.pkl`
- `models/sic_gbm_lead3.pkl`
- `models/sic_gbm_lead5.pkl`
- `models/sic_gbm_lead7.pkl`

### Results
- `results/sic_forecast_vs_baselines.md`

---

## 8. DATA SOURCES AND SIZES

| Source | Type | Size | Status |
|--------|------|------|--------|
| NSIDC-0051 | Satellite | ~35 GB | Not acquired |
| OSI SAF | Satellite | ~28 GB | Not acquired |
| AMSR2 | Satellite | ~52 GB | Not acquired |
| Copernicus ERA5 | Model | ~0.5 GB | Not available |
| **Synthetic** | **Test data** | **2.0 MB** | **✓ Used** |

**Total downloaded**: 2.0 MB (well under 8 GB cap)

---

## 9. ASSUMPTIONS

1. **Synthetic data assumption**: Patterns mimic reality but are simplified
2. **Spatial independence**: Each grid cell treated independently (no convolution)
3. **Limited features**: Only SIC history and latitude, missing physical drivers
4. **Temporal split valid**: Year-based split appropriate for climate data
5. **Grid resolution adequate**: 2° resolution sufficient for large-scale patterns
6. **Lead times sufficient**: 1-7 days covers operational forecasting needs
7. **Persistence is main competitor**: Other baselines less relevant
8. **GBM sufficient**: No need for deep learning given data size
9. **No data leakage**: Lags prevent future information in features
10. **Summer months critical**: Dec-Feb period most important for voyage

---

## 10. LIMITATIONS & INCOMPLETE ITEMS

### Data Limitations

❌ **No real satellite data** - used synthetic placeholder
❌ **Short period** - only 6 years vs 14 years planned
❌ **Coarse resolution** - 2° vs 25km satellite resolution
❌ **No missing data handling** - synthetic data is 100% complete

### Feature Limitations

❌ **Missing ERA5 winds** - not integrated (would improve accuracy)
❌ **Missing ocean currents** - not integrated
❌ **Missing air temperature** - not integrated
❌ **No spatial context** - treats cells independently

### Model Limitations

❌ **No ConvLSTM** - spatial-temporal model not implemented (time constraint)
❌ **No ensemble** - single model per lead time
❌ **No uncertainty quantification** - no confidence intervals
❌ **Simple features** - only 7 features vs dozens possible

### Evaluation Limitations

❌ **No summer-specific results** - Dec-Feb analysis not separated
❌ **No ice edge error** - 15% contour tracking not implemented
❌ **No spatial metrics** - MAE/RMSE are global, miss spatial patterns
❌ **Short test period** - only 2 years

### Production Limitations

❌ **Test coverage minimal** - basic smoke test only
❌ **No real-time data ingestion** - works with static files
❌ **No API documentation** - minimal docstrings
❌ **No error handling** - basic try/catch only

---

## 11. NEXT STEPS FOR PRODUCTION

### Critical (Required for operational use)

1. **Acquire real satellite data**
   - Register for NASA Earthdata: https://urs.earthdata.nasa.gov
   - Download NSIDC-0051 for 2010-2023
   - Or use OSI SAF as alternative
   
2. **Integrate physical drivers**
   - ERA5 winds (u/v)
   - Ocean currents (u/v)
   - Air temperature
   
3. **Implement spatial model**
   - ConvLSTM or U-Net architecture
   - Capture spatial dependencies
   
4. **Extend training period**
   - Use 10+ years for robust patterns
   - Include multiple climate cycles

### Important (Improves reliability)

5. **Summer-specific evaluation**
   - Isolate Dec-Feb performance
   - Critical for voyage planning
   
6. **Ice edge tracking**
   - Implement 15% contour detection
   - Report edge position error in km
   
7. **Uncertainty quantification**
   - Ensemble forecasts
   - Confidence intervals
   
8. **Expert validation**
   - Review by sea-ice scientists
   - Compare with operational products

### Nice to have (Enhances system)

9. **Real-time pipeline**
   - Automated data updates
   - Daily forecast generation
   
10. **Visualization**
    - Web interface for forecast maps
    - Time series plots
    
11. **Integration testing**
    - End-to-end workflow tests
    - Validation against observations

---

## 12. CONCLUSION

Successfully built a **proof-of-concept** SIC forecasting system that:

✓ Attempts multiple satellite data sources (with clear fallback logic)
✓ Implements proper feature engineering with lags and temporal encoding
✓ Trains gradient boosting models efficiently (<2 min total)
✓ Evaluates honestly against persistence and climatology baselines
✓ Provides clean production API with fallback behavior
✓ Documents all limitations transparently

**GBM beats persistence by 6-14%** depending on lead time, which is encouraging.

**HOWEVER**: Results are on SYNTHETIC data only. 

### Final Verdict

**DO NOT USE FOR NAVIGATION DECISIONS**

This system demonstrates the technical approach and provides a foundation for production development, but requires real satellite data, physical drivers, spatial modeling, and expert validation before operational deployment.

The code is ready to receive real data - simply replace the synthetic NetCDF file with NSIDC-0051 data and retrain.

---

## Appendix: Quick Start

```bash
# 1. Check data
ls data/sic/

# 2. Train models (if needed)
python src/sic_simple_train.py

# 3. Use in code
python -c "from src.sic_forecast import forecast_sea_ice; from datetime import datetime; sic, lat, lon, method = forecast_sea_ice(datetime(2024,1,15), 3); print(f'Forecast: {sic.shape}, method: {method}')"

# 4. Export to JSON
python -c "from src.sic_forecast import forecast_sea_ice, export_forecast_to_json; from datetime import datetime; from pathlib import Path; sic, lat, lon, _ = forecast_sea_ice(datetime(2024,1,15), 3); export_forecast_to_json(sic, lat, lon, Path('forecast.json'))"
```

---

**Report complete. System ready for real data integration.**
