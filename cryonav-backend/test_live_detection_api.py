"""
Quick API Test for Live Detection
Tests all endpoints to ensure everything works
"""

import requests
import time
from pathlib import Path
import sys

BASE_URL = "http://localhost:8000"

def test_endpoint(name, method, url, **kwargs):
    """Test a single endpoint"""
    try:
        print(f"\n[TEST] {name}")
        print(f"  {method} {url}")
        
        if method == "GET":
            response = requests.get(url, **kwargs)
        elif method == "POST":
            response = requests.post(url, **kwargs)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "icebergs" in data:
                print(f"  Result: {len(data['icebergs'])} icebergs detected")
            elif "mode" in data:
                print(f"  Mode: {data['mode']}, Model Loaded: {data.get('model_loaded', 'N/A')}")
            elif "message" in data:
                print(f"  Message: {data['message']}")
            print("  ✅ PASS")
            return True
        else:
            print(f"  ❌ FAIL: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"  ❌ FAIL: Server not running")
        print(f"     Start with: python -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        return False


def main():
    print("="*70)
    print("CryoNav Live Detection API Tests")
    print("="*70)
    
    tests = {
        "Health Check": ("GET", f"{BASE_URL}/api/health"),
        "Model Status": ("GET", f"{BASE_URL}/api/model-status"),
        "Demo Mode (Scenario 0)": ("GET", f"{BASE_URL}/api/icebergs"),
        "Demo Mode (Scenario 2)": ("GET", f"{BASE_URL}/api/icebergs?scenario=2"),
        "Enable Live Mode": ("POST", f"{BASE_URL}/api/model-mode?use_real_model=true"),
        "Check Status After Mode Change": ("GET", f"{BASE_URL}/api/model-status"),
    }
    
    results = {}
    for name, (method, url) in tests.items():
        results[name] = test_endpoint(name, method, url)
        time.sleep(0.5)  # Brief pause between requests
    
    # Test live detection if we have a test image
    test_image = Path("test_image_synthetic.jpg")
    if test_image.exists():
        print(f"\n[TEST] Live Detection (File Path)")
        print(f"  Using image: {test_image}")
        results["Live Detection"] = test_endpoint(
            "Live Detection",
            "GET",
            f"{BASE_URL}/api/icebergs-live",
            params={"image_path": str(test_image), "confidence": 0.7}
        )
    else:
        print(f"\n[SKIP] Live Detection - No test image found")
        print(f"  Create one with: python test_yolo_integration.py")
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}  {name}")
    
    print(f"\nResults: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 All API tests passed! Live detection is working!")
        print("\nNext steps:")
        print("1. Test frontend integration")
        print("2. Upload real satellite imagery")
        print("3. Replace test model with trained model")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
