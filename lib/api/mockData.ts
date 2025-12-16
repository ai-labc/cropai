/**
 * Mock data generators for development
 * In production, these would be replaced with actual API calls
 */

import {
  Farm,
  Crop,
  FieldBoundary,
  KPISummary,
  NDVIGrid,
  StressIndex,
  SoilMoistureData,
  YieldPredictionData,
  CarbonMetricsData,
  TimeSeriesData,
} from '@/types';

// Mock Farms
export const mockFarms: Farm[] = [
  {
    id: 'farm-1',
    name: 'Green Valley Farm',
    location: { lat: 37.7749, lng: -122.4194 },
    area: 120.5,
  },
  {
    id: 'farm-2',
    name: 'Sunset Fields',
    location: { lat: 37.7849, lng: -122.4094 },
    area: 85.2,
  },
];

// Mock Crops
export const mockCrops: Crop[] = [
  {
    id: 'crop-1',
    name: 'Tomatoes',
    type: 'vegetable',
    plantingDate: '2024-03-15',
    expectedHarvestDate: '2024-07-20',
  },
  {
    id: 'crop-2',
    name: 'Corn',
    type: 'grain',
    plantingDate: '2024-04-01',
    expectedHarvestDate: '2024-09-15',
  },
  {
    id: 'crop-3',
    name: 'Wheat',
    type: 'grain',
    plantingDate: '2024-02-10',
    expectedHarvestDate: '2024-06-30',
  },
];

// Generate mock field boundaries (GeoJSON polygons)
export function generateMockFieldBoundaries(farmId: string, cropId: string): FieldBoundary[] {
  const baseLat = 37.7749;
  const baseLng = -122.4194;
  
  return [
    {
      id: 'field-1',
      farmId,
      cropId,
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [baseLng, baseLat],
          [baseLng + 0.01, baseLat],
          [baseLng + 0.01, baseLat + 0.01],
          [baseLng, baseLat + 0.01],
          [baseLng, baseLat],
        ]],
      },
      properties: {
        area: 25.5,
        cropType: 'Tomatoes',
      },
    },
    {
      id: 'field-2',
      farmId,
      cropId,
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [baseLng + 0.015, baseLat],
          [baseLng + 0.025, baseLat],
          [baseLng + 0.025, baseLat + 0.008],
          [baseLng + 0.015, baseLat + 0.008],
          [baseLng + 0.015, baseLat],
        ]],
      },
      properties: {
        area: 18.2,
        cropType: 'Tomatoes',
      },
    },
    {
      id: 'field-3',
      farmId,
      cropId,
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [baseLng, baseLat + 0.015],
          [baseLng + 0.012, baseLat + 0.015],
          [baseLng + 0.012, baseLat + 0.025],
          [baseLng, baseLat + 0.025],
          [baseLng, baseLat + 0.015],
        ]],
      },
      properties: {
        area: 22.8,
        cropType: 'Tomatoes',
      },
    },
  ];
}

// Generate mock KPI summary
export function generateMockKPISummary(): KPISummary {
  return {
    productivityIncrease: 20,
    waterEfficiency: 25,
    esgAccuracy: 92,
    timestamp: new Date().toISOString(),
  };
}

// Generate mock NDVI grid
export function generateMockNDVIGrid(fieldId: string): NDVIGrid {
  const gridSize = 20;
  const values: number[][] = [];
  
  for (let i = 0; i < gridSize; i++) {
    values[i] = [];
    for (let j = 0; j < gridSize; j++) {
      // Generate NDVI values between 0.2 and 0.9
      values[i][j] = 0.2 + Math.random() * 0.7;
    }
  }
  
  return {
    fieldId,
    timestamp: new Date().toISOString(),
    grid: {
      resolution: 10, // 10 meters per pixel
      bounds: {
        north: 37.7849,
        south: 37.7649,
        east: -122.4094,
        west: -122.4294,
      },
      values,
    },
  };
}

// Generate mock stress index
export function generateMockStressIndex(fieldId: string): StressIndex {
  const gridSize = 20;
  const values: number[][] = [];
  
  for (let i = 0; i < gridSize; i++) {
    values[i] = [];
    for (let j = 0; j < gridSize; j++) {
      // Generate stress values between 0 and 1 (lower is better)
      values[i][j] = Math.random() * 0.5;
    }
  }
  
  return {
    fieldId,
    timestamp: new Date().toISOString(),
    grid: {
      resolution: 10,
      bounds: {
        north: 37.7849,
        south: 37.7649,
        east: -122.4094,
        west: -122.4294,
      },
      values,
    },
  };
}

// Generate mock time series data
export function generateMockTimeSeries(
  days: number = 30,
  baseValue: number = 50,
  variance: number = 10
): TimeSeriesData[] {
  const data: TimeSeriesData[] = [];
  const now = new Date();
  
  for (let i = days; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    
    data.push({
      timestamp: date.toISOString(),
      value: baseValue + (Math.random() - 0.5) * variance,
    });
  }
  
  return data;
}

// Generate mock soil moisture data
export function generateMockSoilMoisture(fieldId: string): SoilMoistureData[] {
  return generateMockTimeSeries(30, 65, 15).map((item) => ({
    ...item,
    fieldId,
    depth: 20,
  }));
}

// Generate mock yield prediction data
export function generateMockYieldPrediction(fieldId: string): YieldPredictionData[] {
  const baseData = generateMockTimeSeries(30, 40, 8);
  return baseData.map((item, index) => ({
    ...item,
    fieldId,
    value: item.value + index * 0.5, // Upward trend
    confidence: 0.85 + Math.random() * 0.1,
  }));
}

// Generate mock carbon metrics data
export function generateMockCarbonMetrics(fieldId: string): CarbonMetricsData[] {
  return generateMockTimeSeries(30, 45, 12).map((item) => ({
    ...item,
    fieldId,
    metricType: 'sequestration' as const,
  }));
}

