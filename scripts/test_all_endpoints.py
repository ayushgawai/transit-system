"""
Test all API endpoints
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, params=None, data=None):
    """Test an API endpoint"""
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", params=params, timeout=10)
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=10)
        else:
            return False, f"Unsupported method: {method}"
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, dict) and result.get('success', True):
                return True, result
            else:
                return False, f"Response indicates failure: {result}"
        else:
            return False, f"HTTP {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 80)
    print("API ENDPOINT TESTING")
    print("=" * 80)
    print()
    
    endpoints = [
        ("GET", "/api/kpis", {"agency": "BART"}),
        ("GET", "/api/kpis", {"agency": "VTA"}),
        ("GET", "/api/routes", {"agency": "BART"}),
        ("GET", "/api/routes", {"agency": "VTA"}),
        ("GET", "/api/stops", {"agency": "BART"}),
        ("GET", "/api/stops", {"agency": "VTA"}),
        ("GET", "/api/live-data", {}),
        ("GET", "/api/analytics/route-health", {"agency": "BART"}),
        ("GET", "/api/analytics/route-comparison", {}),
        ("GET", "/api/analytics/delay-analysis", {}),
        ("GET", "/api/analytics/utilization-distribution", {}),
        ("GET", "/api/hourly-demand", {"agency": "BART"}),
        ("GET", "/api/hourly-demand", {"agency": "VTA"}),
        ("GET", "/api/hourly-heatmap", {}),
        ("GET", "/api/forecasts/demand", {"hours": 6}),
        ("GET", "/api/forecasts/delay", {}),
        ("GET", "/api/admin/status", {}),
    ]
    
    results = []
    for method, endpoint, params in endpoints:
        print(f"Testing {method} {endpoint}...", end=" ")
        success, result = test_endpoint(method, endpoint, params)
        if success:
            print("✅ PASS")
            results.append((endpoint, True, "OK"))
        else:
            print(f"❌ FAIL: {result}")
            results.append((endpoint, False, str(result)))
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed < total:
        print("\nFailed endpoints:")
        for endpoint, success, error in results:
            if not success:
                print(f"  ❌ {endpoint}: {error}")
    
    return passed == total

if __name__ == "__main__":
    main()

