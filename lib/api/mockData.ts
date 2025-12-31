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

// Mock Farms - Real Canadian farm data
export const mockFarms: Farm[] = [
  {
    id: 'farm-1',
    name: 'Hartland Colony',
    location: { lat: 52.619167, lng: -113.092639 },  // 52°37'09.0"N, 113°05'33.5"W
    area: 250.5,
  },
  {
    id: 'farm-2',
    name: 'Exceedagro Reference Field',
    location: { lat: 54.0167, lng: -124.0167 },  // Vanderhoof, BC
    area: 180.3,
  },
];

// Mock Crops - Real Canadian crop data
export const mockCrops: Crop[] = [
  {
    id: 'crop-1',
    name: 'Canola',
    type: 'Oilseed',
    plantingDate: '2024-05-01',
    expectedHarvestDate: '2024-09-15',
  },
  {
    id: 'crop-2',
    name: 'Timothy Hay',
    type: 'Forage',
    plantingDate: '2024-04-15',
    expectedHarvestDate: '2024-07-20',
  },
];

// Generate mock field boundaries (GeoJSON polygons) - Real Canadian farm locations
export function generateMockFieldBoundaries(farmId: string, cropId: string): FieldBoundary[] {
  // Farm locations
  const farmLocations: Record<string, { lat: number; lng: number }> = {
    'farm-1': { lat: 52.619167, lng: -113.092639 },  // Hartland Colony, Alberta
    'farm-2': { lat: 54.0167, lng: -124.0167 },      // Exceedagro Reference Field, BC
  };

  // Crop types
  const cropTypes: Record<string, string> = {
    'crop-1': 'Canola',
    'crop-2': 'Timothy Hay',
  };

  const farmLocation = farmLocations[farmId] || { lat: 52.619167, lng: -113.092639 };
  const cropType = cropTypes[cropId] || 'Canola';
  const baseLat = farmLocation.lat;
  const baseLng = farmLocation.lng;
  
  // Generate 2-3 fields per farm/crop combination
  const numFields = 2 + Math.floor(Math.random() * 2);
  const fields: FieldBoundary[] = [];
  
  for (let i = 0; i < numFields; i++) {
    const offsetLat = (Math.random() - 0.5) * 0.02; // ~2km variation
    const offsetLng = (Math.random() - 0.5) * 0.02;
    
    const centerLat = baseLat + offsetLat;
    const centerLng = baseLng + offsetLng;
    
    // Create a rectangular field (approximately 500m x 500m)
    const fieldSize = 0.0045; // ~500m in degrees (approximate)
    
    fields.push({
      id: `field-${farmId}-${cropId}-${i + 1}`,
      farmId,
      cropId,
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [centerLng - fieldSize, centerLat - fieldSize],
          [centerLng + fieldSize, centerLat - fieldSize],
          [centerLng + fieldSize, centerLat + fieldSize],
          [centerLng - fieldSize, centerLat + fieldSize],
          [centerLng - fieldSize, centerLat - fieldSize],
        ]],
      },
      properties: {
        area: 20 + Math.random() * 20, // 20-40 hectares
        cropType: cropType,
      },
    });
  }
  
  return fields;
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
        north: 52.624167,  // Hartland Colony, Alberta
        south: 52.614167,
        east: -113.087639,
        west: -113.102639,
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
        north: 52.624167,  // Hartland Colony, Alberta
        south: 52.614167,
        east: -113.087639,
        west: -113.102639,
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

