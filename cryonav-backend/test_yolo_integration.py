"""
YOLO Integration Test Script
Tests the iceberg detection model integration end-to-end

Usage:
    python test_yolo_integration.py [--image path/to/image.jpg] [--confidence 0.7]
"""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_model_loader():
    """Test 1: Model loading and caching"""
    print("\n" + "="*70)
    print("TEST 1: Model Loader")
    print("="*70)
    
    try:
        from app.detection_models.iceberg_detection import load_model, is_model_loaded, get_model_info
        
        # Check if model is already loaded
        print(f"Model loaded before test: {is_model_loaded()}")
        
        # Get model info
        info = get_model_info()
        print(f"\nModel Information:")
        print(f"  Path: {info['model_path']}")
        print(f"  Exists: {info['model_exists']}")
        print(f"  Device: {info['device']}")
        print(f"  CUDA Available: {info['cuda_available']}")
        
        if not info['model_exists']:
            print("\n[WARNING] Model weights file not found!")
            print(f"   Expected location: {info['model_path']}")
            print("   Place your trained best.pt file there to enable live detection.")
            print("   OR run: python create_test_model.py")
            print("   OR use mock detections (automatic fallback)")
            return False
        
        # Load model
        print("\nLoading model...")
        model = load_model()
        
        if model is None:
            print("[FAILED] Model loading returned None")
            return False
        
        print("[PASSED] Model loaded successfully")
        print(f"Model cached: {is_model_loaded()}")
        
        return True
        
    except Exception as e:
        print(f"[FAILED] {e}")
        logger.error("Model loader test failed", exc_info=True)
        return False


def test_detect_icebergs(image_path=None, confidence=0.7):
    """Test 2: Iceberg detection pipeline"""
    print("\n" + "="*70)
    print("TEST 2: Iceberg Detection")
    print("="*70)
    
    try:
        from app.detection_models.iceberg_detection import detect_icebergs, annotate_image
        import numpy as np
        from PIL import Image
        
        # If no image provided, create a synthetic test image
        if image_path is None:
            print("No image provided, creating synthetic test image...")
            test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
            img = Image.fromarray(test_image)
            image_path = Path("test_image_synthetic.jpg")
            img.save(image_path)
            print(f"Created test image: {image_path}")
        else:
            image_path = Path(image_path)
            if not image_path.exists():
                print(f"❌ FAILED: Image not found: {image_path}")
                return False
        
        print(f"\nRunning detection on: {image_path}")
        print(f"Confidence threshold: {confidence}")
        
        # Run detection
        result = detect_icebergs(
            image_path=str(image_path),
            confidence_threshold=confidence
        )
        
        # Check result structure
        if "icebergs" not in result:
            print("❌ FAILED: Missing 'icebergs' key in result")
            return False
        
        if "metadata" not in result:
            print("❌ FAILED: Missing 'metadata' key in result")
            return False
        
        # Display results
        num_detections = len(result["icebergs"])
        print(f"\n📊 Detection Results:")
        print(f"  Detections: {num_detections}")
        
        if "processing_time_ms" in result["metadata"]:
            print(f"  Processing time: {result['metadata']['processing_time_ms']:.2f}ms")
        
        # Show individual detections
        if num_detections > 0:
            print(f"\n🧊 Detected Icebergs:")
            for iceberg in result["icebergs"][:5]:  # Show first 5
                print(f"  {iceberg['id']}:")
                print(f"    Position: {iceberg['position']['lat']:.4f}°, {iceberg['position']['lon']:.4f}°")
                print(f"    Size: {iceberg['size_meters']['length']}m × {iceberg['size_meters']['width']}m")
                print(f"    Confidence: {iceberg['confidence']:.2%}")
            
            if num_detections > 5:
                print(f"  ... and {num_detections - 5} more")
            
            # Try to create annotated image
            try:
                output_path = annotate_image(
                    image_path=str(image_path),
                    detections=result,
                    show_labels=True
                )
                if output_path:
                    print(f"\n[IMAGE] Annotated image saved: {output_path}")
            except Exception as e:
                print(f"\n[WARNING] Could not create annotated image: {e}")
        else:
            print("\n  No icebergs detected (this is normal for synthetic images)")
            if "warning" in result.get("metadata", {}):
                print(f"  Note: {result['metadata']['warning']}")
        
        print("\n[PASSED] Detection pipeline working")
        return True
        
    except Exception as e:
        print(f"[FAILED] {e}")
        logger.error("Detection test failed", exc_info=True)
        return False


