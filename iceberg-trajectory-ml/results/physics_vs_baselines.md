# Physics Predictor Evaluation Results

## Dataset

- **Ocean Current Data**: Oct 2025 - Aug 2026 (monthly, Copernicus Marine)
- **Iceberg Observations**: 612 observations in date range
- **Icebergs**: 3 unique icebergs
- **Test Sequences**: 603 (with 24h/48h/72h ground truth)

## Error Metrics (Haversine Distance in km)

| Horizon | N | Model | Mean (km) | Median (km) |
|---------|---|-------|-----------|-------------|
| 24h | 603 | Stay at Position | 2.49 | 0.00 |
| 24h | 603 | Constant Velocity | 2.19 | 0.02 |
| 24h | 603 | **Physics Predictor** | **6.19** | **4.05** |
| 48h | 603 | Stay at Position | 4.61 | 0.08 |
| 48h | 603 | Constant Velocity | 4.33 | 0.59 |
| 48h | 603 | **Physics Predictor** | **11.53** | **7.61** |
| 72h | 603 | Stay at Position | 6.60 | 0.59 |
| 72h | 603 | Constant Velocity | 6.51 | 1.77 |
| 72h | 603 | **Physics Predictor** | **16.42** | **10.92** |

## Notes

- **Physics Predictor**: Monte Carlo simulation with ocean currents, wind, and Coriolis effect
- **Baseline 1 (Stay)**: Assumes iceberg remains at starting position
- **Baseline 2 (Velocity)**: Assumes constant velocity from previous observation
- **Ground Truth**: Real iceberg positions from BYU Antarctic Tracking Database
- **Honest Reporting**: All errors calculated using haversine distance (spherical Earth)

## Interpretation

[WARNING] Physics predictor does NOT outperform baselines. Best model: Velocity

**Why physics might not win:**
- Monthly ocean currents (not daily) miss short-term dynamics
- Limited validation data (few icebergs in Oct 2025 - Aug 2026)
- Monte Carlo noise with small sample size
- Icebergs respond to local conditions not captured in coarse grid

**Future Improvements:**
- Daily ocean current data (not monthly)
- Wind speed/direction integration
- Iceberg size-dependent drift coefficients
- More validation data in correct time period
