# CryoNav Drift Model — Backend Integration Guide

## What the Model Does

The CryoNav drift model predicts where an iceberg will be in 24 hours given ocean currents, wind, and sea ice conditions. It returns a predicted latitude/longitude plus an uncertainty circle (in kilometers) that represents the 90th percentile position error. The model was trained on 28,000 real observations of 61 Antarctic tabular icebergs tracked from 1995 to 2021.

## How to Call It

```python
import sys
sys.path.insert(0, "iceberg-trajectory-ml/scripts")
from ama8_inference import predict_iceberg_position

result = predict_iceberg_position(
    lat=-65.0,           # Current iceberg latitude (degrees)
    lon=30.0,            # Current iceberg longitude (degrees)
    ocean_u=0.15,        # Ocean current eastward (m/s)
    ocean_v=0.05,        # Ocean current northward (m/s)
    wind_u=-8.0,         # Wind eastward at 10m height (m/s)
    wind_v=3.0,          # Wind northward at 10m height (m/s)
    siconc=0.4,          # Sea ice concentration (0.0 to 1.0)
    ice_u=0.02,          # Sea ice velocity eastward (m/s, optional)
    ice_v=0.01           # Sea ice velocity northward (m/s, optional)
)

# Returns:
# {
#   "predicted_lat": -64.9712,
#   "predicted_lon": 30.0438,
#   "uncertainty_radius_km": 6.81,
#   "speed_category": "slow",
#   "predicted_speed_kmd": 3.15,
#   "model_version": "CryoNav Drift Model v1",
#   "horizon_hours": 24.0
# }
```

## Where to Get Forcing Data

**Ocean currents (uo, vo) + sea ice (siconc, ice_u, ice_v):**
- Source: Copernicus Marine Service
- Dataset: `cmems_mod_glo_phy_my_0.083deg_P1D-m` (GLORYS12 reanalysis)
- Authentication: Set environment variables `COPERNICUSMARINE_SERVICE_USERNAME` and `COPERNICUSMARINE_SERVICE_PASSWORD`
- API: Use `copernicusmarine` Python package

**Wind (u10, v10):**
- Source: ERA5 via Copernicus Climate Data Store (CDS)
- Authentication: Requires `.cdsapirc` file in home directory
- API: Use `cdsapi` Python package

**For the SIH demo:** If real-time forcing is not available, use the most recent available day's data. If sea ice data is unavailable (NaN over ice shelves), set `ice_u=0`, `ice_v=0`, `siconc=0` and add a flag to the UI indicating partial forcing data.

## Uncertainty Explained

The `uncertainty_radius_km` is the 90th percentile of position error from the 2018-2021 validation period. This means 90% of predictions had position errors smaller than this radius.

**Speed-dependent uncertainty:**
- **Stationary** (<2 km/day): ~7.5 km radius
- **Slow** (2-5 km/day): ~6.8 km radius
- **Moderate** (5-10 km/day): ~6.4 km radius
- **Fast** (>10 km/day): ~17.2 km radius

**Display on map:** Draw a circle around the predicted position with radius = `uncertainty_radius_km`. This is your "90% confidence zone" — most icebergs will end up inside this circle.

Exact uncertainty values are in: `iceberg-trajectory-ml/data/validation/model_config.json`

## Limitations (Be Honest with Users)

⚠️ **24-hour horizon only** — The model is validated for 24h forecasts. Do NOT display 48h or 72h predictions without adding a prominent warning that these are extrapolated beyond the validated range.

⚠️ **Giant tabular icebergs only** — Trained on icebergs >10 km in size. May not work accurately for small growlers or bergy bits.

⚠️ **Forcing data gaps** — Ocean/ice data can have NaN values near coastlines or ice shelves. Missing forcing data reduces prediction accuracy. Flag these cases in the UI.

⚠️ **No accuracy percentages** — Do NOT say "95% accurate" or similar. The uncertainty circle IS the accuracy statement. Say: "90% of icebergs end up within this circle."

## File Locations

```
iceberg-trajectory-ml/
├── scripts/
│   └── ama8_inference.py          # Main inference module (import this)
├── data/validation/
│   ├── drift_model.pkl             # Trained model file
│   ├── model_config.json           # Uncertainty bands by speed category
│   └── results/
│       └── ama6_evaluation.md      # Full technical evaluation report
└── HANDOFF.md                      # This file
```

## Dependencies

**Python version:** 3.14 (or 3.8+)

**Required packages:**
```bash
pip install numpy pandas scikit-learn joblib
```

All dependencies should already be installed if you ran the training pipeline.

## Testing

```bash
# Test 1: Run built-in test cases
python iceberg-trajectory-ml/scripts/ama8_inference.py

# Test 2: CLI mode (returns JSON)
python iceberg-trajectory-ml/scripts/ama8_inference.py \
  --lat -65 --lon 30 \
  --uo 0.15 --vo 0.05 \
  --u10 -8 --v10 3 \
  --siconc 0.4

# Test 3: Module import (Python)
python iceberg-trajectory-ml/scripts/test_import.py
```

All tests should pass ✓

## Error Handling

The function raises clear errors for invalid inputs:
- **ValueError**: If any input is NaN or None
- **FileNotFoundError**: If model files are missing
- **ValueError**: If the model was trained on synthetic data (integrity check)

Example:
```python
try:
    result = predict_iceberg_position(...)
except ValueError as e:
    # Handle invalid input: log error and return 400 to client
    print(f"Invalid input: {e}")
except FileNotFoundError as e:
    # Handle missing model: log error and return 500
    print(f"Model not found: {e}")
```

## Questions?

For technical ML details, see: `iceberg-trajectory-ml/data/validation/results/ama6_evaluation.md`

For inference module documentation, see: `iceberg-trajectory-ml/AMA8_INFERENCE_README.md`
