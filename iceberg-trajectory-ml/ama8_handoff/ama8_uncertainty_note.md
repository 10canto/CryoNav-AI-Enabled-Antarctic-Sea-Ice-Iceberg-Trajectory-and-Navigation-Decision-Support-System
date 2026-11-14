# AMA-8 Uncertainty Configuration Note

**Model:** CryoNav Drift Model v1
**Validated horizon:** 24 hours only
**Runtime category variable:** `predicted_speed_kmd`

## Evaluation basis

- Icebergs: 11
- 24-hour prediction pairs: 1,777
- Period: 2018–2021
- Leakage: none (approved 11 unseen iceberg test set)
- Overall ML P75 error: **9.681 km**
- Error metric: Haversine distance between actual and ML-predicted next-day positions

## Runtime speed-band P75 radii

| Speed band | Predicted speed (km/day) | Samples | P75 error / radius (km) |
|---|---:|---:|---:|
| Stationary | [0, 2) | 30 | **12.64** |
| Slow | [2, 5) | 267 | **10.59** |
| Moderate | [5, 10) | 1138 | **9.14** |
| Fast | [10, infinity) | 342 | **10.77** |

## Method

- Runtime bins match `ama8_inference.py` / `speed_categories_kmd`: stationary below 2; slow below 5; moderate below 10; fast at 10 or above.
- The accepted AMA-7 pair CSV contains the start and ML-predicted coordinates, but not the returned `predicted_speed_kmd` field.
- To avoid classifying with actual observed speed, predicted speed was reconstructed from the saved ML-predicted coordinates using the exact inverse of the AMA-8 inference module's 24-hour local coordinate conversion (111,000 metres per degree and the cosine-of-latitude longitude adjustment).
- P75 is calculated separately for the ML Haversine errors in each predicted-speed category using NumPy's default linear percentile method.
- Band sample counts are included in the JSON for auditability.

## AMA-7 model comparison

| Model | Mean (km) | Median (km) | P75 (km) |
|---|---:|---:|---:|
| ML (AMA-8 inference) | 7.391 | 6.262 | 9.681 |
| Physics (AMA-6 baseline) | 21.439 | 18.548 | 28.595 |
| Zero velocity | 9.689 | 8.697 | 13.493 |

## Required limitations

- ML inference is validated for 24 hours only. Do not present 48-hour or 72-hour ML predictions as validated.
- Any 48-hour or 72-hour physics results must be labelled **“Physics extrapolation, unvalidated beyond 24h.”**
- The 1,777 prediction pairs are repeated temporal pairs across 11 iceberg tracks, not 1,777 independent icebergs.
- These P75 values are calculated on the AMA-7 evaluation set itself; they are empirical test-set summaries, not an independent calibration-set coverage guarantee.
- **LSTM remains experimental:** it did not outperform the baselines and is not the production model.

## Data-quality disclosure

- Four selected evaluation rows had marginal `siconc` values slightly above 1.0 (D28: 3; D30B: 1).
- Maximum observed value: 1.0000152583234012; all four were within the 0.0001 tolerance and clipped only in the in-memory AMA-7 evaluation DataFrame.
- The original `training_table.csv` was not modified.

## Backend handoff

- JSON schema follows Kumar's requested `model_version`, `horizon_hours`, `overall_p75_km`, `speed_bands`, and `evaluation` structure.
- Runtime selector must use `predicted_speed_kmd`.
- This is a separate handoff artifact. It does not overwrite `data/validation/model_config.json` or modify `drift_model.pkl`.
