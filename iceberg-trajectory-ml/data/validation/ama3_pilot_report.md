# AMA-3 Pilot Report

Generated : 2026-11-05 23:41:04
Pilot year: 2016

## Extraction Statistics

| Metric | Value |
|---|---|
| Positions requested | 1607 |
| Already cached (skipped) | 0 |
| Newly fetched | 1607 |
| Missing values (land/ice/gap) | 759 |
| API errors | 0 |
| Retries | 0 |
| Success rate | 100.0% |

## Variable Coverage (pilot year, fetched rows only)

| Variable | Non-missing | Missing | Missing % |
|---|---|---|---|
| uo | 1404 | 203 | 12.6% |
| vo | 1404 | 203 | 12.6% |
| siconc | 1254 | 353 | 22.0% |
| usi | 1173 | 434 | 27.0% |
| vsi | 1173 | 434 | 27.0% |

## Cache File

Path  : `C:\Users\Amar\Desktop\cryonav\CryoNav-AI-Enabled-Antarctic-Sea-Ice-Iceberg-Trajectory-and-Navigation-Decision-Support-System\iceberg-trajectory-ml\data\validation\ocean_forcing_cache.csv`
Rows  : 1607  (this pilot)
Size  : 129.6 KB

## Sample Rows (first 3)

```
iceberg=D20A  date=2016-01-01  lat=-69.15  lon=36.4833  uo=-0.005493  vo=0.01587  siconc=0.999443
iceberg=D20B  date=2016-01-01  lat=-69.0167  lon=36.3333  uo=-0.002441  vo=0.014649  siconc=0.983077
iceberg=D20A  date=2016-01-02  lat=-69.15  lon=36.4833  uo=-0.004273  vo=0.014649  siconc=0.993683
```

## AMA-3 Pilot Acceptance Check

- [ ] API connectivity confirmed
- [ ] Correct variables extracted (uo, vo, siconc)
- [ ] Coordinate and timestamp matching verified
- [ ] Missing-value handling works
- [ ] Cache written and readable

_Full 29-year extraction requires explicit approval after pilot review._