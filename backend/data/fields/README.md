# Field Boundaries GeoJSON Data

이 디렉토리에 필드 경계 GeoJSON 파일을 저장하세요.

## 파일 형식

각 필드는 개별 GeoJSON Feature 파일로 저장됩니다.

### 파일명 규칙
- `field-{id}.geojson` 형식으로 저장
- 예: `field-1.geojson`, `field-2.geojson`

### GeoJSON 구조

```json
{
  "type": "Feature",
  "id": "field-1",
  "properties": {
    "farmId": "farm-1",
    "cropId": "crop-1",
    "area": 25.5,
    "cropType": "Canola"
  },
  "geometry": {
    "type": "Polygon",
    "coordinates": [[
      [lng1, lat1],
      [lng2, lat2],
      [lng3, lat3],
      [lng4, lat4],
      [lng1, lat1]
    ]]
  }
}
```

### 필수 필드

- `id`: 필드 고유 ID (예: "field-1")
- `properties.farmId`: 농장 ID (예: "farm-1")
- `properties.cropId`: 작물 ID (예: "crop-1")
- `properties.area`: 필드 면적 (헥타르)
- `properties.cropType`: 작물 종류 (예: "Canola", "Timothy Hay")
- `geometry`: GeoJSON Geometry 객체 (Polygon 또는 MultiPolygon)

### 좌표 형식

- 좌표는 `[경도, 위도]` 형식입니다 (GeoJSON 표준)
- Polygon의 첫 번째와 마지막 좌표는 동일해야 합니다 (폐곡선)
- 좌표 순서는 시계 반대 방향(CCW) 또는 시계 방향(CW) 모두 가능합니다

## 예시 파일

- `field-1.geojson`: Hartland Colony (AB) - Canola 필드 1
- `field-2.geojson`: Hartland Colony (AB) - Canola 필드 2
- `field-3.geojson`: Exceedagro Reference Field (BC) - Timothy Hay 필드 1
- `field-4.geojson`: Exceedagro Reference Field (BC) - Timothy Hay 필드 2

## 사용 방법

1. 이 디렉토리에 새로운 GeoJSON 파일을 추가하거나
2. 기존 파일을 수정하여 필드 경계 데이터를 업데이트하세요
3. 백엔드 서버가 자동으로 이 파일들을 읽어서 API로 제공합니다

