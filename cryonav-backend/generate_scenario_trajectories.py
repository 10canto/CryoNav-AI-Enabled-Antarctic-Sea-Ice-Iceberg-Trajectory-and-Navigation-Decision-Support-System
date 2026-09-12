"""
generate_scenario_trajectories.py
Reads each scenario's icebergs.json, runs physics-based drift prediction,
and writes updated predictions.json files.

Run from the Hackathon root:
    python cryonav-backend/generate_scenario_trajectories.py

Or from inside cryonav-backend/:
    python generate_scenario_trajectories.py
"""

import json
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Try to import the real physics engine; fall back to a local implementation
# so this script works even if ICEBERG_TRAJECTORY_PREDICTION is not installed.
try:
    sys.path.insert(0, str(Path(__file__).parent.parent / "ICEBERG_TRAJECTORY_PREDICTION" / "src"))
    from drift_physics import DriftPredictor, EnvironmentalData, drift_distance_km
    PHYSICS_ENGINE = "ICEBERG_TRAJECTORY_PREDICTION"
except ImportError:
    PHYSICS_ENGINE = "built-in"

    # ── Minimal built-in physics engine ─────────────────────────────────────
    EARTH_OMEGA  = 7.2921e-5
    DEG_TO_M     = 111_000.0
    OCEAN_FACTOR = 0.60
    WIND_FACTOR  = 0.028

    class EnvironmentalData:
        def get_conditions_at(self, lat, lon):
            import random
            rng = random.Random(int(abs(lat * 1000 + lon)) % (2**31))
            return {
                "ocean_current": {
                    "u": 0.28 + rng.gauss(0, 0.06),
                    "v": 0.12 + rng.gauss(0, 0.04),
                },
                "wind": {
                    "u": -9.5 + rng.gauss(0, 1.5),
                    "v":  0.0 + rng.gauss(0, 1.0),
                },
                "data_source": "built-in climatology",
                "timestamp":   datetime.utcnow().isoformat() + "Z",
            }

    class DriftPredictor:
        def predict_with_uncertainty(self, lat, lon, ocean, wind,
                                     hours=72, n_simulations=100):
            import random
            rng     = random.Random(42)
            results = []
            t0      = datetime.utcnow()
            cur_lat = lat
            cur_lon = lon
            dt      = 6 * 3600.0

            for t_hr in [0, 6, 12, 24, 48, 72]:
                if t_hr > hours:
                    break
                results.append({
                    "time_hours":     t_hr,
                    "latitude":       round(cur_lat, 6),
                    "longitude":      round(cur_lon, 6),
                    "uncertainty_km": round(t_hr * 0.47 + rng.gauss(0, 0.5), 2),
                    "timestamp":      (t0 + timedelta(hours=t_hr)).isoformat() + "Z",
                })
                if t_hr < hours:
                    f     = 2.0 * EARTH_OMEGA * math.sin(math.radians(cur_lat))
                    u_b   = OCEAN_FACTOR * ocean["u"] + WIND_FACTOR * wind["u"]
                    v_b   = OCEAN_FACTOR * ocean["v"] + WIND_FACTOR * wind["v"]
                    steps = max(1, (t_hr or 6))
                    cur_lat += (v_b * dt * steps) / DEG_TO_M
                    cos_lat = max(math.cos(math.radians(cur_lat)), 1e-6)
                    cur_lon += (u_b * dt * steps) / (DEG_TO_M * cos_lat)

            return results

    def drift_distance_km(lat1, lon1, lat2, lon2):
        dlat = (lat2 - lat1) * DEG_TO_M
        dlon = (lon2 - lon1) * DEG_TO_M * abs(math.cos(math.radians((lat1+lat2)/2)))
        return round(math.sqrt(dlat**2 + dlon**2) / 1000.0, 1)


# ── Scenario-specific risk mapping ─────────────────────────────────────────

SCENARIO_RISK = {0: "safe", 1: "low", 2: "moderate", 3: "high"}
SCENARIO_NOTES = {
    0: "No icebergs present — safe conditions",
    1: "Drifting northeast, monitoring for route intersection",
    2: "Approaching Route B - increased collision risk",
    3: "CRITICAL: On collision course with vessel position",
}


def _drift_speed_and_dir(p1, p2, dt_hours):
    """Estimate speed (km/h) and direction (degrees) between two positions."""
    dlat  = (p2["latitude"]  - p1["latitude"])  * 111.0
    dlon  = (p2["longitude"] - p1["longitude"])  * 111.0 * abs(
        math.cos(math.radians((p1["latitude"] + p2["latitude"]) / 2.0))
    )
    dist  = math.sqrt(dlat**2 + dlon**2)
    speed = round(dist / dt_hours, 2) if dt_hours else 0.0

    # Bearing: 0 = north, 90 = east
    bearing = math.degrees(math.atan2(dlon, dlat)) % 360
    return speed, round(bearing, 1)


