#!/usr/bin/env python3
"""Test importing ama8_inference as a module."""

from ama8_inference import predict_iceberg_position

# Test import
result = predict_iceberg_position(
    lat=-65,
    lon=0,
    ocean_u=0.1,
    ocean_v=0.05,
    wind_u=-5,
    wind_v=3,
    siconc=0.3
)

print("✓ Import test OK")
print(f"✓ Predicted position: {result['predicted_lat']:.4f}°, {result['predicted_lon']:.4f}°")
print(f"✓ Uncertainty radius: {result['uncertainty_radius_km']:.2f} km")
print(f"✓ Speed category: {result['speed_category']}")
print(f"✓ Model version: {result['model_version']}")
