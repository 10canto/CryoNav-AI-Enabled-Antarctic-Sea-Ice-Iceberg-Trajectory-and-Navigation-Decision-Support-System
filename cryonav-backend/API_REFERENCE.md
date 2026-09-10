# 📡 CryoNav AI - API Reference

Complete documentation for all API endpoints.

## Base URL

```
http://localhost:8000
```

## Authentication

None required for this demo version.

## Response Format

All endpoints return JSON. Success responses have status code `200`. Error responses include an `error` field and current `scenario` number.

---

## Endpoints

### 1. Health Check

Check if the API is running.

**Endpoint:** `GET /api/health`

**Response:**
```json
{
  "status": "CryoNav API Running",
  "timestamp": "2024-01-15T12:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Server is running

---

### 2. Ice Analysis

Get ice concentration data and zone classifications for the current scenario.

**Endpoint:** `GET /api/ice-analysis`

**Response:**
```json
{
  "timestamp": "2024-01-15T12:00:00Z",
  "ice_zones": [
    {
      "type": "open_water",
      "percentage": 65,
      "coordinates": [[-65.2, -64.5], [-65.1, -64.4]]
    },
    {
      "type": "thin_ice",
      "percentage": 25,
      "coordinates": [[-65.3, -64.6], [-65.2, -64.5]]
    },
    {
      "type": "thick_ice",
      "percentage": 10,
      "coordinates": [[-65.4, -64.7], [-65.3, -64.6]]
    }
  ],
  "average_concentration": 35
}
```

**Status Codes:**
- `200 OK` - Data retrieved successfully
- `404 Not Found` - Data file not available

---

### 3. Icebergs

Get all detected icebergs in the current scenario.

**Endpoint:** `GET /api/icebergs`

**Response (No icebergs):**
```json
{
  "icebergs": []
}
```

**Response (With icebergs):**
```json
{
  "icebergs": [
    {
      "id": "ICE-047",
      "position": {
        "lat": -65.234,
        "lon": -64.567
      },
      "size_meters": {
        "length": 800,
        "width": 600
      },
      "confidence": 0.92,
      "detection_time": "2024-01-15T17:30:00Z"
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Data retrieved successfully
- `404 Not Found` - Data file not available

---

### 4. Drift Predictions

Get drift trajectory predictions for icebergs.

**Endpoint:** `GET /api/predict-drift`

**Query Parameters:**
- `iceberg_id` (optional) - Filter predictions for specific iceberg (e.g., "ICE-047")

**Examples:**
```
GET /api/predict-drift                    # All predictions
GET /api/predict-drift?iceberg_id=ICE-047 # Specific iceberg
```

**Response:**
```json
{
  "predictions": [
    {
      "iceberg_id": "ICE-047",
      "trajectory": [
        {
          "time": "6h",
          "position": {"lat": -65.22, "lon": -64.55},
          "uncertainty_radius_km": 3
        },
        {
          "time": "12h",
          "position": {"lat": -65.20, "lon": -64.52},
          "uncertainty_radius_km": 5
        },
        {
          "time": "24h",
          "position": {"lat": -65.18, "lon": -64.48},
          "uncertainty_radius_km": 8
        }
      ]
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Data retrieved successfully
- `404 Not Found` - Data file not available

---

### 5. Routes

Get route options with waypoints and trade-off metrics.

**Endpoint:** `GET /api/routes`

**Response:**
```json
{
  "routes": [
    {
      "type": "safest",
      "waypoints": [
        {"lat": -65.5, "lon": -64.5},
        {"lat": -65.4, "lon": -64.3},
        {"lat": -65.2, "lon": -64.0},
        {"lat": -64.8, "lon": -63.5}
      ],
      "distance_km": 245,
      "time_hours": 18.5,
      "fuel_liters": 3400,
      "risk_score": 8
    },
    {
      "type": "fastest",
      "waypoints": [...],
      "distance_km": 210,
      "time_hours": 15.2,
      "fuel_liters": 3100,
      "risk_score": 23
    },
    {
      "type": "fuel_efficient",
      "waypoints": [...],
      "distance_km": 225,
      "time_hours": 16.8,
      "fuel_liters": 2950,
      "risk_score": 14
    }
  ],
  "current_selected": "safest"
}
```

**Route Types:**
- `safest` - Minimizes risk score
- `fastest` - Minimizes travel time
- `fuel_efficient` - Minimizes fuel consumption

**Status Codes:**
- `200 OK` - Data retrieved successfully
- `404 Not Found` - Data file not available

---

### 6. Risk Assessment

Get current risk level and safety metrics.

**Endpoint:** `GET /api/risk-assessment`

**Response:**
```json
{
  "level": "GREEN",
  "message": "Safe conditions",
  "ice_concentration": 35,
  "nearest_iceberg_km": 0,
  "collision_risk_percent": 5
}
```

**Risk Levels:**
- `GREEN` - Safe conditions (scenarios 0-1)
- `ORANGE` - Warning - hazard approaching (scenario 2)
- `RED` - EMERGENCY - immediate danger (scenario 3)

**Status Codes:**
- `200 OK` - Assessment retrieved successfully

---

### 7. Explanation

Get AI-generated explanation of the current navigation situation.

**Endpoint:** `GET /api/explanation`

**Response:**
```json
{
  "explanation": "New iceberg detected at position 65.2°S, 64.5°W. Size approximately 800m × 600m. Currently 45 km from planned Route A. Monitoring drift trajectory."
}
```

**Status Codes:**
- `200 OK` - Explanation retrieved successfully
- `404 Not Found` - Explanation file not available

---

### 8. Advance Time

Progress to the next scenario (simulates time passage).

**Endpoint:** `POST /api/advance-time`

**Response:**
```json
{
  "scenario": 1,
  "message": "Advanced to scenario 1"
}
```

**Behavior:**
- Increments scenario number: 0 → 1 → 2 → 3 → 0 (loops)
- Affects all GET endpoints (they return data for new scenario)

**Status Codes:**
- `200 OK` - Scenario advanced successfully

---

### 9. Reset Demo

Reset to initial scenario (scenario 0).

**Endpoint:** `POST /api/reset-demo`

**Response:**
```json
{
  "message": "Demo reset to initial state"
}
```

**Behavior:**
- Sets scenario back to 0
- All GET endpoints return scenario 0 data

**Status Codes:**
- `200 OK` - Demo reset successfully

---

## Error Responses

When data files are not found or errors occur:

```json
{
  "error": "Data not available",
  "scenario": 1
}
```

**Common Error Codes:**
- `404 Not Found` - Data file missing
- `500 Internal Server Error` - Server error

---

## Interactive Documentation

Visit these URLs in your browser for interactive API testing:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

---

## Usage Examples

### Python

```python
import requests

# Health check
response = requests.get("http://localhost:8000/api/health")
print(response.json())

# Get icebergs
response = requests.get("http://localhost:8000/api/icebergs")
icebergs = response.json()["icebergs"]

# Advance scenario
response = requests.post("http://localhost:8000/api/advance-time")
print(response.json())
```

### JavaScript (Fetch)

```javascript
// Get risk assessment
fetch('http://localhost:8000/api/risk-assessment')
  .then(response => response.json())
  .then(data => console.log(data.level));

// Advance time
fetch('http://localhost:8000/api/advance-time', {
  method: 'POST'
})
  .then(response => response.json())
  .then(data => console.log(data.message));
```

### curl

```bash
# Get routes
curl http://localhost:8000/api/routes

# Advance time
curl -X POST http://localhost:8000/api/advance-time

# Reset demo
curl -X POST http://localhost:8000/api/reset-demo
```

---

## Scenario Data Summary

| Scenario | Icebergs | Ice Conc. | Risk Level | Key Event |
|----------|----------|-----------|------------|-----------|
| 0 | 0 | 35% | GREEN | Safe conditions |
| 1 | 1 | 55% | GREEN | Iceberg detected 45km away |
| 2 | 2 | 68% | ORANGE | Iceberg approaching route |
| 3 | 3 | 75% | RED | Imminent collision |

---

## CORS Configuration

CORS is enabled for all origins (`*`) in demo mode. Headers:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: *`
- `Access-Control-Allow-Headers: *`

For production, restrict origins in `app/main.py`.

---

## Rate Limiting

None in demo version. Consider adding for production.

---

## Changelog

### Version 1.0.0
- Initial release with 9 endpoints
- 4 demo scenarios
- Full CRUD operations for demo state
