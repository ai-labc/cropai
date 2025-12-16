# CropAgnoAI 아키텍처 문서

## 개요

CropAgnoAI는 확장 가능한 농업 분석 대시보드 플랫폼입니다. 이 문서는 프로젝트의 아키텍처, 데이터 흐름, 그리고 주요 설계 결정을 설명합니다.

## 폴더 구조

```
cropai/
├── app/                          # Next.js App Router
│   ├── layout.tsx               # 루트 레이아웃 (메타데이터, 전역 스타일)
│   ├── page.tsx                 # 메인 대시보드 페이지
│   └── globals.css              # Tailwind CSS 및 전역 스타일
│
├── components/                    # React 컴포넌트
│   ├── dashboard/               # 대시보드 전용 컴포넌트
│   │   ├── DashboardHeader.tsx  # 헤더 (Farm/Crop 선택)
│   │   ├── KPISection.tsx       # KPI 카드 섹션
│   │   ├── KPICard.tsx          # 개별 KPI 카드
│   │   ├── FarmMap.tsx          # Mapbox 맵 컴포넌트
│   │   ├── ChartsSection.tsx    # 우측 차트 섹션
│   │   ├── TimeSeriesChart.tsx  # 재사용 가능한 시계열 차트
│   │   └── TimelineChart.tsx    # 하단 타임라인 차트
│   └── ui/                      # 재사용 가능한 UI 컴포넌트
│       └── Select.tsx           # 드롭다운 선택 컴포넌트
│
├── lib/                          # 유틸리티 및 라이브러리
│   └── api/                     # API 레이어
│       ├── client.ts            # API 클라이언트 (백엔드 통신)
│       └── mockData.ts          # Mock 데이터 생성기
│
├── store/                        # 상태 관리
│   └── dashboardStore.ts        # Zustand store (전역 상태)
│
├── types/                        # TypeScript 타입 정의
│   └── index.ts                 # 모든 타입 인터페이스
│
└── public/                       # 정적 파일 (이미지, 아이콘 등)
```

## 데이터 흐름

### 1. 초기화 흐름

```
페이지 로드
  ↓
DashboardHeader 컴포넌트 마운트
  ↓
initializeDashboard() 호출
  ↓
loadFarms() + loadCrops() 병렬 실행
  ↓
API 클라이언트가 Mock 데이터 반환
  ↓
Zustand store에 상태 저장
  ↓
자동으로 첫 번째 Farm/Crop 선택
  ↓
loadFieldBoundaries() 트리거
  ↓
필드 경계 로드 후 KPI 및 차트 데이터 로드
```

### 2. 필터 변경 흐름

```
사용자가 Farm/Crop 선택
  ↓
setSelectedFarm() / setSelectedCrop() 호출
  ↓
Zustand store 업데이트
  ↓
loadFieldBoundaries() 자동 트리거
  ↓
새로운 필드 경계 로드
  ↓
관련 데이터 (KPI, 차트) 자동 갱신
```

### 3. 맵 레이어 전환 흐름

```
사용자가 레이어 버튼 클릭 (Boundaries/NDVI/Stress)
  ↓
setActiveMapLayer() 호출
  ↓
FarmMap 컴포넌트가 레이어 변경 감지
  ↓
필요한 경우 loadNDVIGrid() / loadStressIndex() 호출
  ↓
맵에 레이어 렌더링 (현재는 Boundaries만 구현)
```

## 핵심 설계 원칙

### 1. Derived Data Only (파생 데이터만 처리)

프론트엔드는 백엔드에서 이미 처리된 데이터만 받습니다:

- ✅ **받는 것**: NDVI 그리드, 스트레스 인덱스, KPI 요약, 시계열 배열
- ❌ **받지 않는 것**: 원시 위성 이미지, 날씨 원시 데이터, 센서 원시 데이터

이렇게 하면:
- 프론트엔드가 가볍게 유지됨
- 백엔드에서 ML 모델 개선 시 프론트엔드 변경 불필요
- 데이터 처리 로직이 중앙화됨

### 2. 계층 분리 (Separation of Concerns)

```
┌─────────────────────────────────────┐
│   UI Components (Presentation)      │
│   - 순수한 렌더링 로직              │
│   - Props를 통한 데이터 수신        │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   State Management (Zustand)        │
│   - 전역 상태 관리                  │
│   - 비즈니스 로직                   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   API Layer (Abstraction)           │
│   - 백엔드 통신 추상화              │
│   - 에러 처리                        │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Data Models (TypeScript)          │
│   - 타입 안정성                     │
│   - 데이터 구조 정의                 │
└─────────────────────────────────────┘
```

### 3. 컴포넌트 재사용성

- `TimeSeriesChart`: 모든 시계열 차트에 재사용
- `KPICard`: 모든 KPI 메트릭에 재사용
- `Select`: 모든 드롭다운에 재사용

### 4. 확장 가능한 구조

새로운 기능 추가가 용이하도록 설계:

- **새 필드 추가**: `types/index.ts`에 타입 추가 → API 클라이언트에 메서드 추가 → 컴포넌트에서 사용
- **새 차트 추가**: `TimeSeriesChart` 재사용 또는 새 차트 컴포넌트 생성
- **새 레이어 추가**: `MapLayerType`에 타입 추가 → `FarmMap`에 렌더링 로직 추가

## 주요 타입 정의

