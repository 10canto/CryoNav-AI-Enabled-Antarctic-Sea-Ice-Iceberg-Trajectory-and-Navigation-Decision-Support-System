#!/usr/bin/env python3
"""
Test backend integration scenario.
Simulates how a backend API would call the inference function.
"""

import json
from ama8_inference import predict_iceberg_position

print("\n" + "=" * 80)
print("BACKEND INTEGRATION TEST")
print("=" * 80)

# Simulate receiving data from API request
api_request = {
    "iceberg_id": "B17A",
    "current_position": {
        "lat": -60.5,
        "lon": 30.2
    },
    "forcing_data": {
        "ocean_u": 0.25,
        "ocean_v": 0.08,
        "wind_u": 7.5,
        "wind_v": -4.2,
        "siconc": 0.15,
        "ice_u": 0.02,
        "ice_v": 0.01
    },
    "forecast_hours": 24
}

print("\n[1] Simulated API Request:")
print(json.dumps(api_request, indent=2))

# Call inference function
print("\n[2] Calling prediction function...")
try:
    result = predict_iceberg_position(
        lat=api_request["current_position"]["lat"],
        lon=api_request["current_position"]["lon"],
        ocean_u=api_request["forcing_data"]["ocean_u"],
        ocean_v=api_request["forcing_data"]["ocean_v"],
        wind_u=api_request["forcing_data"]["wind_u"],
        wind_v=api_request["forcing_data"]["wind_v"],
        siconc=api_request["forcing_data"]["siconc"],
        ice_u=api_request["forcing_data"]["ice_u"],
        ice_v=api_request["forcing_data"]["ice_v"],
        dt_hours=api_request["forecast_hours"]
    )
    
    print("✓ Prediction successful")
    
    # Build API response
    api_response = {
        "iceberg_id": api_request["iceberg_id"],
        "forecast": {
            "predicted_position": {
                "lat": result["predicted_lat"],
                "lon": result["predicted_lon"]
            },
            "uncertainty": {
                "radius_km": result["uncertainty_radius_km"],
                "percentile": 90
            },
            "drift": {
                "speed_kmd": result["predicted_speed_kmd"],
                "category": result["speed_category"]
            },
            "metadata": {
                "horizon_hours": result["horizon_hours"],
                "model_version": result["model_version"]
            }
        }
    }
    
    if "warning" in result:
        api_response["forecast"]["warning"] = result["warning"]
    
    print("\n[3] API Response:")
    print(json.dumps(api_response, indent=2))
    
    # Validate response structure
    print("\n[4] Validating response structure...")
    assert "iceberg_id" in api_response
    assert "forecast" in api_response
    assert "predicted_position" in api_response["forecast"]
    assert "lat" in api_response["forecast"]["predicted_position"]
    assert "lon" in api_response["forecast"]["predicted_position"]
    assert "uncertainty" in api_response["forecast"]
    assert "drift" in api_response["forecast"]
    print("✓ Response structure valid")
    
    # Check values are reasonable
    print("\n[5] Checking output values...")
    pred_lat = api_response["forecast"]["predicted_position"]["lat"]
    pred_lon = api_response["forecast"]["predicted_position"]["lon"]
    uncertainty = api_response["forecast"]["uncertainty"]["radius_km"]
    speed = api_response["forecast"]["drift"]["speed_kmd"]
    
    assert -90 <= pred_lat <= 90, f"Invalid latitude: {pred_lat}"
    assert -180 <= pred_lon <= 180, f"Invalid longitude: {pred_lon}"
    assert uncertainty > 0, f"Invalid uncertainty: {uncertainty}"
    assert speed >= 0, f"Invalid speed: {speed}"
    print(f"✓ Predicted position: {pred_lat:.4f}°, {pred_lon:.4f}°")
    print(f"✓ Uncertainty: {uncertainty:.2f} km")
    print(f"✓ Speed: {speed:.2f} km/day ({api_response['forecast']['drift']['category']})")
    
    # Distance check
    import math
    dlat = pred_lat - api_request["current_position"]["lat"]
    dlon = pred_lon - api_request["current_position"]["lon"]
    distance_km = math.sqrt(
        (dlat * 111)**2 + 
        (dlon * 111 * math.cos(math.radians(pred_lat)))**2
    )
    print(f"✓ Drift distance: {distance_km:.2f} km in 24 hours")
    
    print("\n" + "=" * 80)
    print("✓ BACKEND INTEGRATION TEST PASSED")
    print("=" * 80 + "\n")
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    print("\n" + "=" * 80)
    print("✗ BACKEND INTEGRATION TEST FAILED")
    print("=" * 80 + "\n")
