# Training Data Summary

**Created**: 2026-11-08T14:28:32.229637+00:00  
**Data Source**: REAL (observational data only)

## Sources

1. BYU Antarctic Iceberg Database v8.0 (iceberg positions)
2. Copernicus Marine GLORYS12 (ocean currents and sea ice)
3. ERA5 Reanalysis (atmospheric winds)

## Dataset Statistics

- **Total rows**: 27,707
- **Unique icebergs**: 61
- **Date range**: 1995-09-03 to 2021-12-30
- **Years included**: 21 years (1995-2021)
- **Partial data**: No
- **Max time gap**: 3 days

## Data Completeness

- **Complete cases** (all forcing available): 22,631 (81.7%)
- **Outliers flagged** (speed > 2 m/s): 2 (0.0%)

### Valid Data by Variable

| Variable | Valid | Missing | % Valid |
|----------|-------|---------|---------|
| uo | 25,541 | 2,166 | 92.2% |
| vo | 25,541 | 2,166 | 92.2% |
| siconc | 22,631 | 5,076 | 81.7% |
| usi | 23,532 | 4,175 | 84.9% |
| vsi | 23,532 | 4,175 | 84.9% |
| u10 | 27,707 | 0 | 100.0% |
| v10 | 27,707 | 0 | 100.0% |

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
