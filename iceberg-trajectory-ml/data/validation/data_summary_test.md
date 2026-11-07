# Training Data Summary

**Created**: 2026-11-07T03:51:14.790496+00:00  
**Data Source**: REAL (observational data only)

## Sources

1. BYU Antarctic Iceberg Database v8.0 (iceberg positions)
2. Copernicus Marine GLORYS12 (ocean currents and sea ice)
3. ERA5 Reanalysis (atmospheric winds)

## Dataset Statistics

- **Total rows**: 3,567
- **Unique icebergs**: 16
- **Date range**: 2015-01-01 to 2015-12-30
- **Years included**: 1 years (2015-2015)
- **Partial data**: Yes
- **Max time gap**: 3 days

## Data Completeness

- **Complete cases** (all forcing available): 0 (0.0%)
- **Outliers flagged** (speed > 2 m/s): 2 (0.1%)

### Valid Data by Variable

| Variable | Valid | Missing | % Valid |
|----------|-------|---------|---------|
| uo | 3,310 | 257 | 92.8% |
| vo | 3,310 | 257 | 92.8% |
| siconc | 3,044 | 523 | 85.3% |
| usi | 3,310 | 257 | 92.8% |
| vsi | 3,310 | 257 | 92.8% |
| u10 | 0 | 3,567 | 0.0% |
| v10 | 0 | 3,567 | 0.0% |

## Columns

Position data:
- iceberg_id, date, date_next, dt_days, year, month
- lat, lon, lat_next, lon_next

Observed drift:
- dx_km, dy_km, u_obs, v_obs, speed_obs, outlier_flag

Ocean forcing (from GLORYS12):
- uo, vo (ocean currents, m/s)
- siconc (sea ice concentration, 0-1)
- usi, vsi (sea ice drift, m/s)

Atmospheric forcing (from ERA5):
- u10, v10 (10m wind components, m/s)

Flags:
- has_ocean, has_ice, has_wind, complete_case

## Data Integrity

✓ NO synthetic data (all NaN values are real missing data, not filled)  
✓ NO accuracy claims  
✓ Data gate enforced via data_report.json

---

*This dataset contains only REAL observational data. No values have been fabricated, interpolated, or filled.*
