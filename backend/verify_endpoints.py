#!/usr/bin/env python3
"""
서버 엔드포인트 확인 스크립트
"""
import requests

base_url = "http://localhost:8000"

print("=== 서버 엔드포인트 확인 ===\n")

endpoints = [
    ("/api/kpi?farm_id=farm-1&crop_id=crop-1", "KPI"),
    ("/api/yield-prediction/field-1", "Yield Prediction"),
    ("/api/carbon-metrics/field-1", "Carbon Metrics"),
    ("/api/soil-moisture/field-1?lat=37.7799&lng=-122.4144", "Soil Moisture"),
]

for endpoint, name in endpoints:
    try:
        response = requests.get(f"{base_url}{endpoint}", timeout=5)
        if response.status_code == 200:
            print(f"[OK] {name}: Status {response.status_code}")
        else:
            print(f"[FAIL] {name}: Status {response.status_code} - {response.text[:50]}")
    except Exception as e:
        print(f"[FAIL] {name}: Error - {str(e)[:50]}")

print("\n=== OpenAPI 스키마 확인 ===")
try:
    response = requests.get(f"{base_url}/openapi.json", timeout=2)
    schema = response.json()
    paths = list(schema.get('paths', {}).keys())
    api_paths = [p for p in paths if '/api/' in p]
    
    print(f"등록된 API 경로: {len(api_paths)}개")
    kpi_exists = '/api/kpi' in paths
    yield_exists = any('yield' in p for p in paths)
    carbon_exists = any('carbon' in p for p in paths)
    
    print(f"  /api/kpi: {'[OK]' if kpi_exists else '[MISSING]'}")
    print(f"  /api/yield-prediction: {'[OK]' if yield_exists else '[MISSING]'}")
    print(f"  /api/carbon-metrics: {'[OK]' if carbon_exists else '[MISSING]'}")
except Exception as e:
    print(f"OpenAPI 확인 실패: {e}")

