# API Contracts - Spec to Implementation Mapping

This document maps the 7 core specification endpoints to their actual implementation in `cryonav-backend/app/main.py`.

## Endpoint Mapping

### 1. Ice Analysis
**Spec Name:** Ice Analysis / Sea Ice Concentration  
**Implemented URL:** `GET /api/ice-analysis`  
**Status:** ✅ IMPLEMENTED (MOCK)  
**Name Match:** ✓ Exact match

**Implementation Details:**
- Returns ice concentration zones with percentages
- Data source: Scenario JSON files (`data/scenarios/scenario_N/ice_data.json`)
- Mock data with honest labeling (returns error dict if not found)

**Example Request:**
```bash
GET http://localhost:8000/api/ice-analysis
```

**Example Response:**
```json
{
  "timestamp": "2024-01-15T12:00:00Z",
  "ice_zones": [
    {
      "type": "open_water",
      "percentage": 65,
      "coordinates": [[-65.2, -64.5], [-65.1, -64.4]]
    }
  ],
  "average_concentration": 35
}
```

---

### 2. Iceberg Detection
**Spec Name:** Iceberg Detection / Icebergs  
**Implemented URL:** `GET /api/icebergs`  
**Status:** ✅ IMPLEMENTED (HYBRID - Real YOLO or Mock)  
**Name Match:** ✓ Exact match

**Implementation Details:**
- Uses `iceberg_service` abstraction layer
- Can return real YOLO detections (if `USE_REAL_MODEL=true`) OR scenario mock data
- Metadata clearly indicates source ("scenario_data" or "real_time_detection")
- Honest fallback behavior with clear error messages

**Example Request:**
```bash
GET http://localhost:8000/api/icebergs
```

**Example Response:**
```json
{
  "icebergs": [
    {
      "id": "ICE-047",
      "position": {"lat": -65.234, "lon": -64.567},
      "size_meters": {"length": 800, "width": 600},
      "confidence": 0.92,
      "detection_time": "2024-01-15T17:30:00Z"
    }
  ],
  "metadata": {
    "source": "scenario_data",
    "scenario": 1,
    "total_detections": 1
  }
}
```

---

### 3. Drift Prediction
**Spec Name:** Drift Trajectory Prediction  
**Implemented URL:** `GET /api/predict-drift`  
**Status:** ✅ IMPLEMENTED (MOCK)  
**Name Match:** ⚠️ Minor variation (spec: "predict-drift", could be "drift-predictions")

**Implementation Details:**
- Returns predicted iceberg trajectories with uncertainty radii
- Optional `iceberg_id` query parameter for filtering
- Data source: Scenario JSON files
- Mock data with honest labeling

**Example Request:**
```bash
GET http://localhost:8000/api/predict-drift?iceberg_id=ICE-047
```

**Example Response:**
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
        }
      ]
    }
  ]
}
```

---

### 4. Route Calculation
**Spec Name:** Route Calculation / Navigation Routes  
**Implemented URL:** `GET /api/routes`  
**Status:** ✅ IMPLEMENTED (MOCK)  
**Name Match:** ⚠️ Minor variation (spec: "routes", could be "calculate-routes")

**Implementation Details:**
- Returns multiple route options (safest, fastest, fuel_efficient)
- Includes waypoints, distance, time, fuel, and risk score
- Data source: Scenario JSON files
- Mock data with honest labeling

**Example Request:**
```bash
GET http://localhost:8000/api/routes
```

**Example Response:**
```json
{
  "routes": [
    {
      "type": "safest",
      "waypoints": [{"lat": -65.5, "lon": -64.5}],
      "distance_km": 245,
      "time_hours": 18.5,
      "fuel_liters": 3400,
      "risk_score": 8
    }
  ],
  "current_selected": "safest"
}
```

---

### 5. Risk Assessment
**Spec Name:** Risk Assessment  
**Implemented URL:** `GET /api/risk-assessment`  
**Status:** ✅ IMPLEMENTED (MOCK) - ⚠️ **NOT HONESTLY LABELED**  
**Name Match:** ✓ Exact match

**Implementation Details:**
- Returns risk level (GREEN/YELLOW/ORANGE/RED)
- Hardcoded risk levels per scenario
- Mock distance calculations
- **ISSUE:** Does not include "simulated" or "mock" flag (will be fixed in Step 2)

**Example Request:**
```bash
GET http://localhost:8000/api/risk-assessment
```

**Example Response (Current - Missing "simulated" flag):**
```json
{
  "level": "YELLOW",
  "message": "Iceberg detected - monitoring situation",
  "ice_concentration": 55,
  "nearest_iceberg_km": 45,
  "collision_risk_percent": 12
}
```

---

### 6. Alert System
**Spec Name:** Alert / Emergency Alert  
**Implemented URL:** `POST /api/alert`  
**Status:** ✅ IMPLEMENTED (SIMULATED)  
**Name Match:** ✓ Exact match

**Implementation Details:**
- Accepts JSON body with message, severity (RED/ORANGE/YELLOW), and optional recipients list
- Logs alerts to `cryonav-backend/app/alerts.json` file
- Generates timestamp-based alert IDs
- Default recipients: ["bridge", "mission_control"]
- **Honest labeling:** Response includes `"simulated": true` flag

**Example Request:**
```bash
POST http://localhost:8000/api/alert
Content-Type: application/json

