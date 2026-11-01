# CryoNav AI - Antarctic Iceberg Drift Prediction & Safe Routing

AI-enabled decision support system for Antarctic navigation using physics-based iceberg trajectory prediction, ocean currents, and intelligent routing.

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

Backend runs at `http://localhost:8000`

### Frontend

```bash
cd cryonav-ai
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

## Features

### 🧊 Hybrid Drift Prediction
- **Primary**: Track extrapolation from recent positions (if ≥2 available)
- **Fallback**: Current-based physics model when track unavailable
- Calibrated uncertainty from real validation data
- 24h/48h/72h uncertainty quantification
- Returns method used: "track_extrapolation" or "current_based_fallback"
- Real iceberg positions from BYU Antarctic Tracking Database

### 🗺️ Intelligent Routing
- 3 route options: Safest, Fastest, Fuel-Efficient
- A* pathfinding with ice field avoidance
- Real-time risk assessment (GREEN/YELLOW/ORANGE/RED)
- Explainable AI route recommendations

### 📊 Honest ML Evaluation
- Split by iceberg ID (no data leakage)
- Displacement prediction (not absolute positions)
- Baseline comparison: "Stay at position" vs "Constant velocity"
- Results: `iceberg-trajectory-ml/results/lstm_honest_metrics.md`

### 🎭 Demo Mode
- Scripted 6-hour scenario
- Risk escalation: GREEN → YELLOW → ORANGE → Crisis Averted
- Interactive decision making

## Data Sources

- **Iceberg Positions**: BYU Antarctic Iceberg Tracking Database (real)
- **Ocean Currents**: Copernicus Marine Service (monthly, Oct 2025 - Aug 2026)
- **Ice Fields**: SIMULATED (smooth noise for demo purposes)
- **Drift Model**: Physics-based with Monte Carlo uncertainty

## Disclaimer

**Track extrapolation with current-based fallback. Error measured on a small sample; to be validated.**

Ice concentration fields are SIMULATED demo data. Satellite alerts are SIMULATED - not sent to real recipients.

## Project Structure

```
├── backend/               # FastAPI backend
│   ├── main.py           # API endpoints
│   ├── routing.py        # A* pathfinding engine
│   └── requirements.txt
├── cryonav-ai/           # React frontend
│   ├── src/
│   │   ├── components/   # UI components
│   │   ├── services/     # API client
│   │   └── types/        # TypeScript types
│   └── public/
├── iceberg-trajectory-ml/ # ML & prediction
│   ├── src/
│   │   ├── physics_predictor.py
│   │   ├── train_honest_lstm.py
│   │   └── audit_lstm_model.py
│   ├── data/             # Ocean currents (not in git)
│   └── results/          # Evaluation metrics
└── DATA/                 # Raw data (not in git)
```

## Development Notes

- Old LSTM R²=0.9996 was invalid (data leakage, wrong dates)
- New honest evaluation: ~7 km mean error (realistic)
- Large data files (DATA/*.nc, ocean_currents_yearly/*.json) are local only
- Backend uses physics model by default; LSTM optional via ?model=lstm

## License

Educational/Research Use - See LICENSE
