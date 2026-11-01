"""
Export Demo Scenario Script
Calls the real backend to generate frozen demo data for reliable live presentation
"""
import json
import requests
from pathlib import Path
from datetime import datetime

API_BASE = "http://localhost:8000"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "cryonav-ai" / "public" / "demo"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Demo scenario waypoints
CAPE_TOWN = {"lat": -33.9249, "lon": 18.4241}
MAITRI = {"lat": -70.7667, "lon": 11.7333}

# Ship positions for each step (along the route)
SHIP_POSITIONS = [
    {"lat": -40.5, "lon": 20.0, "time": "T+0h Departure"},
    {"lat": -50.2, "lon": 25.5, "time": "T+24h Into Southern Ocean"},
    {"lat": -58.5, "lon": 18.2, "time": "T+48h New Iceberg Detected"},
    {"lat": -62.0, "lon": 15.5, "time": "T+60h Crisis Averted - Rerouted"},
]

def fetch_icebergs():
    """Get current icebergs"""
    try:
        r = requests.get(f"{API_BASE}/icebergs", timeout=5)
        r.raise_for_status()
        return r.json().get("icebergs", [])
    except Exception as e:
        print(f"Failed to fetch icebergs: {e}")
        return []

def fetch_routes(ship_pos, date_str):
    """Calculate routes from Cape Town to Maitri"""
    try:
        r = requests.post(f"{API_BASE}/calculate-routes", json={
            "start": CAPE_TOWN,
            "end": MAITRI,
            "ship": {"speed_knots": 12.0},
            "date": date_str,
            "wind": {"speed": 8, "direction": 210}
        }, timeout=10)
        r.raise_for_status()
        return r.json().get("routes", [])
    except Exception as e:
        print(f"Failed to calculate routes: {e}")
        return []

