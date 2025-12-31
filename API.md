# CropAgnoAI API 문서

## 개요

CropAgnoAI 백엔드 API는 FastAPI로 구현되었으며, 농업 데이터 분석을 위한 RESTful API를 제공합니다.

**Base URL**: `http://localhost:8000/api` (개발 환경)

**API 문서**: 
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 인증

현재 MVP에서는 인증이 필요하지 않습니다. 향후 JWT 토큰 기반 인증이 추가될 예정입니다.

## 공통 응답 형식

모든 API 응답은 다음 형식을 따릅니다:

```typescript
interface APIResponse<T> {
  data: T;
  timestamp: string;  // ISO 8601 형식
  status: 'success' | 'error';
  message?: string;  // 에러 시에만 제공
}
```

### 성공 응답 예시

```json
{
  "data": [...],
  "timestamp": "2024-01-01T00:00:00Z",
  "status": "success"
}
```

### 에러 응답 예시

```json
{
  "data": null,
  "timestamp": "2024-01-01T00:00:00Z",
  "status": "error",
  "message": "Farm not found"
}
```

## 엔드포인트

### 1. Farms (농장)

#### GET /api/farms

모든 농장 목록을 조회합니다.

**요청**:
```http
GET /api/farms
```

**응답**:
```json
{
  "data": [
    {
      "id": "farm-1",
      "name": "Hartland Colony",
      "location": {
        "lat": 52.619167,
        "lng": -113.092639
      },
      "area": 250.5
    }
  ],
  "timestamp": "2024-01-01T00:00:00Z",
  "status": "success"
}
```

#### GET /api/farms/{farm_id}

특정 농장 정보를 조회합니다.

**요청**:
```http
GET /api/farms/farm-1
```

**응답**: Farm 객체 (위와 동일)

**에러**:
- `404`: Farm not found

---

### 2. Crops (작물)

#### GET /api/crops

모든 작물 목록을 조회합니다.

**요청**:
```http
GET /api/crops
```

**응답**:
```json
{
  "data": [
    {
      "id": "crop-1",
      "name": "Canola",
      "type": "Oilseed",
      "plantingDate": "2024-05-01",
      "expectedHarvestDate": "2024-09-15"
    }
  ],
  "timestamp": "2024-01-01T00:00:00Z",
  "status": "success"
}
```

#### GET /api/crops/{crop_id}

특정 작물 정보를 조회합니다.

**요청**:
```http
GET /api/crops/crop-1
```

**응답**: Crop 객체 (위와 동일)

#### GET /api/crops/{crop_id}/metadata

FAO API에서 작물 메타데이터를 조회합니다.

**요청**:
```http
GET /api/crops/crop-1/metadata?crop_name=canola
```

**쿼리 파라미터**:
- `crop_name` (optional): 작물 이름 (소문자)

**응답**:
```json
{
  "data": {
    "item_code": "2547",
    "item_name": "Canola",
    "source": "FAO",
    ...
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "status": "success"
}
```

---

### 3. Fields (필드 경계)

#### GET /api/fields

농장과 작물에 해당하는 필드 경계를 조회합니다.

**요청**:
```http
GET /api/fields?farm_id=farm-1&crop_id=crop-1
```

**쿼리 파라미터**:
- `farm_id` (required): 농장 ID
- `crop_id` (required): 작물 ID

**응답**:
```json
{
  "data": [
    {
      "id": "field-1",
      "farmId": "farm-1",
      "cropId": "crop-1",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [-113.097639, 52.614167],
          [-113.087639, 52.614167],
          [-113.087639, 52.624167],
          [-113.097639, 52.624167],
          [-113.097639, 52.614167]
        ]]
      },
      "properties": {
        "area": 25.5,
        "cropType": "Canola"
      }
    }
  ],
  "timestamp": "2024-01-01T00:00:00Z",
  "status": "success"
}
```

**에러**:
- `400`: Missing required parameters (farm_id or crop_id)

#### POST /api/fields/upload

필드 경계 GeoJSON 파일을 업로드합니다.

**요청**:
```http
POST /api/fields/upload?farm_id=farm-1&crop_id=crop-1
Content-Type: multipart/form-data

file: <GeoJSON file>
```

**쿼리 파라미터**:
- `farm_id` (required): 농장 ID
- `crop_id` (required): 작물 ID

**응답**:
```json
{
  "message": "Field boundary uploaded successfully",
  "farmId": "farm-1",
  "cropId": "crop-1",
  "filename": "field-1.geojson"
}
```

**참고**: 현재는 업로드만 처리하며, 검증 및 저장 로직은 TODO 상태입니다.

---

### 4. KPI Summary

#### GET /api/kpi

