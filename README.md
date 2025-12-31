# CropAgnoAI - Agriculture Analytics Dashboard

농업 분석 대시보드를 위한 웹 기반 플랫폼 MVP입니다. 위성 이미지, 날씨 데이터, 필드 경계를 기반으로 농업 인사이트를 시각화합니다.

## 기술 스택

- **Frontend**: Next.js 14 (App Router), TypeScript
- **UI**: Tailwind CSS + Headless UI
- **Maps**: Mapbox GL JS
- **Charts**: Recharts
- **State Management**: Zustand
- **Data Fetching**: API 기반 (현재는 Mock 데이터)

## 프로젝트 구조

``` bash
cropai/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # 루트 레이아웃
│   ├── page.tsx           # 메인 대시보드 페이지
│   └── globals.css        # 전역 스타일
├── components/
│   ├── dashboard/         # 대시보드 컴포넌트
│   │   ├── DashboardHeader.tsx
│   │   ├── KPISection.tsx
│   │   ├── KPICard.tsx
│   │   ├── FarmMap.tsx
│   │   ├── ChartsSection.tsx
│   │   ├── TimeSeriesChart.tsx
│   │   └── TimelineChart.tsx
│   └── ui/                # 재사용 가능한 UI 컴포넌트
│       └── Select.tsx
├── lib/
│   └── api/               # API 레이어
│       ├── client.ts      # API 클라이언트
│       └── mockData.ts    # Mock 데이터 생성기
├── store/                 # 상태 관리
│   └── dashboardStore.ts  # Zustand store
├── types/                 # TypeScript 타입 정의
│   └── index.ts
└── public/                # 정적 파일
```

## 아키텍처 원칙

### 1. Derived Data Only
- 프론트엔드는 백엔드 API에서 이미 처리된 데이터만 받습니다
- 원시 위성 이미지나 날씨 데이터를 직접 처리하지 않습니다
- 백엔드가 NDVI 그리드, 스트레스 인덱스, 시계열 배열, KPI 요약 값을 반환합니다

### 2. 계층 분리
- **UI Components**: 순수한 프레젠테이션 컴포넌트
- **Data Models**: TypeScript 인터페이스로 정의된 데이터 구조
- **API Layer**: 백엔드와의 통신을 담당하는 추상화 레이어
- **State Management**: Zustand를 통한 전역 상태 관리

### 3. 확장 가능한 구조
- 컴포넌트는 재사용 가능하도록 설계
- ML 모델이 개선되어도 프론트엔드 구조 변경 없이 동작
- 새로운 필드나 메트릭 추가가 용이

## 데이터 모델

### 핵심 타입

- `Farm`: 농장 메타데이터
- `Crop`: 작물 정보
- `FieldBoundary`: 필드 경계 (GeoJSON)
- `KPISummary`: KPI 요약 (생산성, 물 효율, ESG 정확도)
- `NDVIGrid`: NDVI 그리드 데이터
- `StressIndex`: 스트레스 인덱스 그리드
- `TimeSeriesData`: 시계열 데이터 (토양 수분, 수확 예측, 탄소 메트릭)

## 설치 및 실행

### 1. 프론트엔드 의존성 설치

``` bash
npm install
```

### 2. 백엔드 설정

백엔드 디렉토리로 이동하여 Python 가상환경을 설정하세요:

``` bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

`.env` 파일이 이미 생성되어 있으며 API 키가 설정되어 있습니다.

### 3. 환경 변수 설정

프론트엔드 루트 디렉토리에 `.env.local` 파일을 생성하세요:

``` env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Mapbox Token
NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token_here
```

### 4. 서버 실행

**백엔드 서버 실행** (터미널 1):
``` bash
cd backend
# Windows
run.bat
# 또는 Linux/Mac
./run.sh
# 또는 직접 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

백엔드 API는 `http://localhost:8000`에서 실행됩니다.

**프론트엔드 서버 실행** (터미널 2):
``` bash
npm run dev
```

브라우저에서 [http://localhost:3000](http://localhost:3000)을 열어 대시보드를 확인하세요.

### 5. API 문서 확인

백엔드 서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

상세한 API 문서는 [API.md](./API.md)를 참조하세요.

## 주요 기능

### 대시보드 구성 요소

1. **헤더 영역**
   - Farm 선택 드롭다운
   - Crop 선택 드롭다운

2. **KPI 카드**
   - 생산성 증가율
   - 물 효율
   - ESG 데이터 정확도

3. **중앙 맵 뷰**
   - 필드 경계 레이어
   - NDVI 히트맵 레이어 (토글 가능)
   - 스트레스 인덱스 히트맵 레이어 (토글 가능)

4. **우측 차트**
   - 토양 수분 (Soil Moisture)
   - 수확 예측 (Yield Prediction)
   - 탄소 메트릭 (Carbon Metrics)

5. **하단 타임라인 차트**
   - 트렌드 분석

## 데이터 흐름

```
Backend API → APIClient → Zustand Store → React Components
```

1. **API 호출**: `lib/api/client.ts`의 메서드들이 백엔드 API를 호출
2. **상태 업데이트**: Zustand store가 데이터를 저장하고 관리
3. **UI 렌더링**: React 컴포넌트가 store에서 데이터를 구독하여 렌더링

## API 문서

상세한 API 문서는 [API.md](./API.md)를 참조하세요.

주요 엔드포인트:
- `GET /api/farms` - 농장 목록
- `GET /api/crops` - 작물 목록
- `GET /api/fields?farm_id={id}&crop_id={id}` - 필드 경계
- `GET /api/kpi` - KPI 요약
- `GET /api/ndvi/{field_id}/grid` - NDVI 그리드
- `GET /api/stress/{field_id}` - 스트레스 인덱스

## 에러 처리

프론트엔드는 다음과 같은 에러를 처리합니다:
- **네트워크 오류**: 백엔드 서버 연결 실패
- **타임아웃**: 요청 시간 초과 (60초)
- **API 오류**: 백엔드에서 반환한 에러
- **검증 오류**: 잘못된 입력 파라미터

에러 발생 시 재시도 버튼이 표시되며, 자세한 정보는 "자세한 정보 보기"를 클릭하여 확인할 수 있습니다.

## 향후 개선 사항

- [x] 실제 백엔드 API 연동 ✅
- [x] NDVI/스트레스 히트맵 실제 렌더링 ✅
- [x] 에러 처리 및 로딩 상태 개선 ✅
- [ ] 날짜 범위 필터 추가
- [ ] 필드별 상세 정보 모달
- [ ] 데이터 내보내기 기능
- [ ] 반응형 디자인 개선

## 라이선스

MIT