def fetch_risk(ship_pos, date_str):
    """Assess risk at ship position"""
    try:
        r = requests.get(f"{API_BASE}/risk", params={
            "ship_lat": ship_pos["lat"],
            "ship_lon": ship_pos["lon"],
            "date": date_str
        }, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Failed to assess risk: {e}")
        return {
            "level": "YELLOW",
            "distance_km": 20.0,
            "nearest_iceberg": "Unknown",
            "reasons": ["Risk assessment unavailable"],
            "timestamp": datetime.now().isoformat()
        }

def fetch_explain(route_id):
    """Get route explanation"""
    try:
        r = requests.get(f"{API_BASE}/explain", params={"route_id": route_id}, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Failed to get explanation: {e}")
        return None

def fetch_prediction(iceberg_id, hours=72):
    """Get drift prediction"""
    try:
        r = requests.get(f"{API_BASE}/predict-drift", params={
            "iceberg_id": iceberg_id,
            "hours": hours,
            "model": "hybrid"
        }, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Failed to predict drift for {iceberg_id}: {e}")
        return None

def generate_demo_scenario():
    """Generate complete demo scenario with frozen data"""
    
    print("Fetching icebergs...")
    all_icebergs = fetch_icebergs()
    print(f"Found {len(all_icebergs)} icebergs")
    
    # Select icebergs in the route area
    route_icebergs = [
        ib for ib in all_icebergs 
        if -75 < (ib.get("Lat") or ib.get("lat", 0)) < -35 
        and -20 < (ib.get("Lon") or ib.get("lon", 0)) < 60
    ][:15]  # Limit to 15 real icebergs
    
    print(f"Selected {len(route_icebergs)} real icebergs in route area")
    
    # Add scripted demo icebergs that move to create risk escalation
    demo_icebergs_by_step = [
        # Step 1: Baseline - distant icebergs
        route_icebergs + [
            {"Iceberg": "A81", "Lat": -45.2, "Lon": 28.5, "Length_km": 8.5, "Width_km": 4.2, "Area_km2": 35.7},
            {"Iceberg": "A83", "Lat": -52.8, "Lon": 15.3, "Length_km": 12.3, "Width_km": 6.8, "Area_km2": 83.6},
        ],
        # Step 2: One iceberg drifts closer
        route_icebergs + [
            {"Iceberg": "A81", "Lat": -48.5, "Lon": 26.2, "Length_km": 8.5, "Width_km": 4.2, "Area_km2": 35.7},
            {"Iceberg": "A83", "Lat": -52.8, "Lon": 15.3, "Length_km": 12.3, "Width_km": 6.8, "Area_km2": 83.6},
        ],
        # Step 3: NEW iceberg + closer approach
        route_icebergs + [
            {"Iceberg": "A81", "Lat": -55.2, "Lon": 20.1, "Length_km": 8.5, "Width_km": 4.2, "Area_km2": 35.7},
            {"Iceberg": "A83", "Lat": -52.8, "Lon": 15.3, "Length_km": 12.3, "Width_km": 6.8, "Area_km2": 83.6},
            {"Iceberg": "A85-NEW", "Lat": -57.8, "Lon": 18.5, "Length_km": 15.2, "Width_km": 8.1, "Area_km2": 123.1},
        ],
        # Step 4: After reroute - safe distance
        route_icebergs + [
            {"Iceberg": "A81", "Lat": -58.5, "Lon": 19.2, "Length_km": 8.5, "Width_km": 4.2, "Area_km2": 35.7},
            {"Iceberg": "A83", "Lat": -52.8, "Lon": 15.3, "Length_km": 12.3, "Width_km": 6.8, "Area_km2": 83.6},
            {"Iceberg": "A85-NEW", "Lat": -59.1, "Lon": 17.8, "Length_km": 15.2, "Width_km": 8.1, "Area_km2": 123.1},
        ],
    ]
    
    print(f"Generated scripted icebergs for 4 steps")
    
    # Generate steps
    steps = []
    base_date = datetime.now()
    
    for idx, ship_pos in enumerate(SHIP_POSITIONS):
        step_date = datetime(base_date.year, base_date.month, base_date.day + idx)
        date_str = step_date.isoformat()
        
        print(f"\nGenerating step {idx + 1}: {ship_pos['time']}")
        
        # Get routes
        routes = fetch_routes(ship_pos, date_str)
        print(f"  Routes: {len(routes)}")
        
        # Get risk - override with scripted risk levels
        risk = fetch_risk(ship_pos, date_str)
        
        # Override risk levels for proper escalation
        scripted_risks = ["GREEN", "YELLOW", "ORANGE", "RED"]
        risk["level"] = scripted_risks[idx]
        risk["distance_km"] = [28.5, 18.2, 9.3, 22.1][idx]
        risk["nearest_iceberg"] = ["A81", "A81", "A85-NEW", "A81"][idx]
        risk["reasons"] = [
            ["Clear navigation - Nearest iceberg: 28.5 km", "Low risk - Continue with standard monitoring"],
            ["Iceberg A81 drifting closer: 18.2 km", "Moderate risk - Maintain awareness", "Monitor drift trajectory"],
            ["Iceberg A85-NEW within 10 km (distance: 9.3 km)", "High risk - Monitor closely", "Predicted drift cone blocks planned route", "IMMEDIATE: Reroute recommended"],
            ["Successfully rerouted to safer corridor", "Clear navigation - Nearest iceberg: 22.1 km", "Low risk - Route adds 12 km but maintains safety buffer"]
        ][idx]
        
        print(f"  Risk: {risk['level']} ({risk['distance_km']} km)")
        
        # Get explanation for safest route
        explanation = None
        if routes:
            safest = next((r for r in routes if r.get("type") == "safest"), routes[0])
            explanation = fetch_explain(safest["id"])
            print(f"  Explanation: {explanation['summary'][:50] if explanation else 'N/A'}...")
        
        # Build step
        step = {
            "id": idx + 1,
            "time": ship_pos["time"],
            "title": [
                "Departure - All Clear",
                "Into Southern Ocean",
                "New Iceberg Near Route",
                "Crisis Averted - Rerouted"
            ][idx],
            "shipPosition": ship_pos,
            "icebergs": demo_icebergs_by_step[idx],
            "routes": routes,
            "risk": risk,
            "explanation": explanation,
            "message": [
                "Route initiated from Cape Town. Weather favorable. All systems nominal.",
                "24 hours into voyage. Iceberg A81 drifting toward route. Monitoring closely.",
                "CRITICAL: New iceberg A85-NEW detected ahead. Risk RED. Drift model shows collision risk in 6 hours.",
                "Successfully rerouted to eastern corridor. Risk reduced to GREEN. ETA adjusted +1.5 hours. Crisis averted."
            ][idx],
            "alert_sent": idx == 2  # Alert sent in step 3 (RED risk)
        }
        
        steps.append(step)
    
    # Build scenario
    scenario = {
        "name": "Antarctic Navigation Crisis Demo",
        "description": "Frozen 4-step scenario for live presentation",
        "generated_at": datetime.now().isoformat(),
        "steps": steps
    }
    
    # Save scenario
    output_path = OUTPUT_DIR / "scenario.json"
    with open(output_path, "w") as f:
        json.dump(scenario, f, indent=2)
    
    print(f"\n✓ Demo scenario saved to {output_path}")
    print(f"  {len(steps)} steps")
    
    # Generate predictions for demo icebergs (for cache)
    print("\nGenerating iceberg predictions for cache...")
    predictions = {}
    sample_icebergs = steps[0]["icebergs"][:5] if steps and steps[0]["icebergs"] else []
    for ib in sample_icebergs:  # Limit to 5 for speed
        ib_id = ib.get("Iceberg") or ib.get("id")
        if ib_id:
            pred = fetch_prediction(ib_id, 72)
            if pred:
                predictions[ib_id] = pred
                print(f"  {ib_id}: {len(pred.get('mean_path', []))} points")
    
    # Save predictions cache
    cache_dir = OUTPUT_DIR / "cache"
    cache_dir.mkdir(exist_ok=True)
    
    with open(cache_dir / "predictions.json", "w") as f:
        json.dump(predictions, f, indent=2)
    
    print(f"✓ Saved {len(predictions)} predictions to cache")
    
    return scenario

if __name__ == "__main__":
    print("CryoNav AI Demo Scenario Export")
    print("=" * 50)
    print(f"Backend: {API_BASE}")
    print(f"Output: {OUTPUT_DIR}")
    print()
    
    try:
        scenario = generate_demo_scenario()
        print("\n✓ Demo export complete!")
        print("\nTo use in frontend:")
        print("  1. Start frontend: npm run dev")
        print("  2. Click 'Start Scripted Demo' button")
        print("  3. Step through with 'Next Step' button")
    except Exception as e:
        print(f"\n✗ Export failed: {e}")
        import traceback
        traceback.print_exc()
