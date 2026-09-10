# 🚀 CryoNav AI - Quick Start Guide

Get the backend running in **under 2 minutes**!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

**Expected output:** Successfully installed fastapi, uvicorn, pydantic...

## Step 2: Start the Server

```bash
uvicorn app.main:app --reload
```

**Alternative:**
```bash
python app/main.py
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Step 3: Test the API

### Option A: Browser (Easiest)

Open your browser and go to:
- **http://localhost:8000/docs** - Interactive API documentation
- **http://localhost:8000/api/health** - Health check endpoint

### Option B: Command Line

```bash
# Health check
curl http://localhost:8000/api/health

# Get ice data
curl http://localhost:8000/api/ice-analysis

# Get icebergs
curl http://localhost:8000/api/icebergs

# Advance to next scenario
curl -X POST http://localhost:8000/api/advance-time
```

### Option C: Postman

1. Open Postman
2. Create a new request
3. Set method to **GET**
4. Enter URL: **http://localhost:8000/api/health**
5. Click **Send**

## Step 4: Demo the Scenarios

The demo has 4 scenarios that simulate time progression:

1. **Start at scenario 0** (safe conditions)
   ```bash
   curl http://localhost:8000/api/risk-assessment
   # Returns: "level": "GREEN"
   ```

2. **Advance time** to see new conditions
   ```bash
   curl -X POST http://localhost:8000/api/advance-time
   curl http://localhost:8000/api/risk-assessment
   # Returns: "level": "GREEN" (scenario 1 - monitoring)
   ```

3. **Advance again** for warning scenario
   ```bash
   curl -X POST http://localhost:8000/api/advance-time
   curl http://localhost:8000/api/risk-assessment
   # Returns: "level": "ORANGE"
   ```

4. **Advance once more** for emergency
   ```bash
   curl -X POST http://localhost:8000/api/advance-time
   curl http://localhost:8000/api/risk-assessment
   # Returns: "level": "RED"
   ```

5. **Reset** back to start
   ```bash
   curl -X POST http://localhost:8000/api/reset-demo
   ```

## 🎯 Key Endpoints for Demo

| Endpoint | What to Show |
|----------|--------------|
| `/api/health` | Server is running |
| `/api/ice-analysis` | Ice concentration zones |
| `/api/icebergs` | Detected icebergs (empty in scenario 0) |
| `/api/routes` | 3 route options with trade-offs |
| `/api/risk-assessment` | Alert level and metrics |
| `/api/explanation` | AI explanation of current situation |
| `/api/predict-drift` | Iceberg trajectory predictions |

## 🐛 Troubleshooting

### "Module not found" error
```bash
pip install -r requirements.txt
```

### Port 8000 already in use
```bash
uvicorn app.main:app --reload --port 8001
```
Then use http://localhost:8001 instead

### CORS errors from frontend
- Already configured to allow all origins for demo
- If still having issues, check browser console

### "File not found" errors
- Make sure you're in the `cryonav-backend` directory
- Check that `data/scenarios/` folder exists with all files

## 📱 Frontend Integration

Point your frontend to:
```
API Base URL: http://localhost:8000
```

All endpoints return JSON. Example:
```json
{
  "level": "GREEN",
  "message": "Safe conditions",
  "ice_concentration": 35,
  "nearest_iceberg_km": 0,
  "collision_risk_percent": 5
}
```

## 🎬 Demo Script

1. Show health endpoint working
2. Show scenario 0 (safe) - no icebergs
3. Advance time - show iceberg appears
4. Advance time - show warning level increases
5. Advance time - show emergency alert
6. Show explanation text for drama
7. Show route options with different trade-offs
8. Reset and repeat

## 🎉 You're Ready!

The backend is running and serving data. Now build an awesome frontend to visualize it!

---

**Questions?** Check `README.md` for full documentation.
