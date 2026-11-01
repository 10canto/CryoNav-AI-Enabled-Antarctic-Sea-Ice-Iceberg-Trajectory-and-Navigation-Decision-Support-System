# CryoNav AI Backend

FastAPI backend for iceberg drift prediction, safe routing, and risk assessment.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

API will be available at `http://localhost:8000`

## Endpoints

- `GET /icebergs` - Current iceberg positions
- `GET /predict-drift` - Physics-based drift prediction
- `GET /ocean-currents` - Regional ocean current data
- `POST /calculate-routes` - Safe navigation routes
- `GET /risk` - Risk assessment
- `POST /alert` - Simulated satellite alert
- `GET /explain` - Route explanation

## Notes

- Uses physics-based predictor with Monte Carlo uncertainty
- Ocean currents from Copernicus Marine (monthly, Oct 2025 - Aug 2026)
- Ice field data is SIMULATED for demo purposes
- Alerts are SIMULATED - not sent to real recipients
