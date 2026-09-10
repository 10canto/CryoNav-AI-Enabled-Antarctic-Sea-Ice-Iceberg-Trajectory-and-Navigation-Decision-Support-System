"""
Simple test script to verify all CryoNav API endpoints are working.
Run this after starting the server with: uvicorn app.main:app --reload
"""
import requests
import json
from time import sleep

BASE_URL = "http://localhost:8000"

def print_header(text):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def test_endpoint(method, endpoint, description):
    """Test an API endpoint and print results."""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n🔍 Testing: {description}")
    print(f"   {method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url)
        else:
            print("   ❌ Unsupported method")
            return False
        
        if response.status_code == 200:
            print(f"   ✅ Status: {response.status_code} OK")
            data = response.json()
            print(f"   📦 Response: {json.dumps(data, indent=6)[:200]}...")
            return True
        else:
            print(f"   ⚠️  Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except requests.exceptions.ConnectionError:
        print("   ❌ ERROR: Could not connect to server!")
        print("   Make sure the server is running: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        return False

def main():
    """Run all API tests."""
    print_header("🚢 CryoNav AI - API Test Suite")
    print("\nMake sure the server is running on http://localhost:8000")
    print("Start with: uvicorn app.main:app --reload")
    
    sleep(1)
    
    # Test all GET endpoints
    print_header("GET Endpoints")
    
    results = []
    results.append(test_endpoint("GET", "/api/health", "Health Check"))
    results.append(test_endpoint("GET", "/api/ice-analysis", "Ice Analysis Data"))
    results.append(test_endpoint("GET", "/api/icebergs", "Iceberg Detection"))
    results.append(test_endpoint("GET", "/api/predict-drift", "Drift Predictions (All)"))
    results.append(test_endpoint("GET", "/api/predict-drift?iceberg_id=ICE-047", "Drift Predictions (Filtered)"))
    results.append(test_endpoint("GET", "/api/routes", "Route Options"))
    results.append(test_endpoint("GET", "/api/risk-assessment", "Risk Assessment"))
    results.append(test_endpoint("GET", "/api/explanation", "Situation Explanation"))
    
    # Test POST endpoints
    print_header("POST Endpoints")
    
    results.append(test_endpoint("POST", "/api/advance-time", "Advance Time (Scenario +1)"))
    sleep(0.5)
    results.append(test_endpoint("GET", "/api/risk-assessment", "Risk Assessment (Scenario 1)"))
    
    sleep(0.5)
    results.append(test_endpoint("POST", "/api/advance-time", "Advance Time (Scenario +2)"))
    sleep(0.5)
    results.append(test_endpoint("GET", "/api/risk-assessment", "Risk Assessment (Scenario 2)"))
    
    sleep(0.5)
    results.append(test_endpoint("POST", "/api/reset-demo", "Reset Demo"))
    sleep(0.5)
    results.append(test_endpoint("GET", "/api/risk-assessment", "Risk Assessment (After Reset)"))
    
    # Summary
    print_header("Test Summary")
    passed = sum(results)
    total = len(results)
    
    print(f"\n✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! API is working perfectly!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
