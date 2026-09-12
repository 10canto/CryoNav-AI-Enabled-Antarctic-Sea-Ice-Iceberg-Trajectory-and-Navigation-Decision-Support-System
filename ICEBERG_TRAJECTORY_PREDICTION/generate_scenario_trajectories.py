#!/usr/bin/env python
"""
Generate 72h drift trajectories for all 4 CryoNav demo scenarios.
Uses the physics-based DriftPredictor with Monte Carlo uncertainty.
Outputs updated predictions.json files compatible with frontend.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent / "src"))

from drift_physics import DriftPredictor, EnvironmentalData, drift_distance_km

SCENARIOS_DIR = Path("../cryonav-backend/data/scenarios")
PREDICTOR = DriftPredictor()
ENV_DATA = EnvironmentalData()

RISK_LEVELS = {0: "safe", 1: "low", 2: "moderate", 3: "high"}

def load_icebergs(scenario_num):
    """Load icebergs from scenario JSON file."""
    icebergs_path = SCENARIOS_DIR / f"scenario_{scenario_num}" / "icebergs.json"
    if not icebergs_path.exists():
        return []
    with open(icebergs_path, 'r') as f:
        data = json.load(f)
    return data.get("icebergs", [])

def generate_trajectory(iceberg, scenario_num):
    """Generate drift trajectory with uncertainty for a single iceberg."""
    lat = iceberg["position"]["lat"]
    lon = iceberg["position"]["lon"]
    
    conditions = ENV_DATA.get_conditions_at(lat, lon)
    ocean = conditions["ocean_current"]
    wind = conditions["wind"]
    
    # Monte Carlo prediction with uncertainty
    traj = PREDICTOR.predict_with_uncertainty(
        lat=lat,
        lon=lon,
        ocean_current=ocean,
        wind=wind,
        hours=72,
        n_simulations=100
    )
    
    # Filter to only future time points (6, 12, 24, 48, 72)
    future_times = {6, 12, 24, 48, 72}
    traj = [p for p in traj if p["time_hours"] in future_times]
    
    # Calculate drift speed and direction for each point
    trajectory_points = []
    prev_point = {"latitude": lat, "longitude": lon, "time_hours": 0}
    
    for point in traj:
        dist = drift_distance_km(prev_point["latitude"], prev_point["longitude"], 
                                 point["latitude"], point["longitude"])
        time_diff = point["time_hours"] - prev_point["time_hours"]
        drift_speed = dist / (time_diff if time_diff > 0 else 1)
        
        # Calculate bearing
        dlat = point["latitude"] - prev_point["latitude"]
        dlon = point["longitude"] - prev_point["longitude"]
        import math
        bearing = math.degrees(math.atan2(dlon, dlat))
        drift_direction = (bearing + 360) % 360
        
        trajectory_points.append({
            "time_hours": point["time_hours"],
            "latitude": point["latitude"],
            "longitude": point["longitude"],
            "uncertainty_km": point["uncertainty_km"],
            "timestamp": point["timestamp"],
            "drift_speed_kmh": round(drift_speed, 2),
            "drift_direction_deg": round(drift_direction, 1)
        })
        prev_point = point
    
    return trajectory_points

def generate_notes(iceberg, trajectory, scenario_num):
    """Generate human-readable notes about the trajectory."""
    if scenario_num == 0:
        return "No icebergs detected in safe zone"
    elif scenario_num == 1:
        return "Drifting northeast, monitoring for route intersection"
    elif scenario_num == 2:
        return "Approaching Route B - increased collision risk"
    else:
        return "CRITICAL: On collision course with vessel position"

def main():
    print("=" * 60)
    print("  GENERATING SCENARIO TRAJECTORIES")
    print("=" * 60)
    print()
    
    for scenario_num in range(4):
        icebergs = load_icebergs(scenario_num)
        predictions = []
        
        for iceberg in icebergs:
            trajectory = generate_trajectory(iceberg, scenario_num)
            
            pred = {
                "iceberg_id": iceberg["id"],
                "current_position": {
                    "lat": iceberg["position"]["lat"],
                    "lon": iceberg["position"]["lon"]
                },
                "trajectory": trajectory,
                "risk_level": RISK_LEVELS[scenario_num],
                "notes": generate_notes(iceberg, trajectory, scenario_num)
            }
            predictions.append(pred)
        
        # Write updated predictions.json
        out_path = SCENARIOS_DIR / f"scenario_{scenario_num}" / "predictions.json"
        out_path.write_text(json.dumps({"predictions": predictions}, indent=2))
        print(f"[OK] Scenario {scenario_num}: {len(predictions)} icebergs processed -> {out_path}")
    
    print()
    print("=" * 60)
    print("  ALL SCENARIOS UPDATED SUCCESSFULLY")
    print("=" * 60)

if __name__ == "__main__":
    main()