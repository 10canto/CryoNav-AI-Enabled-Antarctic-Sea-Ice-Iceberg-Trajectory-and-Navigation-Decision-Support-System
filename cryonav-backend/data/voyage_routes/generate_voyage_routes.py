"""Generate demo-only Chennai-to-Maitri voyage route scenarios.

These are visualisation/planning datasets for a hackathon. They are not an
authorised passage plan, ENC substitute, or instruction to navigate in ice.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

OUT = Path(__file__).parent
START = {"name": "Chennai Port, India", "lat": 13.0827, "lon": 80.2707}
END = {"name": "Maitri Research Station, Antarctica", "lat": -70.7644, "lon": 11.7386}


def wp(lat, lon, label):
    return {"lat": lat, "lon": lon, "label": label}


def numbered(points):
    return [{"seq": index, **point} for index, point in enumerate(points, 1)]


SAFEST = [
    wp(13.0827, 80.2707, "Chennai Port — DEPARTURE"),
    wp(9.2, 81.5, "Palk Strait traffic separation clearance"),
    wp(6.4, 82.8, "Sri Lanka East Pass"),
    wp(1.0, 85.0, "Equator approach — Indian Ocean lane exit"),
    wp(-5.0, 87.0, "Equator crossing"),
    wp(-12.0, 89.0, "Mid-Indian Ocean weather checkpoint"),
    wp(-20.0, 90.0, "Southern Indian Ocean checkpoint"),
    wp(-28.0, 87.0, "Subtropical convergence southbound"),
    wp(-35.0, 82.0, "Weather-routing decision point"),
    wp(-40.0, 75.0, "Roaring Forties entry"),
    wp(-43.0, 68.0, "Westerly storm-track avoidance leg"),
    wp(-46.0, 60.0, "Prince Edward Islands wide eastern clearance"),
    wp(-49.0, 48.0, "Furious Fifties — ice-avoidance transit"),
    wp(-52.0, 34.0, "Iceberg monitoring zone western boundary"),
    wp(-55.0, 26.0, "South of primary Iceberg Alley sector"),
    wp(-58.0, 20.0, "Antarctic Convergence approach"),
    wp(-60.0, 17.0, "Antarctic Convergence crossing"),
    wp(-62.0, 15.5, "Seasonal pack-ice edge assessment"),
    wp(-64.5, 14.2, "Ice navigation commencement"),
    wp(-67.0, 12.9, "Riiser-Larsen Ice Shelf outer approach"),
    wp(-69.0, 12.1, "Final ice-field pilotage waypoint"),
    wp(-70.0, 11.82, "Maitri ice-shelf approach"),
    wp(-70.7644, 11.7386, "Maitri Research Station — ARRIVAL"),
]

FASTEST = [
    wp(13.0827, 80.2707, "Chennai Port — DEPARTURE"),
    wp(8.0, 79.5, "Sri Lanka West Pass"),
    wp(2.0, 77.0, "Indian Ocean lane exit"),
    wp(-5.0, 74.0, "South Equatorial crossing"),
    wp(-13.0, 70.0, "Direct southbound track"),
    wp(-21.0, 65.0, "Mid-Indian Ocean direct transit"),
    wp(-30.0, 58.0, "Weather-routing decision point"),
    wp(-38.0, 50.0, "Roaring Forties entry"),
    wp(-43.0, 42.0, "Prince Edward Islands western clearance"),
    wp(-48.0, 37.0, "Furious Fifties direct leg"),
    wp(-52.0, 33.0, "Iceberg monitoring zone entry"),
    wp(-55.0, 29.0, "Iceberg Alley transit — enhanced watch"),
    wp(-58.0, 25.0, "Antarctic Convergence approach"),
    wp(-60.0, 21.0, "Antarctic Convergence quick crossing"),
    wp(-63.0, 17.5, "Thin-pack ice entry"),
    wp(-66.0, 14.8, "Ice-speed reduction waypoint"),
    wp(-68.5, 12.8, "Riiser-Larsen approach"),
    wp(-70.0, 11.95, "Final ice navigation"),
    wp(-70.7644, 11.7386, "Maitri Research Station — ARRIVAL"),
]

FUEL = [
    wp(13.0827, 80.2707, "Chennai Port — DEPARTURE"),
    wp(8.5, 78.5, "Sri Lanka West Pass"),
    wp(2.0, 75.0, "Indian Ocean lane exit"),
    wp(-5.0, 70.0, "South Equatorial Current checkpoint"),
    wp(-12.0, 65.0, "Southern Indian Ocean transit"),
    wp(-20.0, 57.0, "Current and weather optimisation point"),
    wp(-28.0, 48.0, "Agulhas Return Current region"),
    wp(-35.0, 39.0, "Westward track begins"),
    wp(-40.0, 30.0, "Prince Edward Islands west-pass clearance"),
    wp(-43.0, 23.0, "Roaring Forties westward leg"),
    wp(-45.0, 25.0, "ACC eastbound assist zone entry"),
    wp(-46.0, 32.0, "Maximum eastbound current-assist leg"),
    wp(-48.0, 34.0, "ACC exit and south-west turn preparation"),
    wp(-52.0, 27.0, "Iceberg monitoring waypoint"),
    wp(-57.0, 16.0, "Antarctic Convergence approach"),
    wp(-60.0, 11.0, "Antarctic Convergence crossing"),
    wp(-62.5, 11.3, "Pack-ice edge assessment"),
    wp(-65.0, 11.5, "Managed ice navigation"),
    wp(-67.5, 11.65, "Riiser-Larsen outer approach"),
    wp(-69.0, 11.70, "Final ice navigation"),
    wp(-70.0, 11.73, "Maitri ice-shelf approach"),
    wp(-70.7644, 11.7386, "Maitri Research Station — ARRIVAL"),
]


def route(kind, name, points, distance, days, speed, fuel, risk, description, features):
    return {
        "type": kind,
        "name": name,
        "status": "viable",
        "waypoints": numbered(points),
        "distance_km": distance,
        "distance_nm": round(distance / 1.852),
        "duration_days": days,
        "avg_speed_knots": speed,
        "fuel_liters": fuel,
        "risk_score": risk,
        "description": description,
        "key_features": features,
        "operating_assumptions": {
            "open_ocean_speed_knots": speed,
            "ice_navigation_speed_knots": 9.0,
            "weather_delay_buffer_days": 3,
            "port_procedures_days": 2,
            "ice_entry_weather_window": "72-hour forecast calm window required",
            "minimum_turn_radius_nm": 5,
        },
    }


BASE_ROUTES = [
    route("safest", "Eastern Ice-Avoidance Route", SAFEST, 12200, 34, 15.0, 185000, 12,
          "Conservative wide-clearance route that avoids the main iceberg-density sector and gives extra room for weather routing.",
          ["Wide Prince Edward Islands clearance", "Avoids the 40–60°E iceberg-density sector", "Gradual descent permits ice-edge reassessment"]),
    route("fastest", "Direct Southern Route", FASTEST, 10500, 28, 15.5, 168000, 38,
          "Shortest planned track; accepts thin-pack navigation and closer proximity to monitored iceberg traffic.",
          ["Direct southern geometry", "Enhanced iceberg watch south of 52°S", "Lower weather-routing margin"]),
    route("fuel_efficient", "Current-Assisted Western Route", FUEL, 11200, 31, 15.0, 152000, 23,
          "Balanced route that seeks favourable current windows before a controlled southward approach.",
          ["ACC/current-assist planning window", "West of Prince Edward Islands", "Moderate ice exposure"]),
]


def base_document(scenario, conditions):
    return {
        "metadata": {
            "generated": "2024-01-15T10:00:00Z",
            "voyage_type": "India–Antarctica Research Expedition (hackathon planning demo)",
            "ship_type": "Ice-strengthened research vessel (assumed 1A ice class)",
            "season": "Austral summer (December–February)",
            "scenario": scenario,
            "data_sources": [
                "IMO Polar Code voyage-planning principles",
                "NSIDC sea-ice products (operational data required before sailing)",
                "British Antarctic Survey Southern Ocean/ACC background",
            ],
            "navigation_notice": "Demo waypoints only. Not for navigation; the master must use current ENCs, Notices to Mariners, ice charts, weather routing, SAR arrangements and vessel-specific Polar Water Operational Manual limits.",
        },
        "voyage_info": {
            "start": START,
            "end": END,
            "season": "December (Austral Summer)",
            "ice_conditions": conditions,
            "planned_distance_range_km": [10000, 12200],
            "ocean_regions": ["Indian Ocean", "Southern Ocean", "Antarctic waters"],
        },
        "navigation_environment": {
            "westerlies": "Persistent and often severe between 40°S and 60°S; weather routing retains a 2–3 day buffer.",
            "acc": "Predominantly eastward flow; local route benefit is conditional on nowcast/forecast and must not be assumed as a fixed 0.5–1.5 kn gain.",
            "ice_concentration_percent_by_latitude": {"40S_50S": "0–5", "50S_60S": "5–25", "60S_65S": "20–60", "65S_70S": "40–80; route only with current ice intelligence"},
            "fuel_basis": "Open ocean benchmark 5,500 L/day at 15 kn; ice benchmark 8,000 L/day at 10 kn; totals include manoeuvring, weather/ice allowances and 15% safety reserve.",
        },
        "hazard_zones": [
            {"name": "Prince Edward Islands / seamount clearance", "bounds": {"lat": [-48, -45], "lon": [34, 42]}, "risk": "Shallow-water and island-clearance constraint"},
            {"name": "Iceberg Alley monitoring sector", "bounds": {"lat": [-60, -55], "lon": [40, 60]}, "risk": "Elevated tabular-iceberg probability"},
            {"name": "Bouvet Island isolation hazard", "position": {"lat": -54.4, "lon": 3.4}, "risk": "Remote isolated land/limited shelter"},
        ],
    }


def scenario_zero():
    doc = base_document(0, "Favourable — near-minimum seasonal ice extent; routine satellite/radar monitoring still required.")
    doc["routes"] = copy.deepcopy(BASE_ROUTES)
    return doc


def scenario_one():
    doc = base_document(1, "Favourable overall; a newly detected tabular iceberg requires a monitored deviation on the direct option.")
    routes = copy.deepcopy(BASE_ROUTES)
    fastest = routes[1]
    fastest["waypoints"].insert(13, {"seq": 0, "lat": -58.6, "lon": 22.0, "label": "Deviation west of detected tabular iceberg"})
    fastest["waypoints"] = numbered([{k: v for k, v in point.items() if k != "seq"} for point in fastest["waypoints"]])
    fastest.update({"distance_km": 10850, "distance_nm": round(10850 / 1.852), "duration_days": 29, "fuel_liters": 176000, "risk_score": 52,
                    "description": "Direct route deviates around a newly detected tabular iceberg; risk remains elevated due to close iceberg-density exposure."})
    doc["routes"] = routes
    doc["detected_icebergs"] = [{"id": "TAB-2024-042", "position": {"lat": -58.5, "lon": 42.0}, "size_km": {"length": 2.5, "width": 1.8}, "drift": {"direction": "northwest", "speed_km_per_day": 1.2}, "impact": "Fastest route deviation required; safest and fuel-efficient options remain outside the alert buffer."}]
    return doc


def scenario_two():
    doc = base_document(2, "Deteriorating — storm avoidance and denser-than-forecast pack ice require route modifications.")
    routes = copy.deepcopy(BASE_ROUTES)
    adjustments = [(0, 150, 35, 190000, 20, "Minor eastern weather adjustment"), (1, 800, 31, 188000, 61, "Major westward storm/ice detour"), (2, 300, 32, 160000, 37, "Moderate current-route adjustment")]
    for index, extra_km, days, fuel, risk, note in adjustments:
        r = routes[index]
        r["distance_km"] += extra_km
        r["distance_nm"] = round(r["distance_km"] / 1.852)
        r["duration_days"], r["fuel_liters"], r["risk_score"] = days, fuel, risk
        r["description"] += f" {note}."
    routes[0]["waypoints"].insert(-5, {"seq": 0, "lat": -57.5, "lon": 18.0, "label": "Eastern storm-clearance adjustment"})
    routes[1]["waypoints"].insert(-6, {"seq": 0, "lat": -56.5, "lon": 18.0, "label": "Major westward storm-detour waypoint"})
    routes[2]["waypoints"].insert(-5, {"seq": 0, "lat": -58.0, "lon": 6.0, "label": "Current-route weather adjustment"})
    for r in routes:
        r["waypoints"] = numbered([{k: v for k, v in point.items() if k != "seq"} for point in r["waypoints"]])
    doc["routes"] = routes
    doc["hazard_zones"].extend([
        {"name": "Active Southern Ocean storm system", "bounds": {"lat": [-58, -52], "lon": [30, 50]}, "risk": "Avoid; severe sea-state and wind corridor"},
        {"name": "Unexpected dense pack ice", "bounds": {"lat": [-65, -60], "lon": [15, 35]}, "risk": "40–70% concentration; entry conditional on current imagery and vessel limits"},
        {"name": "Multiple iceberg reports", "bounds": {"lat": [-60, -55], "lon": [35, 55]}, "risk": "Elevated iceberg density; speed and visibility restrictions"},
    ])
    return doc


def scenario_three():
    doc = base_document(3, "Critical — calving-related iceberg field blocks the usual final approach; only the modified conservative route is viable.")
    safest = copy.deepcopy(BASE_ROUTES[0])
    safest["name"] = "Emergency Eastern Ice-Avoidance Route"
    safest.update({"distance_km": 12450, "distance_nm": round(12450 / 1.852), "duration_days": 36, "fuel_liters": 199000, "risk_score": 18,
                   "description": "Only viable demo option. Extended eastern approach, 72-hour ice-entry weather window and icebreaker escort are required for the final 150 km."})
    safest["waypoints"].insert(-3, {"seq": 0, "lat": -69.4, "lon": 16.0, "label": "Emergency eastern approach extension"})
    safest["waypoints"].insert(-2, {"seq": 0, "lat": -70.1, "lon": 14.2, "label": "Icebreaker escort rendezvous — final 150 km"})
    safest["waypoints"] = numbered([{k: v for k, v in point.items() if k != "seq"} for point in safest["waypoints"]])
    doc["routes"] = [safest]
    doc["blocked_routes"] = [
        {"type": "fastest", "status": "blocked", "reason": "Calving-related iceberg field blocks final approach."},
        {"type": "fuel_efficient", "status": "blocked", "reason": "Calving-related iceberg field blocks final approach."},
    ]
    doc["hazard_zones"].append({"name": "Critical Riiser-Larsen calving/iceberg field", "bounds": {"lat": [-71, -69.5], "lon": [0, 20]}, "risk": "No independent entry; escort and updated reconnaissance required"})
    doc["emergency_requirements"] = ["Icebreaker escort for final 150 km", "72-hour calm-weather window before ice entry", "Master/ice adviser reassessment immediately before final approach", "Contingency and SAR communications verified"]
    return doc


for scenario, factory in enumerate((scenario_zero, scenario_one, scenario_two, scenario_three)):
    target = OUT / f"routes_scenario_{scenario}.json"
    target.write_text(json.dumps(factory(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {target.name}")
