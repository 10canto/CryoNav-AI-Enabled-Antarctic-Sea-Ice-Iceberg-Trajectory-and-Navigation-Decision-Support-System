# Sea Ice Concentration Forecast Results

**WARNING: SYNTHETIC DATA - NOT FOR PRODUCTION USE**

## Test Performance

| Lead Time | Model | MAE (pp) | RMSE (pp) |
|-----------|-------|----------|-----------|
| Lead1d    | Persistence  |    3.02 |    4.42 |
| Lead1d    | Climatology  |   18.98 |   23.12 |
| Lead1d    | GBM          |    2.60 |    4.01 |
| Lead3d    | Persistence  |    3.48 |    5.85 |
| Lead3d    | Climatology  |   19.01 |   23.19 |
| Lead3d    | GBM          |    3.09 |    5.49 |
| Lead5d    | Persistence  |    3.94 |    6.98 |
| Lead5d    | Climatology  |   19.04 |   23.25 |
| Lead5d    | GBM          |    3.59 |    6.62 |
| Lead7d    | Persistence  |    4.40 |    7.97 |
| Lead7d    | Climatology  |   19.08 |   23.32 |
| Lead7d    | GBM          |    4.10 |    7.56 |


## Data Source

SYNTHETIC sea-ice concentration data with realistic patterns.

## Honest Assessment

- **1 days**: GBM wins, 13.9% better than persistence
- **3 days**: GBM wins, 11.4% better than persistence
- **5 days**: GBM wins, 8.8% better than persistence
- **7 days**: GBM wins, 6.8% better than persistence


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