KPI 요약 정보를 조회합니다. 실제 데이터(ERA5, ERA5-Land, Sentinel-2)를 기반으로 계산됩니다.

**요청**:
```http
GET /api/kpi?farm_id=farm-1&crop_id=crop-1&lat=52.619167&lng=-113.092639
```

**쿼리 파라미터**:
- `farm_id` (optional): 농장 ID
- `crop_id` (optional): 작물 ID
- `lat` (optional): 위도 (농장 위치 기반으로 자동 설정)
- `lng` (optional): 경도 (농장 위치 기반으로 자동 설정)
- `field_id` (optional): 필드 ID

**응답**:
```json
{
  "data": {
    "productivityIncrease": 20.0,
    "waterEfficiency": 25.0,
    "esgAccuracy": 92.0,
    "timestamp": "2024-01-01T00:00:00Z"
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "status": "success"
}
```

**계산 방식**:
- **Productivity Increase**: NDVI 추세 또는 날씨 데이터 기반 (기본값: 20%)
- **Water Efficiency**: 토양 수분 데이터 기반 (기본값: 25%)
- **ESG Accuracy**: 데이터 완성도 점수 (기본값: 92%)

**데이터 소스**:
- ERA5: 날씨 데이터 (온도 등)
- ERA5-Land: 토양 수분 데이터
- Sentinel-2: NDVI 타임라인 데이터 (선택적)

---

### 5. NDVI (식생 건강도)

#### GET /api/ndvi/{field_id}/grid

필드의 NDVI 그리드를 조회합니다.

**요청**:
```http
GET /api/ndvi/field-1/grid?date=2024-01-01
```

**경로 파라미터**:
- `field_id` (required): 필드 ID

**쿼리 파라미터**:
- `date` (optional): 특정 날짜 (YYYY-MM-DD). 없으면 최근 30일 내 데이터 사용

**응답**:
```json
{
  "data": {
    "fieldId": "field-1",
    "timestamp": "2024-01-01T00:00:00Z",
    "grid": {
      "resolution": 0.0001,
      "bounds": {
        "north": 52.624167,
        "south": 52.614167,
        "east": -113.087639,
        "west": -113.097639
      },
      "values": [[0.6, 0.7, ...], [0.65, 0.72, ...], ...]
    }
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "status": "success"
}
```

**에러**:
- `404`: Field geometry not found
- `400`: Invalid field geometry
- `500`: Error calculating NDVI grid

**데이터 소스**: Sentinel-2 (Copernicus Data Space API)

#### GET /api/ndvi/{field_id}/timeline

필드의 NDVI 타임라인을 조회합니다.

**요청**:
```http
GET /api/ndvi/field-1/timeline?date_start=2024-01-01&date_end=2024-01-31
```

**경로 파라미터**:
- `field_id` (required): 필드 ID

**쿼리 파라미터**:
- `date_start` (optional): 시작 날짜 (YYYY-MM-DD)
- `date_end` (optional): 종료 날짜 (YYYY-MM-DD)

**응답**:
```json
{
  "data": [
    {
      "date": "2024-01-01",
      "value": 0.65,
      "unit": "NDVI"
    },
    {
      "date": "2024-01-02",
      "value": 0.67,
      "unit": "NDVI"
    }
  ],
  "timestamp": "2024-01-01T00:00:00Z",
  "status": "success"
}
```

---

### 6. Stress Index (스트레스 지수)

#### GET /api/stress/{field_id}

필드의 스트레스 인덱스를 조회합니다.

**요청**:
```http
GET /api/stress/field-1?lat=52.619167&lng=-113.092639&crop_type=Canola
```

**경로 파라미터**:
- `field_id` (required): 필드 ID

**쿼리 파라미터**:
- `lat` (optional): 위도
- `lng` (optional): 경도
- `crop_type` (optional): 작물 종류

**응답**:
```json
{
  "data": {
    "fieldId": "field-1",
    "timestamp": "2024-01-01T00:00:00Z",
    "grid": {
      "resolution": 0.02,
      "bounds": {
        "north": 52.624167,
        "south": 52.614167,
        "east": -113.087639,
        "west": -113.097639
      },
      "values": [[0.3, 0.4, ...], [0.35, 0.45, ...], ...]
    }
  },
  "timestamp": "2024-01-01T00:00:00Z",
  "status": "success"
}
```

**계산 방식**: NDVI, 날씨 데이터, 토양 수분 데이터를 기반으로 규칙 기반 계산

---

### 7. Weather (날씨)

#### GET /api/weather

날씨 데이터를 조회합니다.

**요청**:
```http
GET /api/weather?lat=52.619167&lng=-113.092639&date_start=2024-01-01&date_end=2024-01-31
```

