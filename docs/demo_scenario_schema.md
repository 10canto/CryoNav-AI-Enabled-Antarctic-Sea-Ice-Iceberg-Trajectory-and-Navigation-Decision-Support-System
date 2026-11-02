# Demo Scenario Schema

## Overview

The demo scenario is a frozen, pre-generated JSON file that contains all data for a reliable 5-minute presentation. It ensures the demo works 100% offline and produces consistent risk escalation.

## File Location

```
public/demo/scenario.json
```

## Schema

```json
{
  "name": "string",
  "description": "string",
  "generated_at": "ISO 8601 timestamp",
  "steps": [
    {
      "id": "number (1-based)",
      "time": "string (e.g., 'T+0h Departure')",
      "title": "string",
      "shipPosition": {
        "lat": "number",
        "lon": "number",
        "time": "string"
      },
      "ship_trail": [
        { "lat": "number", "lon": "number" }
      ],
      "icebergs": [
        {
          "Iceberg": "string (ID)",
          "Lat": "number",
          "Lon": "number",
          "Length_km": "number",
          "Width_km": "number",
          "Area_km2": "number"
        }
      ],
      "routes": [
        {
          "id": "string",
          "type": "safest | fastest | fuel_efficient",
          "name": "string",
          "color": "string (CSS color)",
          "waypoints": [
            { "lat": "number", "lon": "number" }
          ],
          "coordinates": "array of [lat, lon]",
          "distanceKm": "number (REMAINING distance)",
          "timeDays": "number (REMAINING time)",
          "fuelIndex": "number",
          "riskPercent": "number"
        }
      ],
      "risk": {
        "level": "GREEN | YELLOW | ORANGE | RED",
        "distance_km": "number",
        "nearest_iceberg": "string",
        "reasons": ["string"],
        "timestamp": "ISO 8601 timestamp"
      },
      "explanation": {
        "route_id": "string",
        "route_type": "string",
        "summary": "string",
        "reasons": ["string"],
        "trade_offs": {
          "extra_distance_km": "number",
          "extra_time_hours": "number",
          "extra_fuel_percent": "number",
          "risk_reduction_percent": "number"
        },
        "confidence": "string",
        "data_sources": ["string"]
      },
      "message": "string",
      "alert_sent": "boolean (optional)"
    }
  ]
}
```

## Rules

### Ship Position and Time

1. **Ship position per step** = departure date + elapsed time at ship speed
2. Each step's `shipPosition` represents the vessel's location at that point in time
3. Elapsed time should be realistic based on ship speed (e.g., 12 knots) and distance covered

### Routes

1. **Step 1 (Departure):**
   - Routes start at **Cape Town** (-33.9249, 18.4241)
   - `distanceKm` and `timeDays` are **TOTAL** from Cape Town to Maitri
   
2. **Later Steps:**
   - Routes start at **current ship position** (from `shipPosition`)
   - `distanceKm` and `timeDays` are **REMAINING** distance and time
   - The UI will prepend the ship position to route coordinates if needed

### Ship Trail

3. **Optional `ship_trail` array:**
   - Contains past positions of the ship
   - Rendered as a thin dashed line on the map
   - Empty or omitted in step 1
   - Grows with each subsequent step

Example:
```json
"ship_trail": [
  { "lat": -33.9249, "lon": 18.4241 },  // Cape Town
  { "lat": -40.5, "lon": 20.0 }         // After 24h
]
```

### Risk Escalation

4. Risk levels should escalate for demo:
   - Step 1: GREEN (safe departure)
   - Step 2: YELLOW (iceberg detected)
   - Step 3: ORANGE or RED (crisis)
   - Step 4: GREEN (resolved after reroute)

### Data Consistency

5. All data in each step is **frozen** - no backend calls during demo mode
6. Iceberg positions should reflect drift over time
7. Routes should update to reflect changing conditions

## Generation Script

To regenerate the scenario from live backend data:

```bash
cd backend
python scripts/export_demo.py
```

This will:
1. Call `/calculate-routes` for each step
2. Call `/risk` for each ship position
3. Call `/explain` for the safest route
4. Generate scripted icebergs with realistic drift
5. Override risk levels for proper escalation
6. Save to `cryonav-ai/public/demo/scenario.json`

## Usage in Frontend

```typescript
// Load once and cache
import { fetchOnce } from './utils/resourceCache';

const scenario = await fetchOnce('/demo/scenario.json');

// Apply step data
const step = scenario.steps[stepIndex];
setIcebergs(step.icebergs);
setRoutes(step.routes);
setRiskAssessment(step.risk);
setShipPosition(step.shipPosition);
```

## Notes

- The scenario is designed for a **5-minute live presentation**
- All network requests are eliminated in demo mode
- The data is pre-validated and guaranteed to work
- Route explanations use real backend responses
- Risk assessment is scripted for dramatic effect
