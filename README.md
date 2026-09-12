# CryoNav AI — Antarctic Ship Navigation System

AI-powered maritime navigation dashboard for polar research vessels.
Routes a ship from **Chennai, India** to **Maitri Research Station, Antarctica** through
4 escalating ice-hazard scenarios, with real-time iceberg drift prediction,
YOLOv5-based satellite detection, and route-aware emergency alerts.

---

## Project Structure

```
Hackathon/
├── cryonav-ai/                  ← React + Vite frontend (port 3000)
├── cryonav-backend/             ← FastAPI backend (port 8000)
└── ICEBERG_TRAJECTORY_PREDICTION/   ← Python prediction engine
```

---

## Run Commands (CMD / PowerShell)

> Open **two separate terminal windows** — one for the backend, one for the frontend.

---

### Terminal 1 — Backend (FastAPI)

```cmd
cd cryonav-backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Backend runs at: **http://localhost:8000**

---

### Terminal 2 — Frontend (React + Vite)

```cmd
cd cryonav-ai
npm install
npm run dev
```

Frontend runs at: **http://localhost:3000**

---

### Optional — Trajectory Prediction Engine

```cmd
cd ICEBERG_TRAJECTORY_PREDICTION
pip install -r requirements.txt
python main.py --mock
```

To regenerate scenario trajectory data:

```cmd
cd cryonav-backend
python generate_scenario_trajectories.py
```

---

## One-Shot Setup (First Time)

Run this once from the project root to copy model weights and sample images:

```cmd
python setup_project.py
```

---

## Quick Verify (after both servers are running)

```cmd
curl http://localhost:8000/api/health
curl http://localhost:3000
```

---

## Demo Flow

Once both servers are running, open **http://localhost:3000** in your browser.

| Step | Action | What you see |
|------|--------|--------------|
| 1 | Open browser | Scenario 0 — ship departing Chennai, no icebergs |
| 2 | Click **Advance** | Scenario 1 — ICE-047 detected in Iceberg Alley (green trajectory) |
| 3 | Click **Advance** | Scenario 2 — ICE-047 approaching route (orange warning) |
| 4a | Stay on **Route A**, click **Advance** | Scenario 3 — ✅ **Success modal** — arrived safely |
| 4b | Switch to **Route B or C**, click **Advance** | Scenario 3 — ⚠️ **Iceberg Collision Warning** modal |
| 5 | Click **Reset** | Back to Scenario 0 |

---

## Routes

| Route | Color | Risk | Behaviour in Scenario 3 |
|-------|-------|------|--------------------------|
| A — Safest | Green solid | 12–18% | ✅ Destination reached |
| B — Fastest | Orange dashed | 38–98% | ⚠️ Collision warning |
| C — Fuel-Efficient | Orange dotted | 23–35% | ⚠️ Collision warning |
| Coastal Hugging | Purple solid | 18% | ⚠️ Collision warning |
| Middle Balance | Pink dashed | 26% | ⚠️ Collision warning |

---

## API Endpoints (Backend)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/icebergs` | Icebergs for current scenario |
| GET | `/api/ice-analysis` | Ice zone concentration data |
| GET | `/api/predict-drift` | Trajectory predictions |
| GET | `/api/routes` | Route options |
| GET | `/api/risk-assessment` | Risk level and metrics |
| GET | `/api/explanation` | AI explanation text |
| POST | `/api/advance-time` | Advance to next scenario |
| POST | `/api/reset-demo` | Reset to scenario 0 |
| GET | `/api/model-status` | YOLO model status |
| POST | `/api/model-mode` | Toggle demo/live detection |

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Leaflet, react-leaflet |
| Backend | Python, FastAPI, Uvicorn |
| AI Detection | YOLOv5 (best.pt), Ultralytics |
| Drift Prediction | Physics-based Monte Carlo (NumPy, SciPy) |
| Styling | CSS, Tailwind |

---

## Environment (Optional)

Copy `.env.example` to `.env` in both folders if you need custom ports:

```cmd
cd cryonav-backend
copy .env.example .env

cd ../cryonav-ai
copy .env.example .env
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `npm install` fails | Run `npm install --legacy-peer-deps` |
| `pip install` fails | Run `pip install -r requirements.txt --user` |
| Port 3000 in use | Change port: `npm run dev -- --port 3001` |
| Port 8000 in use | Change port: `uvicorn app.main:app --reload --port 8001` |
| No trajectories on map | Backend may be offline — frontend uses mock data automatically |
| Model not loading | Run `python setup_project.py` to copy `best.pt` to the right place |

---

## Hackathon Demo Checklist

- [ ] `cd cryonav-backend && python -m uvicorn app.main:app --reload`
- [ ] `cd cryonav-ai && npm run dev`
- [ ] Open http://localhost:3000
- [ ] Test Route A through all 4 scenarios → success modal
- [ ] Test Route B/C through scenario 3 → collision warning modal
- [ ] Toggle trajectory layer on/off from map controls
- [ ] Click iceberg trajectory circles → popups with drift data
