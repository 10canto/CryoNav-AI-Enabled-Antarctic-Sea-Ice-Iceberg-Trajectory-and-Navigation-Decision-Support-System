# CryoNav AI Backend

Antarctic Ship Navigation System - Hackathon Demo Backend

A FastAPI-based backend serving pre-made JSON data for a 4-scenario navigation demo. No real AI integration - pure demo data for hackathon presentation.

## Project Structure

```
cryonav-backend/
├── app/
│   ├── main.py          # FastAPI app with all endpoints
│   ├── config.py        # Settings and environment variables
│   └── models.py        # Pydantic response models
├── data/
│   └── scenarios/
│       ├── scenario_0/  # Safe conditions (GREEN)
│       ├── scenario_1/  # Iceberg detected - Yellow alert
│       ├── scenario_2/  # Danger approaching - Orange warning
│       └── scenario_3/  # Emergency - Red alert
├── static/              # Static files (images, etc.)
├── requirements.txt
├── .env.example
└── docker-compose.yml
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000

Note: Swagger UI and ReDoc documentation have been disabled for this demo.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/ice-analysis` | Ice concentration data |
| GET | `/api/icebergs` | Detected icebergs |
| GET | `/api/predict-drift?iceberg_id={id}` | Drift predictions |
| GET | `/api/routes` | Route options |
| GET | `/api/risk-assessment` | Risk level & metrics |
| GET | `/api/explanation` | Scenario explanation text |
| POST | `/api/advance-time` | Advance to next scenario |
| POST | `/api/reset-demo` | Reset to scenario 0 |

## Demo Scenarios

The demo cycles through 4 scenarios:

| Scenario | Alert Level | Description |
|----------|-------------|-------------|
| 0 | 🟢 GREEN | Safe conditions, no icebergs |
| 1 | 🟡 YELLOW | Iceberg detected, monitoring |
| 2 | 🟠 ORANGE | Iceberg approaching route |
| 3 | 🔴 RED | Emergency - imminent collision |

Use `POST /api/advance-time` to cycle through scenarios.
Use `POST /api/reset-demo` to return to scenario 0.

## Testing with curl

```bash
# Health check
curl http://localhost:8000/api/health

# Get current ice analysis
curl http://localhost:8000/api/ice-analysis

# Get icebergs
curl http://localhost:8000/api/icebergs

# Get drift predictions
curl http://localhost:8000/api/predict-drift
curl "http://localhost:8000/api/predict-drift?iceberg_id=ICE-047"

# Get routes
curl http://localhost:8000/api/routes

# Get risk assessment
curl http://localhost:8000/api/risk-assessment

# Get explanation
curl http://localhost:8000/api/explanation

# Advance scenario
curl -X POST http://localhost:8000/api/advance-time

# Reset demo
curl -X POST http://localhost:8000/api/reset-demo
```

## Testing with Postman

1. Manually create requests using the endpoints listed above
2. All endpoints return JSON responses
3. Use the API reference in API_REFERENCE.md for detailed schemas

## Environment Variables

Copy `.env.example` to `.env` and modify:

```bash
cp .env.example .env
```

Available variables:
- `API_HOST` - Server host (default: 0.0.0.0)
- `API_PORT` - Server port (default: 8000)
- `API_RELOAD` - Auto-reload on changes (default: true)
- `DATA_DIR` - Data directory path (default: data/scenarios)
- `LOG_LEVEL` - Logging level (default: INFO)

## Docker (Optional)

```bash
docker-compose up --build
```

## Notes

- This is a **hackathon demo** - data is static JSON files
- Global `current_scenario` variable tracks demo state (not persistent)
- CORS enabled for all origins (adjust for production)
- Error handling returns valid JSON, never crashes

## License

Hackathon prototype - not for production use.