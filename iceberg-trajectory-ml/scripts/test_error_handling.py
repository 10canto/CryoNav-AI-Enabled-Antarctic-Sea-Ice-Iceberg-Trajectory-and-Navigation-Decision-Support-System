#!/usr/bin/env python3
"""Test error handling in ama8_inference."""

from ama8_inference import predict_iceberg_position
import numpy as np

print("\n" + "=" * 80)
print("TESTING ERROR HANDLING")
print("=" * 80)

# Test 1: NaN input
print("\n[TEST 1] NaN input (should raise ValueError)")
try:
    result = predict_iceberg_position(
        lat=-65,
        lon=np.nan,  # NaN!
        ocean_u=0.1,
        ocean_v=0.05,
        wind_u=-5,
        wind_v=3,
        siconc=0.3
    )
    print("✗ FAILED: Should have raised ValueError")
except ValueError as e:
    print(f"✓ PASSED: Caught ValueError: {e}")

# Test 2: None input
print("\n[TEST 2] None input (should raise ValueError)")
try:
    result = predict_iceberg_position(
        lat=-65,
        lon=0,
        ocean_u=None,  # None!
        ocean_v=0.05,
        wind_u=-5,
        wind_v=3,
        siconc=0.3
    )
    print("✗ FAILED: Should have raised ValueError")
except ValueError as e:
    print(f"✓ PASSED: Caught ValueError: {e}")

# Test 3: Valid inputs with extreme values
print("\n[TEST 3] Valid extreme values (should succeed)")
try:
    result = predict_iceberg_position(
        lat=-75,  # Southern limit
        lon=180,  # East edge
        ocean_u=1.0,  # Strong current
        ocean_v=-0.5,
        wind_u=20.0,  # Strong wind
        wind_v=-15.0,
        siconc=1.0  # Full ice cover
    )
    print(f"✓ PASSED: {result['predicted_lat']:.4f}°, {result['predicted_lon']:.4f}°")
    print(f"  Wrapped lon: {result['predicted_lon']:.4f}° (should be -180..180)")
except Exception as e:
    print(f"✗ FAILED: {e}")

# Test 4: Longitude wrapping
print("\n[TEST 4] Longitude wrapping (lon > 180)")
try:
    result = predict_iceberg_position(
        lat=-60,
        lon=179.5,  # Near date line
        ocean_u=0.5,
        ocean_v=0.0,
        wind_u=10.0,
        wind_v=0.0,
        siconc=0.0
    )
    print(f"✓ PASSED: Input lon=179.5° → Output lon={result['predicted_lon']:.4f}°")
    if -180 <= result['predicted_lon'] <= 180:
        print("  ✓ Longitude properly wrapped to [-180, 180]")
    else:
        print("  ✗ Longitude NOT properly wrapped!")
except Exception as e:
    print(f"✗ FAILED: {e}")

print("\n" + "=" * 80)
print("ERROR HANDLING TESTS COMPLETE")
print("=" * 80 + "\n")
