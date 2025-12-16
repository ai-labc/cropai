# 프로젝트 구조 요약

## 생성된 파일 목록

### 설정 파일
- `package.json` - 프로젝트 의존성 및 스크립트
- `tsconfig.json` - TypeScript 설정
- `next.config.js` - Next.js 설정 (Mapbox 웹팩 설정 포함)
- `tailwind.config.js` - Tailwind CSS 설정
- `postcss.config.js` - PostCSS 설정
- `.gitignore` - Git 무시 파일

### 앱 구조 (Next.js App Router)
- `app/layout.tsx` - 루트 레이아웃
- `app/page.tsx` - 메인 대시보드 페이지
- `app/globals.css` - 전역 스타일

### 타입 정의
- `types/index.ts` - 모든 TypeScript 인터페이스

### API 레이어
- `lib/api/client.ts` - API 클라이언트 (현재 Mock)
- `lib/api/mockData.ts` - Mock 데이터 생성기

### 상태 관리
- `store/dashboardStore.ts` - Zustand store

### 컴포넌트
#### UI 컴포넌트
- `components/ui/Select.tsx` - 재사용 가능한 드롭다운

#### 대시보드 컴포넌트
- `components/dashboard/DashboardHeader.tsx` - 헤더 및 필터
- `components/dashboard/KPISection.tsx` - KPI 카드 섹션
- `components/dashboard/KPICard.tsx` - 개별 KPI 카드
- `components/dashboard/FarmMap.tsx` - Mapbox 맵 컴포넌트
- `components/dashboard/ChartsSection.tsx` - 우측 차트 섹션
- `components/dashboard/TimeSeriesChart.tsx` - 재사용 가능한 시계열 차트
- `components/dashboard/TimelineChart.tsx` - 하단 타임라인 차트

### 문서
- `README.md` - 프로젝트 개요 및 사용법
- `ARCHITECTURE.md` - 상세 아키텍처 문서
- `PROJECT_STRUCTURE.md` - 이 파일

## 데이터 흐름 예시

### 1. 페이지 로드 시
```
app/page.tsx
  → DashboardHeader (초기화)
  → initializeDashboard()
  → loadFarms() + loadCrops()
  → apiClient.getFarms() / getCrops()
  → Mock 데이터 반환
  → Zustand store 업데이트
  → 자동으로 첫 번째 Farm/Crop 선택
  → loadFieldBoundaries()
  → 필드 경계 로드
  → KPI 및 차트 데이터 로드
```

### 2. Farm 선택 시
```
Select 컴포넌트 onChange
  → setSelectedFarm()
  → Zustand store 업데이트
  → loadFieldBoundaries() 자동 트리거
  → 새로운 필드 경계 로드
  → 관련 데이터 자동 갱신
```

### 3. 맵 레이어 전환 시
```
레이어 버튼 클릭
  → setActiveMapLayer()
  → FarmMap 컴포넌트 감지
  → 필요 시 loadNDVIGrid() / loadStressIndex()
  → 맵 레이어 업데이트
```

## 주요 의존성

### 프로덕션
- `next` - Next.js 프레임워크
- `react` / `react-dom` - React 라이브러리
- `zustand` - 상태 관리
- `recharts` - 차트 라이브러리
- `mapbox-gl` - 맵 라이브러리
- `@headlessui/react` - UI 컴포넌트
- `@heroicons/react` - 아이콘
- `date-fns` - 날짜 처리
- `clsx` - 클래스명 유틸리티

### 개발
- `typescript` - TypeScript
- `tailwindcss` - CSS 프레임워크
- `postcss` / `autoprefixer` - CSS 처리
- `eslint` - 린터

## 다음 단계

1. **의존성 설치**
   ```bash
   npm install
   ```

2. **환경 변수 설정**
   - `.env.local` 파일 생성
   - `NEXT_PUBLIC_MAPBOX_TOKEN` 추가

3. **개발 서버 실행**
   ```bash
   npm run dev
   ```

4. **실제 백엔드 연동**
   - `lib/api/client.ts`의 메서드들을 실제 HTTP 요청으로 교체
   - API 엔드포인트 URL 설정

5. **NDVI/스트레스 히트맵 구현**
   - `components/dashboard/FarmMap.tsx`에 히트맵 렌더링 로직 추가
   - Mapbox 타일 서버 또는 Canvas 기반 렌더링

## 컴포넌트 사용 예시

### KPI 카드
```tsx
<KPICard
  title="PRODUCTIVITY INCREASE"
  value={20}
  trend="up"
/>
```

### 시계열 차트
```tsx
<TimeSeriesChart
  title="SOIL MOISTURE"
  data={soilMoistureData}
  yAxisLabel="%"
  xAxisLabel="Last 30 days"
  color="#3b82f6"
/>
```

### 맵
```tsx
<FarmMap
  fieldBoundaries={fieldBoundaries}
  ndviGrids={ndviGrids}
  stressIndices={stressIndices}
  activeLayer="boundaries"
/>
```

## 확장 가이드

### 새 필드 추가
1. `types/index.ts`에 타입 정의
2. `lib/api/mockData.ts`에 Mock 데이터 생성 함수 추가
3. `lib/api/client.ts`에 API 메서드 추가
4. `store/dashboardStore.ts`에 상태 및 액션 추가
5. 컴포넌트에서 사용

### 새 차트 추가
1. `TimeSeriesChart` 재사용 또는 새 컴포넌트 생성
2. `ChartsSection` 또는 새 섹션에 추가
3. Store에서 데이터 구독

### 새 맵 레이어 추가
1. `types/index.ts`의 `MapLayerType`에 타입 추가
2. `FarmMap` 컴포넌트에 렌더링 로직 추가
3. Store에 데이터 로딩 로직 추가

