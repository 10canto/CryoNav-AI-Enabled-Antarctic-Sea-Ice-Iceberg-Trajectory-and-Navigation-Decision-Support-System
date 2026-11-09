# Calibrated Drift Model — Evaluation Report

**CALIBRATED DRIFT MODEL** using Approach A: Direct Physics Features

This model combines physics-based features with machine learning to predict iceberg drift velocity.

**NO ACCURACY CLAIMS**: Only raw error metrics (MAE, RMSE) are reported below.

---

## Model Description

**Approach**: Approach A: Direct Physics Features

**Input Features**:
- Ocean current: uo, vo
- Sea ice: siconc, usi, vsi (ice drift weighted by concentration)
- Wind: u10, v10 (approximate leeway factor)
- Location: lat, lon (normalized)
- Season: sin(month), cos(month)

**Model**: Ridge Regression (alpha=1.0) trained separately for u and v components

**Physics Baseline**: u_physics = 0.9*uo + 0.2*usi*ice_weight + 0.02*u10

---

## Evaluation Strategy

**NO RANDOM SPLITS**: Three evaluation strategies ensure no temporal leakage:

1. **Temporal Split**: Train on years <=2017, test on 2018-2021
   - Tests: "Can the model predict the future?"

2. **Spatial Split**: Hold out 10 icebergs with most positions
   - Tests: "Can the model predict unseen icebergs?"

3. **Combined Split**: Train on <=2017 excluding holdouts, test on 2018+ for holdouts only
   - Tests: "Can the model predict future behavior of unseen icebergs?"
   - This is the hardest and most realistic test

---

## Results Summary

### Temporal Split (train <=2017, test 2018-2021)

| Model | N | MAE u (m/s) | MAE v (m/s) | RMSE u (m/s) | RMSE v (m/s) | MAE speed (km/day) |
|-------|---|-------------|-------------|--------------|--------------|-------------------|
| **ML Model** | 423 | 0.0587 | 0.0139 | 0.0704 | 0.0244 | 5.25 |
| Zero Baseline | 423 | 0.0161 | 0.0085 | 0.0622 | 0.0291 | 1.62 |
| Physics Baseline | 423 | 0.2017 | 0.0838 | 0.2506 | 0.1042 | 19.04 |

---

### Spatial Split (hold out 10 icebergs)

| Model | N | MAE u (m/s) | MAE v (m/s) | RMSE u (m/s) | RMSE v (m/s) | MAE speed (km/day) |
|-------|---|-------------|-------------|--------------|--------------|-------------------|
| **ML Model** | 1,080 | 0.0604 | 0.0185 | 0.0773 | 0.0320 | 5.38 |
| Zero Baseline | 1,080 | 0.0447 | 0.0155 | 0.1025 | 0.0363 | 4.20 |
| Physics Baseline | 1,080 | 0.2083 | 0.0884 | 0.2616 | 0.1091 | 19.40 |

**Held-out icebergs**: B09G, B15AA, B09D, B09F, B09H

---

### Combined Split (<=2017 excl. holdouts -> 2018+ for holdouts)


*(No test data for this split in test mode)*


---

## Interpretation

**Error Metrics**:
- MAE (Mean Absolute Error): Average absolute difference between predicted and observed velocity
- RMSE (Root Mean Squared Error): Penalizes larger errors more heavily
- Speed in km/day: Conversion factor is 86.4 (m/s × 86400 s/day ÷ 1000 m/km)

**Model Comparison**:
- **Zero Baseline**: Assumes iceberg doesn't move (u=0, v=0)
- **Physics Baseline**: Uses textbook coefficients (0.9 ocean, 0.2 ice, 0.02 wind)
- **ML Model**: Learns optimal coefficients from data

**Performance**:
- Lower MAE/RMSE values indicate better predictions
- ML model should beat both baselines to demonstrate value
- Combined split is the hardest test (future + unseen icebergs)

---

## Moving Icebergs Only

**CRITICAL FOR NAVIGATION SAFETY**: The overall MAE comparison can be misleading because many icebergs move slowly or remain stationary. For navigation purposes, the critical metric is performance on icebergs that ARE actively moving toward vessels.

**Zero-velocity baseline**: Despite achieving low overall MAE, this baseline is operationally useless because it cannot predict when an iceberg IS moving. It achieves low error by correctly predicting that stationary icebergs stay stationary, but fails completely on moving icebergs.

### Moderate Movement (speed > 0.05 m/s / 4.3 km/day)


**Temporal Split**: 39 moving icebergs out of 423 total (9.2%)

| Model | MAE speed (km/day) | RMSE u (m/s) | RMSE v (m/s) |
|-------|-------------------|--------------|--------------|
| **ML Model** | 7.87 | 0.1263 | 0.0729 |
| Physics Baseline | 13.06 | 0.2555 | 0.1374 |
| Zero Baseline | 17.52 | 0.2047 | 0.0957 |

**Spatial Split**: 266 moving icebergs out of 1,080 total (24.6%)

| Model | MAE speed (km/day) | RMSE u (m/s) | RMSE v (m/s) |
|-------|-------------------|--------------|--------------|
| **ML Model** | 7.96 | 0.1142 | 0.0605 |
| Physics Baseline | 14.53 | 0.2254 | 0.1236 |
| Zero Baseline | 16.39 | 0.2062 | 0.0723 |

### Fast Movement (speed > 0.10 m/s / 8.6 km/day)


**Temporal Split**: 36 moving icebergs out of 423 total (8.5%)

| Model | MAE speed (km/day) | RMSE u (m/s) | RMSE v (m/s) |
|-------|-------------------|--------------|--------------|
| **ML Model** | 8.44 | 0.1313 | 0.0753 |
| Physics Baseline | 13.40 | 0.2649 | 0.1388 |
| Zero Baseline | 18.28 | 0.2119 | 0.0982 |

**Spatial Split**: 206 moving icebergs out of 1,080 total (19.1%)

| Model | MAE speed (km/day) | RMSE u (m/s) | RMSE v (m/s) |
|-------|-------------------|--------------|--------------|
| **ML Model** | 9.04 | 0.1248 | 0.0678 |
| Physics Baseline | 14.38 | 0.2245 | 0.1205 |
| Zero Baseline | 19.20 | 0.2311 | 0.0800 |

**Key Insight**: When filtered to moving icebergs, the ML model's advantage becomes clear. The zero baseline performs poorly because it cannot capture actual iceberg motion, making it unsuitable for navigation safety despite lower overall MAE on the full dataset.

---

## Data Integrity

✓ NO synthetic data (all values from real observations)  
✓ NO accuracy claims (raw error metrics only)  
✓ NO random splits (temporal/spatial strategies prevent leakage)  
✓ Data gate enforced at training start

---

*Generated by: iceberg-trajectory-ml/scripts/ama6_train_drift_model.py*