{
  "message": "Iceberg collision risk",
  "severity": "RED",
  "recipients": ["bridge", "mission_control"]
}
```

**Example Response:**
```json
{
  "alert_id": "20261104233500",
  "timestamp": "2026-11-04T23:35:00Z",
  "message": "Iceberg collision risk",
  "severity": "RED",
  "recipients": ["bridge", "mission_control"],
  "simulated": true
}
```

---

### 7. Explanation
**Spec Name:** AI Explanation  
**Implemented URL:** `GET /api/explanation`  
**Status:** ✅ IMPLEMENTED (MOCK)  
**Name Match:** ✓ Exact match

**Implementation Details:**
- Returns plain-language explanation of current navigation situation
- Data source: Scenario text files
- Mock data with honest labeling (returns error if file not found)

**Example Request:**
```bash
GET http://localhost:8000/api/explanation
```

**Example Response:**
```json
{
  "explanation": "New iceberg detected at position 65.2°S, 64.5°W. Size approximately 800m × 600m. Currently 45 km from planned Route A. Monitoring drift trajectory."
}
```

---

## Additional Endpoints (Not in Core Spec)

### Ocean Currents (Spec Addition)
**Implemented URL:** **NOT YET IMPLEMENTED** (will be added in Step 2)  
**Status:** 🔴 PLANNED  
**Purpose:** Provide ocean current vector data for visualization

---

## Summary Table

| # | Spec Endpoint | Implemented URL | Status | Name Match | Honest Label |
|---|---------------|-----------------|--------|------------|--------------|
| 1 | Ice Analysis | `/api/ice-analysis` | ✅ MOCK | ✓ | ✓ |
| 2 | Icebergs | `/api/icebergs` | ✅ HYBRID | ✓ | ✓ |
| 3 | Drift Prediction | `/api/predict-drift` | ✅ MOCK | ⚠️ Minor | ✓ |
| 4 | Routes | `/api/routes` | ✅ MOCK | ⚠️ Minor | ✓ |
| 5 | Risk Assessment | `/api/risk-assessment` | ✅ MOCK | ✓ | ❌ Missing flag |
| 6 | Alert | `/api/alert` | ✅ SIMULATED | ✓ | ✓ |
| 7 | Explanation | `/api/explanation` | ✅ MOCK | ✓ | ✓ |
| - | Ocean Currents | `/api/ocean-currents` | 🔴 PLANNED | - | - |

---

## Notes

1. **Name Mismatches:** Minor variations exist (e.g., `/api/routes` vs `/api/calculate-routes` in comments)
2. **Critical Fix Needed:** `/api/risk-assessment` needs "simulated": true flag (Step 2)
3. **Planned Addition:** `/api/ocean-currents` endpoint (Step 2)
4. **Honest Labeling:** Most endpoints correctly indicate mock/simulated status except risk-assessment
5. **Hybrid Capability:** Iceberg endpoint supports both real YOLO detection and mock data with clear metadata

---

## Implementation Status Legend

- ✅ **IMPLEMENTED** - Fully functional
- ✅ **MOCK** - Returns simulated data with honest labeling
- ✅ **HYBRID** - Can use real or mock data based on configuration
- ✅ **SIMULATED** - Returns simulated results with clear disclaimer
- 🔴 **PLANNED** - Not yet implemented
- ⚠️ **NEEDS FIX** - Implemented but missing honest labeling
