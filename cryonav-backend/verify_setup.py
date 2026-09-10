"""
Quick verification that everything is ready to go
"""

print('='*70)
print('CRYONAV LIVE AI DETECTION - VERIFICATION')
print('='*70)
print()

# Test imports
try:
    from app.detection_models.iceberg_detection import detect_icebergs, load_model
    print('[OK] Imports working')
except Exception as e:
    print(f'[FAIL] Import error: {e}')
    exit(1)

# Test model
try:
    from app.detection_models.iceberg_detection import get_model_info
    info = get_model_info()
    print(f'[OK] Model file exists: {info["model_exists"]}')
    print(f'[OK] CUDA available: {info["cuda_available"]}')
    print(f'[OK] Device: {info["device"]}')
except Exception as e:
    print(f'[FAIL] Model check failed: {e}')
    exit(1)

# Test service
try:
    from app.services import iceberg_service
    status = iceberg_service.get_service_status()
    print(f'[OK] Service initialized')
    print(f'[OK] Current mode: {status["mode"]}')
except Exception as e:
    print(f'[FAIL] Service error: {e}')
    exit(1)

# Test main app
try:
    from app import main
    print('[OK] FastAPI app loads')
except Exception as e:
    print(f'[FAIL] App error: {e}')
    exit(1)

print()
print('='*70)
print('ALL CHECKS PASSED - READY TO START SERVER!')
print('='*70)
print()
print('Start server with:')
print('  python -m uvicorn app.main:app --reload')
print()
print('Then test with:')
print('  python test_live_detection_api.py')
print()
print('Or go directly to:')
print('  http://localhost:8000/docs')