def _enrich_trajectory(traj: list) -> list:
    """Add drift_speed_kmh and drift_direction_deg between consecutive points."""
    enriched = []
    for i, pt in enumerate(traj):
        pt = dict(pt)
        if i < len(traj) - 1:
            next_pt  = traj[i + 1]
            dt_hours = next_pt["time_hours"] - pt["time_hours"]
            speed, bearing = _drift_speed_and_dir(pt, next_pt, dt_hours)
        else:
            # Last point: reuse previous values
            speed, bearing = (enriched[-1]["drift_speed_kmh"],
                              enriched[-1]["drift_direction_deg"]) if enriched else (0.0, 0.0)
        pt["drift_speed_kmh"]    = speed
        pt["drift_direction_deg"] = bearing
        enriched.append(pt)
    return enriched


def generate_for_scenario(scenario_idx: int, data_base: Path,
                           predictor: DriftPredictor,
                           env: EnvironmentalData) -> dict:
    """
    Read icebergs.json, run predictions, return predictions dict.

    Args:
        scenario_idx: 0-3
        data_base:    Path to cryonav-backend/data/scenarios/
        predictor:    DriftPredictor instance
        env:          EnvironmentalData instance

    Returns:
        Dict ready to write to predictions.json
    """
    scenario_dir  = data_base / f"scenario_{scenario_idx}"
    icebergs_path = scenario_dir / "icebergs.json"

    if not icebergs_path.exists():
        print(f"  [SKIP] {icebergs_path} not found")
        return {"predictions": []}

    raw = json.loads(icebergs_path.read_text(encoding="utf-8"))
    icebergs = raw.get("icebergs", [])

    if not icebergs:
        print(f"  Scenario {scenario_idx}: 0 icebergs — writing empty predictions")
        return {"predictions": []}

    risk_level = SCENARIO_RISK.get(scenario_idx, "low")
    notes      = SCENARIO_NOTES.get(scenario_idx, "")
    predictions = []

    for berg in icebergs:
        # Support both {lat, lon} and {latitude, longitude} position keys
        pos = berg.get("position", {})
        lat = pos.get("lat") or pos.get("latitude")
        lon = pos.get("lon") or pos.get("longitude")
        if lat is None or lon is None:
            print(f"  [WARN] Skipping iceberg {berg.get('id')} — no position")
            continue

        cond  = env.get_conditions_at(lat, lon)
        traj  = predictor.predict_with_uncertainty(
            lat, lon,
            cond["ocean_current"], cond["wind"],
            hours=72, n_simulations=50,
        )

        # Skip t=0 (that's the current position, not a future prediction)
        future = [p for p in traj if p["time_hours"] > 0]
        future = _enrich_trajectory(future)

        final = future[-1] if future else {"latitude": lat, "longitude": lon}
        dist  = drift_distance_km(lat, lon,
                                  final["latitude"], final["longitude"])

        predictions.append({
            "iceberg_id":       berg.get("id", "ICE-???"),
            "current_position": {"lat": round(lat, 6), "lon": round(lon, 6)},
            "trajectory":       future,
            "risk_level":       risk_level,
            "notes":            notes,
            "drift_summary": {
                "total_distance_km": dist,
                "forecast_hours":    72,
            },
        })

    return {"predictions": predictions}


def main():
    # Locate the scenarios directory regardless of where the script is run from
    script_dir = Path(__file__).parent.resolve()
    data_base  = script_dir / "data" / "scenarios"

    if not data_base.exists():
        print(f"ERROR: scenarios directory not found at {data_base}")
        sys.exit(1)

    print(f"Physics engine : {PHYSICS_ENGINE}")
    print(f"Scenarios path : {data_base}")
    print()

    predictor = DriftPredictor()
    env       = EnvironmentalData()

    for s in range(4):
        print(f"Scenario {s}:")
        result = generate_for_scenario(s, data_base, predictor, env)
        n      = len(result["predictions"])

        out_path = data_base / f"scenario_{s}" / "predictions.json"
        out_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"  Generated trajectories for scenario {s}: "
              f"{n} iceberg(s) processed")
        print(f"  Written → {out_path}")

    print()
    print("All scenarios updated.")


if __name__ == "__main__":
    main()
