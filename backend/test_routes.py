#!/usr/bin/env python3
"""
라우터 등록 테스트 스크립트
"""
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

print("=== 라우터 등록 테스트 ===\n")

# 모든 라우트 확인
routes = [r.path for r in app.routes if hasattr(r, 'path')]
api_routes = [r for r in routes if '/api/' in r]
print(f"총 API 라우트: {len(api_routes)}")
print("\n등록된 API 라우트:")
for route in sorted(api_routes):
    print(f"  {route}")

# 새 엔드포인트 테스트
print("\n=== 새 엔드포인트 테스트 ===")
endpoints = [
    ("/api/kpi?farm_id=farm-1&crop_id=crop-1", "KPI"),
    ("/api/yield-prediction/field-1", "Yield Prediction"),
    ("/api/carbon-metrics/field-1", "Carbon Metrics"),
    ("/api/soil-moisture/field-1?lat=37.7799&lng=-122.4144", "Soil Moisture"),
]

for endpoint, name in endpoints:
    try:
        response = client.get(endpoint)
        if response.status_code == 200:
            print(f"  [OK] {name}: OK")
        else:
            print(f"  [FAIL] {name}: {response.status_code} - {response.text[:50]}")
    except Exception as e:
        print(f"  [FAIL] {name}: Error - {str(e)[:50]}")

