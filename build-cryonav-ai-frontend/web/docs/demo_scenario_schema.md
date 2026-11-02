# Demo Scenario Schema

This document describes the JSON schema for the demo scenario file at `public/demo/scenario.json`.

## Top-Level Structure

```json
{
  "title": "string",
  "placeholder": boolean,
  "note": "string (optional)",
  "steps": [Step, ...]
}
```

- `title`: Human-readable title for the scenario
- `placeholder`: Whether this is placeholder data (true for development data)
- `note`: Optional description or notes about the scenario
- `steps`: Array of 5 steps showing the progression of the scenario

## Step Structure

Each step represents a point in time during the voyage:

```json
{
  "title": "string",
  "label": "string",
  "date": "YYYY-MM-DD",
  "ship": { "lat": number, "lon": number },
  "icebergs": [Iceberg, ...],
  "routes": [Route, ...],
  "selected_route_id": "string",
  "risk": Risk,
  "risk_original": RiskComparison (optional),
  "risk_selected": RiskComparison (optional),
  "predicted_crossing": PredictedCrossing (optional),
  "explanation_text": "string",
  "alert": Alert | null,
  "whatif": [WhatIf, ...]
}
```

### Step Fields

- `title`: Full descriptive title
- `label`: Short label shown in the timeline (e.g., "Baseline", "Timing", "Crisis averted")
- `date`: ISO date string for the step
- `ship`: Current ship position
- `icebergs`: Array of tracked icebergs visible at this step
- `routes`: Array of candidate routes from the current position
- `selected_route_id`: ID of the currently selected route
- `risk`: Overall risk assessment for the selected route
- `risk_original` *(optional)*: Risk of the original plan (used in steps 4-5 for dual risk display)
- `risk_selected` *(optional)*: Risk of the selected reroute (used in steps 4-5 for dual risk display)
- `predicted_crossing` *(optional)*: Location marker for predicted iceberg crossing (shown in step 4, cleared in step 5)
- `explanation_text`: Narrative explanation of the current situation
- `alert`: Alert configuration if RED risk is present, null otherwise
- `whatif`: Array of what-if scenario results

## Iceberg Structure

```json
{
  "id": "string",
  "lat": number,
  "lon": number,
  "size_m": number,
  "method": "string",
  "drift_path": [DriftPoint, ...]
}
```

- `id`: Unique identifier (e.g., "ICE-104")
- `lat`, `lon`: Current position
- `size_m`: Approximate size in meters
- `method`: Drift prediction method (e.g., "track extrapolation", "current-based fallback")
- `drift_path`: Array of predicted future positions

### Drift Point Structure

```json
{
  "hours": number,
  "lat": number,
  "lon": number,
  "uncertainty_radius_km": number
}
```

## Route Structure

```json
{
  "id": "string",
  "name": "string",
  "color": "string",
  "waypoints": [Waypoint, ...],
  "distance_km": number,
  "duration_days": number,
  "risk_score": number,
  "reasons": [string, ...],
  "fuel_index": number
}
```

- `id`: Unique identifier for the route
- `name`: Human-readable name
- `color`: Hex color for map display
- `waypoints`: Array of route waypoints with positions and ETAs
- `distance_km`: Total route distance
- `duration_days`: Estimated duration
- `risk_score`: Numerical risk score (0-100)
- `reasons`: Array of strings explaining the risk factors
- `fuel_index`: Relative fuel consumption index (100 = baseline)

### Waypoint Structure

```json
{
  "lat": number,
  "lon": number,
  "eta": "ISO 8601 datetime string"
}
```

## Risk Structure

```json
{
  "level": "GREEN" | "YELLOW" | "ORANGE" | "RED",
  "reasons": [string, ...]
}
```

## Risk Comparison Structure

*(Used for dual risk display in steps 4-5)*

```json
{
  "level": "GREEN" | "YELLOW" | "ORANGE" | "RED",
  "score": number
}
```

- `level`: Risk level color code
- `score`: Numerical risk score (0-100)

## Predicted Crossing Structure

*(Used in step 4 to show the red zone marker)*

```json
{
  "label": "string",
  "lat": number,
  "lon": number,
  "iceberg_id": "string"
}
```

- `label`: Text label shown on the map (e.g., "Predicted iceberg crossing (72 h)")
- `lat`, `lon`: Position of the predicted crossing
- `iceberg_id`: ID of the iceberg that would cross the route

## Alert Structure

```json
{
  "recipients": [string, ...],
  "simulated": boolean
}
```

- `recipients`: List of alert recipients
- `simulated`: Always true in demo mode

## What-If Structure

```json
{
  "label": "string",
  "before": WhatIfOutcome,
  "after": WhatIfOutcome
}
```

### What-If Outcome Structure

```json
{
  "risk_level": "GREEN" | "YELLOW" | "ORANGE" | "RED",
  "risk_score": number,
  "distance_km": number,
  "duration_days": number,
  "fuel_index": number
}
```

## Scenario Steps Overview

The scenario consists of **5 steps**:

1. **Baseline** - All clear, ship departing Cape Town
2. **Timing** - An iceberg drifts toward the planned corridor
3. **New iceberg** - ICE-104 appears near the route
4. **Reroute + alert** - Original plan blocked (RED), reroute to east arc, alert modal triggered
   - Shows dual risk display: "Original plan: RED (score 88)" vs "Selected route: YELLOW (score 34)"
   - Shows red predicted crossing marker on the map
5. **Crisis averted** - Ship on eastern reroute, risk reduced to YELLOW, no alert
   - Shows dual risk display continues
   - Red crossing marker is cleared
   - Explanation describes successful reroute and added distance/days

## Step 4 vs Step 5 Differences

### Step 4 (Reroute + alert)
- `risk.level`: "RED"
- `alert`: present (triggers modal)
- `risk_original` and `risk_selected`: present for dual display
- `predicted_crossing`: present (shows red marker)
- Ship at: 56°S, 8°E (original corridor)

### Step 5 (Crisis averted)
- `risk.level`: "YELLOW"
- `alert`: null (no modal)
- `risk_original` and `risk_selected`: present for dual display
- `predicted_crossing`: absent (marker cleared)
- Ship at: 63°S, 15.5°E (eastern reroute)
- Explanation includes reroute distance and duration impact

## Implementation Notes

- The RiskCard component checks for `risk_original` and `risk_selected` fields to display dual risk comparison
- The predicted crossing marker is rendered by MapController when `predicted_crossing` is present
- Route pulse animation triggers when the alert modal is acknowledged (alert transitions from open to closed)
- Timeline component displays all 5 step labels