### Farm & Crop
```typescript
interface Farm {
  id: string;
  name: string;
  location: { lat: number; lng: number };
  area: number; // hectares
}

interface Crop {
  id: string;
  name: string;
  type: string;
  plantingDate: string;
  expectedHarvestDate: string;
}
```

### Field Boundary (GeoJSON)
```typescript
interface FieldBoundary {
  id: string;
  farmId: string;
  cropId: string;
  geometry: {
    type: 'Polygon' | 'MultiPolygon';
    coordinates: number[][][] | number[][][][];
  };
  properties: {
    area: number;
    cropType: string;
  };
}
```

### KPI Summary
```typescript
interface KPISummary {
  productivityIncrease: number; // percentage
  waterEfficiency: number; // percentage
  esgAccuracy: number; // percentage (0-100)
  timestamp: string;
}
```

### Grid Data (NDVI, Stress)
```typescript
interface NDVIGrid {
  fieldId: string;
  timestamp: string;
  grid: {
    resolution: number; // meters per pixel
    bounds: { north, south, east, west };
    values: number[][]; // 2D array
  };
}
```

## API 클라이언트 패턴

모든 API 호출은 `APIClient` 클래스를 통해 이루어집니다:

```typescript
// 현재: Mock 데이터 반환
const response = await apiClient.getFarms();

// 향후: 실제 HTTP 요청으로 교체
// lib/api/client.ts에서만 수정하면 됨
```

이 패턴의 장점:
- Mock → Production 전환이 쉬움
- API 엔드포인트 변경 시 한 곳만 수정
- 테스트가 용이함

## 상태 관리 (Zustand)

Zustand를 선택한 이유:
- 간단하고 가벼움
- TypeScript 지원 우수
- Redux보다 보일러플레이트가 적음
- React Context보다 성능이 좋음

Store 구조:
- **State**: 모든 데이터와 UI 상태
- **Actions**: 데이터 로딩 및 상태 변경 함수
- **Selectors**: 컴포넌트에서 필요한 데이터만 선택

## 맵 구현 (Mapbox GL JS)

현재 구현:
- ✅ 필드 경계 레이어 (GeoJSON)
- ✅ 레이어 토글 UI
- ⚠️ NDVI/스트레스 히트맵 (UI만 구현, 실제 렌더링은 향후)

향후 개선:
- NDVI 그리드를 Mapbox 타일로 변환
- 스트레스 인덱스를 히트맵으로 렌더링
- 필드 클릭 시 상세 정보 표시

## 차트 구현 (Recharts)

`TimeSeriesChart` 컴포넌트는 모든 시계열 데이터에 재사용됩니다:
- 토양 수분
- 수확 예측
- 탄소 메트릭
- 타임라인 차트

커스터마이징:
- `color` prop으로 색상 변경
- `yAxisLabel`, `xAxisLabel`로 축 레이블 설정
- `dataKey`로 데이터 키 지정

## Mock 데이터 전략

현재 모든 데이터는 `lib/api/mockData.ts`에서 생성됩니다:
- 현실적인 범위의 값 생성
- 시계열 데이터는 시간에 따른 트렌드 포함
- GeoJSON 형식 준수

실제 백엔드 연동 시:
1. `lib/api/client.ts`의 메서드들을 실제 HTTP 요청으로 교체
2. `mockData.ts`는 개발/테스트용으로 유지

## 성능 고려사항

1. **지연 로딩**: 필요한 데이터만 로드 (예: NDVI는 해당 레이어 활성화 시에만)
2. **메모이제이션**: Zustand의 선택적 구독으로 불필요한 리렌더링 방지
3. **맵 최적화**: 필드 경계는 한 번만 렌더링, 레이어 전환 시 재사용

## 향후 확장 계획

### 단기
- [ ] 실제 백엔드 API 연동
- [ ] NDVI/스트레스 히트맵 실제 렌더링
- [ ] 날짜 범위 필터 추가

### 중기
- [ ] 필드별 상세 정보 모달
- [ ] 데이터 내보내기 (CSV, PDF)
- [ ] 알림 시스템 (임계값 초과 시)

### 장기
- [ ] 다중 농장 비교
- [ ] 예측 모델 시각화
- [ ] 모바일 반응형 최적화
- [ ] 실시간 데이터 스트리밍

## 보안 고려사항

현재 MVP 단계에서는:
- API 토큰은 환경 변수로 관리
- CORS 설정은 백엔드에서 처리
- 인증/인가는 향후 구현 예정

## 테스트 전략

권장 테스트 구조:
```
__tests__/
├── components/
│   ├── dashboard/
│   └── ui/
├── lib/
│   └── api/
└── store/
```

테스트 도구:
- Jest + React Testing Library (컴포넌트 테스트)
- MSW (Mock Service Worker) (API 모킹)

## 배포 고려사항

1. **환경 변수**: `.env.local` → `.env.production`
2. **빌드 최적화**: Next.js 자동 최적화 활용
3. **맵 토큰**: Mapbox 토큰은 클라이언트에 노출되므로 제한된 권한으로 설정

## 결론

이 아키텍처는:
- ✅ 확장 가능: 새로운 기능 추가가 용이
- ✅ 유지보수 가능: 명확한 계층 분리
- ✅ 테스트 가능: 각 레이어가 독립적
- ✅ 프로덕션 준비: 실제 백엔드 연동 시 구조 변경 최소화