**쿼리 파라미터**:
- `lat` (required): 위도
- `lng` (required): 경도
- `date_start` (optional): 시작 날짜 (YYYY-MM-DD)
- `date_end` (optional): 종료 날짜 (YYYY-MM-DD)

**응답**:
```json
{
  "data": [
    {
      "date": "2024-01-01",
      "value": 15.5,
      "unit": "°C"
    }
  ],
  "timestamp": "2024-01-01T00:00:00Z",
  "status": "success"
}
```

**데이터 소스**: ERA5 (Copernicus Data Store)

---

### 8. Soil Moisture (토양 수분)

#### GET /api/soil/{field_id}

토양 수분 데이터를 조회합니다.

**요청**:
```http
GET /api/soil/field-1?lat=52.619167&lng=-113.092639&date_start=2024-01-01&date_end=2024-01-31
```

**경로 파라미터**:
- `field_id` (required): 필드 ID

**쿼리 파라미터**:
- `lat` (optional): 위도
- `lng` (optional): 경도
- `date_start` (optional): 시작 날짜 (YYYY-MM-DD)
- `date_end` (optional): 종료 날짜 (YYYY-MM-DD)

**응답**:
```json
{
  "data": [
    {
      "date": "2024-01-01",
      "value": 45.2,
      "unit": "%"
    }
  ],
  "timestamp": "2024-01-01T00:00:00Z",
  "status": "success"
}
```

**데이터 소스**: ERA5-Land (Copernicus Data Store)

---

## 에러 코드

| HTTP 상태 코드 | 의미 | 설명 |
|---------------|------|------|
| 200 | OK | 요청 성공 |
| 400 | Bad Request | 잘못된 요청 파라미터 |
| 404 | Not Found | 리소스를 찾을 수 없음 |
| 500 | Internal Server Error | 서버 내부 오류 |
| 503 | Service Unavailable | 외부 API 서비스 사용 불가 |

## 에러 응답 형식

```json
{
  "detail": "Error message here"
}
```

## 타임아웃

- 일반 API 요청: 60초
- NDVI 계산: 60초 (Sentinel-2 다운로드 포함)
- ERA5 데이터: 30초
- ERA5-Land 데이터: 30초

## 캐싱

백엔드는 SQLite를 사용하여 다음 데이터를 캐싱합니다:
- 날씨 데이터 (ERA5)
- 토양 수분 데이터 (ERA5-Land)
- NDVI 그리드 데이터

캐시는 자동으로 관리되며, 동일한 좌표와 날짜 범위에 대해서는 캐시된 데이터를 반환합니다.

## 환경 변수

백엔드 실행을 위해 다음 환경 변수가 필요합니다:

```env
# Copernicus Data Space API (Sentinel-2)
COPERNICUS_USERNAME=your_username
COPERNICUS_PASSWORD=your_password

# Copernicus Data Store API (ERA5, ERA5-Land)
CDS_URL=https://cds.climate.copernicus.eu/api/v2
CDS_KEY=your_cds_key

# FAO API (선택적)
FAO_API_BASE_URL=https://fenixservices.fao.org/faostat/api/v1/en

# CORS 설정
CORS_ORIGINS=http://localhost:3000,https://your-frontend-domain.com
```

## 데이터 소스

### 1. Sentinel-2 (Copernicus Data Space)
- **용도**: NDVI 계산
- **엔드포인트**: `https://catalogue.dataspace.copernicus.eu/odata/v1/Products`
- **인증**: Basic Auth (username/password)

### 2. ERA5 (Copernicus Data Store)
- **용도**: 날씨 데이터 (온도 등)
- **엔드포인트**: CDS API
- **인증**: API Key

### ERA5-Land (Copernicus Data Store)
- **용도**: 토양 수분 데이터
- **엔드포인트**: CDS API
- **인증**: API Key

### 3. FAO API
- **용도**: 작물 메타데이터
- **엔드포인트**: `https://fenixservices.fao.org/faostat/api/v1/en`
- **인증**: 없음 (공개 API)

## 제한 사항 (MVP)

1. **하드코딩된 데이터**: Farm, Crop, FieldBoundary는 현재 하드코딩된 샘플 데이터를 사용합니다.
2. **Mock 데이터 폴백**: 외부 API 실패 시 mock 데이터를 반환합니다.
3. **GeoJSON 업로드**: 업로드 엔드포인트는 있으나 검증 및 저장 로직은 미구현입니다.
4. **인증**: 현재 인증이 필요하지 않습니다.

## 향후 개선 사항

- [ ] 데이터베이스 연동 (PostgreSQL/SQLite)
- [ ] 사용자 인증 (JWT)
- [ ] GeoJSON 검증 및 저장
- [ ] 배치 처리 API
- [ ] 웹소켓 실시간 업데이트
- [ ] API Rate Limiting

