# AMA-7: 24-hour unseen-iceberg evaluation

**Evaluation statement:** 11 unseen icebergs, 2018-2021, no training leakage.

## Evaluation design

- Approved test icebergs: 11
- IDs: A78, B09I, B39, D21B, D27, D28, D29A, D29B, D29C, D30A, D30B
- Evaluation period: 2018-01-01 through 2021-12-31 (both pair dates within period)
- Prediction horizon: 24 hours only
- Models: AMA-8 ML inference, AMA-6 physics baseline, zero-velocity baseline
- Complete cases only; outlier-flagged pairs excluded
- Pair rule: dt_days equals one and calendar difference is exactly one day
- The three models use the same evaluation rows
- Leakage check: IDs verified against AMA-6 manifest test_only_ids
- Spatial check: no overlap with AMA-6 spatial held_out_ids

## Dataset coverage

- Evaluation pairs: 1,777
- Icebergs represented: 11
- First observation date: 2018-07-06
- Last target date: 2021-12-31

## Aggregate error metrics

Errors are great-circle Haversine distances in kilometres. P75 uses linear interpolation.

| Model | N | Mean (km) | Median (km) | P75 (km) |
|---|---:|---:|---:|---:|
| ML (AMA-8 inference) | 1777 | 7.391 | 6.262 | 9.681 |
| Physics (AMA-6 baseline) | 1777 | 21.439 | 18.548 | 28.595 |
| Zero velocity | 1777 | 9.689 | 8.697 | 13.493 |

## Per-iceberg metrics

| Iceberg | Model | N | Mean (km) | Median (km) | P75 (km) |
|---|---|---:|---:|---:|---:|
| A78 | ML (AMA-8 inference) | 124 | 6.563 | 6.492 | 7.547 |
| A78 | Physics (AMA-6 baseline) | 124 | 19.984 | 17.381 | 27.392 |
| A78 | Zero velocity | 124 | 2.501 | 1.020 | 4.239 |
| B09I | ML (AMA-8 inference) | 137 | 12.700 | 12.952 | 15.526 |
| B09I | Physics (AMA-6 baseline) | 137 | 21.225 | 18.603 | 28.655 |
| B09I | Zero velocity | 137 | 13.707 | 11.162 | 21.059 |
| B39 | ML (AMA-8 inference) | 220 | 8.452 | 6.602 | 10.561 |
| B39 | Physics (AMA-6 baseline) | 220 | 22.708 | 18.836 | 30.012 |
| B39 | Zero velocity | 220 | 11.662 | 9.853 | 14.958 |
| D21B | ML (AMA-8 inference) | 72 | 5.099 | 4.805 | 6.371 |
| D21B | Physics (AMA-6 baseline) | 72 | 18.908 | 16.063 | 25.442 |
| D21B | Zero velocity | 72 | 9.885 | 8.447 | 12.750 |
| D27 | ML (AMA-8 inference) | 204 | 10.220 | 9.618 | 13.921 |
| D27 | Physics (AMA-6 baseline) | 204 | 18.431 | 15.822 | 25.143 |
| D27 | Zero velocity | 204 | 7.542 | 7.196 | 10.859 |
| D28 | ML (AMA-8 inference) | 315 | 6.565 | 5.553 | 8.719 |
| D28 | Physics (AMA-6 baseline) | 315 | 26.756 | 23.888 | 35.336 |
| D28 | Zero velocity | 315 | 8.877 | 8.125 | 13.082 |
| D29A | ML (AMA-8 inference) | 135 | 6.538 | 5.839 | 8.670 |
| D29A | Physics (AMA-6 baseline) | 135 | 20.102 | 18.524 | 26.124 |
| D29A | Zero velocity | 135 | 11.719 | 12.520 | 15.187 |
| D29B | ML (AMA-8 inference) | 183 | 5.403 | 5.165 | 7.089 |
| D29B | Physics (AMA-6 baseline) | 183 | 20.203 | 16.502 | 26.916 |
| D29B | Zero velocity | 183 | 7.615 | 7.108 | 10.369 |
| D29C | ML (AMA-8 inference) | 136 | 5.875 | 4.652 | 7.947 |
| D29C | Physics (AMA-6 baseline) | 136 | 20.546 | 17.332 | 27.579 |
| D29C | Zero velocity | 136 | 10.910 | 9.610 | 13.361 |
| D30A | ML (AMA-8 inference) | 107 | 6.391 | 5.430 | 7.810 |
| D30A | Physics (AMA-6 baseline) | 107 | 21.145 | 18.856 | 28.629 |
| D30A | Zero velocity | 107 | 13.934 | 12.403 | 16.262 |
| D30B | ML (AMA-8 inference) | 144 | 5.874 | 4.856 | 7.230 |
| D30B | Physics (AMA-6 baseline) | 144 | 18.736 | 17.018 | 24.905 |
| D30B | Zero velocity | 144 | 10.182 | 8.298 | 14.923 |

## Method notes and limitations

- The existing trained AMA-6 model is used through the corrected AMA-8 inference function; no retraining is performed.
- Each ML inference call receives the actual observation date, so the seasonal month feature is date-specific.
- Physics velocities use the AMA-6 coefficients: u = 0.9*uo + 0.2*usi*ice_weight + 0.02*u10; v = 0.9*vo + 0.2*vsi*ice_weight + 0.02*v10; ice_weight = clip((siconc - 0.6)/0.3, 0, 1).
- Physics velocities are integrated for 24 hours using the local coordinate conversion used by the AMA-8 inference module.
- The zero-velocity baseline predicts no displacement from the starting position.
- The inference P90 uncertainty radius is recorded in the pair-level CSV, but is not substituted for the empirical P75 error metric.
- No 48-hour or 72-hour performance claims are reported.
- Results describe this approved 11-iceberg test set, not the full Antarctic iceberg population.

## Output files

- Pair-level predictions and errors: `results/ama7_evaluation_per_pair.csv`
- Per-iceberg summary: `results/ama7_evaluation_per_iceberg.csv`

## Sea-ice concentration boundary handling

The AMA-7 evaluation applied a numerical tolerance of 0.0001 to sea-ice concentration (`siconc`), which must be within [0, 1].

- Four eligible records had marginally high values: D28 (3 records) and D30B (1 record).
- Maximum observed value: 1.0000152583234012.
- No values were below 0.
- No values exceeded the permitted numerical tolerance.
- The four small boundary overshoots were clipped to 1.0 only in the in-memory evaluation DataFrame.
- The original `training_table.csv` was not modified.
- No percentage conversion or synthetic replacement was applied.


## Sea-ice concentration boundary handling

The AMA-7 evaluation applied a numerical tolerance of 0.0001 to sea-ice concentration (`siconc`), which must be within [0, 1].

- Four eligible records had marginally high values: D28 (3 records) and D30B (1 record).
- Maximum observed value: 1.0000152583234012.
- No values were below 0.
- No values exceeded the permitted numerical tolerance.
- The four small boundary overshoots were clipped to 1.0 only in the in-memory evaluation DataFrame.
- The original `training_table.csv` was not modified.
- No percentage conversion or synthetic replacement was applied.

