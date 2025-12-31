#!/usr/bin/env python3
"""
서버 상태 확인 스크립트
"""
import requests
import json

base_url = "http://localhost:8000"

print("=== 서버 상태 확인 ===\n")

# Health check
try:
    response = requests.get(f"{base_url}/health", timeout=2)
    print(f"[OK] Health check: {response.status_code} - {response.json()}")
except Exception as e:
    print(f"[FAIL] Health check failed: {e}")
    exit(1)

# OpenAPI schema 확인
try:
    response = requests.get(f"{base_url}/openapi.json", timeout=2)
    schema = response.json()
    paths = list(schema.get('paths', {}).keys())
    api_paths = [p for p in paths if '/api/' in p]
    
    print(f"\n=== 등록된 API 경로 ({len(api_paths)}개) ===")
    for path in sorted(api_paths):
        print(f"  {path}")
    
    # 새 엔드포인트 확인
    print("\n=== 새 엔드포인트 확인 ===")
    kpi_exists = any('kpi' in p for p in paths)
    yield_exists = any('yield' in p for p in paths)
    carbon_exists = any('carbon' in p for p in paths)
    
    print(f"  /api/kpi: {'[OK]' if kpi_exists else '[MISSING]'}")
    print(f"  /api/yield-prediction: {'[OK]' if yield_exists else '[MISSING]'}")
    print(f"  /api/carbon-metrics: {'[OK]' if carbon_exists else '[MISSING]'}")
    
    if not (kpi_exists and yield_exists and carbon_exists):
        print("\n[WARNING] 새 엔드포인트가 등록되지 않았습니다!")
        print("   서버를 재시작하세요.")
    
except Exception as e:
    print(f"✗ OpenAPI schema 확인 실패: {e}")

# 실제 엔드포인트 테스트
print("\n=== 엔드포인트 테스트 ===")
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
            print(f"  [OK] {name}: OK")
        else:
            print(f"  [FAIL] {name}: {response.status_code} - {response.text[:50]}")
    except Exception as e:
        print(f"  [FAIL] {name}: Error - {str(e)[:50]}")