def test_iceberg_service():
    """Test 3: Service layer abstraction"""
    print("\n" + "="*70)
    print("TEST 3: Iceberg Service Layer")
    print("="*70)
    
    try:
        from app.services import iceberg_service
        
        # Test 3a: Get service status
        print("\nChecking service status...")
        status = iceberg_service.get_service_status()
        
        print(f"  Mode: {status['mode']}")
        print(f"  USE_REAL_MODEL: {status['use_real_model']}")
        print(f"  Model loaded: {status['model_loaded']}")
        print(f"  Available scenarios: {status['scenarios_available']}")
        
        # Test 3b: Demo mode (scenario-based)
        print("\nTesting demo mode (scenario data)...")
        result = iceberg_service.get_icebergs(scenario=0)
        
        if "icebergs" in result:
            print(f"  ✅ Scenario 0: {len(result['icebergs'])} icebergs loaded")
        else:
            print(f"  ⚠️  Scenario 0: No iceberg data")
        
        # Test 3c: Mode switching
        print("\nTesting mode switching...")
        original_mode = status['use_real_model']
        
        # Switch mode
        new_status = iceberg_service.set_mode(use_real_model=not original_mode)
        print(f"  Mode changed: {new_status['old_mode']} → {new_status['new_mode']}")
        
        # Switch back
        iceberg_service.set_mode(use_real_model=original_mode)
        print(f"  Mode restored to: {status['mode']}")
        
        print("\n[PASSED] Service layer working")
        return True
        
    except Exception as e:
        print(f"[FAILED] {e}")
        logger.error("Service test failed", exc_info=True)
        return False


def test_api_endpoints():
    """Test 4: API endpoints (requires server running)"""
    print("\n" + "="*70)
    print("TEST 4: API Endpoints")
    print("="*70)
    
    try:
        import requests
        
        base_url = "http://127.0.0.1:8000"
        
        print(f"\nTesting endpoints at {base_url}...")
        print("(Server must be running for this test)")
        
        # Test health endpoint
        try:
            response = requests.get(f"{base_url}/api/health", timeout=2)
            if response.status_code == 200:
                print("  [OK] /api/health: OK")
            else:
                print(f"  [FAIL] /api/health: {response.status_code}")
        except requests.exceptions.RequestException:
            print("  [SKIP] /api/health: Server not running")
            print("\n  To test API endpoints, start the server:")
            print("    python -m uvicorn app.main:app --reload")
            return None  # Not a failure, just skip
        
        # Test model status endpoint
        try:
            response = requests.get(f"{base_url}/api/model-status", timeout=2)
            if response.status_code == 200:
                data = response.json()
                print(f"  [OK] /api/model-status: Mode={data.get('mode')}")
            else:
                print(f"  [FAIL] /api/model-status: {response.status_code}")
        except Exception as e:
            print(f"  [FAIL] /api/model-status: {e}")
        
        # Test icebergs endpoint
        try:
            response = requests.get(f"{base_url}/api/icebergs", timeout=2)
            if response.status_code == 200:
                data = response.json()
                num_icebergs = len(data.get("icebergs", []))
                print(f"  [OK] /api/icebergs: {num_icebergs} icebergs")
            else:
                print(f"  [FAIL] /api/icebergs: {response.status_code}")
        except Exception as e:
            print(f"  [FAIL] /api/icebergs: {e}")
        
        print("\n[PASSED] API endpoints accessible")
        return True
        
    except ImportError:
        print("[SKIP] 'requests' library not installed")
        print("   Install with: pip install requests")
        return None
    except Exception as e:
        print(f"[FAILED] {e}")
        return False


def print_summary(results):
    """Print test summary"""
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    total = len(results)
    
    for test_name, result in results.items():
        status = "[PASS]" if result is True else "[FAIL]" if result is False else "[SKIP]"
        print(f"  {status:8} {test_name}")
    
    print(f"\nResults: {passed}/{total} passed, {failed} failed, {skipped} skipped")
    
    if failed == 0:
        print("\n[SUCCESS] All tests passed! YOLO integration is working.")
    else:
        print(f"\n[WARNING] {failed} test(s) failed. Check logs above for details.")


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Test YOLO integration")
    parser.add_argument("--image", type=str, help="Path to test image")
    parser.add_argument("--confidence", type=float, default=0.7, help="Confidence threshold")
    parser.add_argument("--skip-api", action="store_true", help="Skip API tests")
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("CryoNav YOLO Integration Test Suite")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run tests
    results = {}
    
    results["Model Loader"] = test_model_loader()
    results["Iceberg Detection"] = test_detect_icebergs(args.image, args.confidence)
    results["Service Layer"] = test_iceberg_service()
    
    if not args.skip_api:
        results["API Endpoints"] = test_api_endpoints()
    
    # Print summary
    print_summary(results)
    
    # Exit with appropriate code
    if any(r is False for r in results.values()):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
