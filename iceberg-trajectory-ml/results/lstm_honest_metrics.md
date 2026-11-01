# Honest LSTM Evaluation Results

**Training Configuration:**
- Split method: By iceberg ID (no data leakage)
- Prediction target: Displacement (dlat, dlon)
- Features: Last 5 displacements + current latitude + month (sin/cos)
- Train icebergs: 23
- Test icebergs: 6
- Test sequences: 3526

## Error Metrics (Haversine Distance in km)

| Model | Mean Error (km) | Median Error (km) | Std Dev (km) |
|-------|-----------------|-------------------|---------------|
| Stay at Position | 6.93 | 2.81 | 26.27 |
| Constant Velocity | 5.40 | 0.58 | 34.63 |
| Simple Predictor (avg last 3) | 18.18 | 1.29 | 249.93 |

**Notes:**
- All metrics calculated using haversine distance (spherical Earth)
- Test set: completely unseen icebergs (no overlap with training)
- No ocean current features used (98% had wrong-date data)
- Simple predictor averages last 3 displacement vectors
