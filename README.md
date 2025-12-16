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

### 1. 의존성 설치

``` bash
npm install
```

### 2. 환경 변수 설정

`.env.local` 파일을 생성하고 Mapbox 토큰을 추가하세요:

``` env
NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token_here
```

Mapbox 토큰은 [Mapbox](https://account.mapbox.com/)에서 무료로 발급받을 수 있습니다.

### 3. 개발 서버 실행

``` bash
npm run dev
```

브라우저에서 [http://localhost:3000](http://localhost:3000)을 열어 대시보드를 확인하세요.

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

## 향후 개선 사항

- [ ] 실제 백엔드 API 연동
- [ ] NDVI/스트레스 히트맵 실제 렌더링 (현재는 토글만 구현)
- [ ] 날짜 범위 필터 추가
- [ ] 필드별 상세 정보 모달
- [ ] 데이터 내보내기 기능
- [ ] 반응형 디자인 개선
- [ ] 에러 처리 및 로딩 상태 개선

## 라이선스

MIT

