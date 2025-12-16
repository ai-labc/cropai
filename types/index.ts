/**
 * Core data models for CropAgnoAI platform
 * All data is assumed to be derived/processed from backend APIs
 */

// Farm and Crop metadata
export interface Farm {
  id: string;
  name: string;
  location: {
    lat: number;
    lng: number;
  };
  area: number; // hectares
}

export interface Crop {
  id: string;
  name: string;
  type: string;
  plantingDate: string;
  expectedHarvestDate: string;
}

// Field boundary (GeoJSON format)
export interface FieldBoundary {
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

// KPI Summary (derived from backend analysis)
export interface KPISummary {
  productivityIncrease: number; // percentage
  waterEfficiency: number; // percentage
  esgAccuracy: number; // percentage (0-100)
  timestamp: string;
}

// NDVI Grid (derived from satellite imagery)
export interface NDVIGrid {
  fieldId: string;
  timestamp: string;
  grid: {
    resolution: number; // meters per pixel
    bounds: {
      north: number;
      south: number;
      east: number;
      west: number;
    };
    values: number[][]; // 2D array of NDVI values (-1 to 1)
  };
}

// Stress Index (derived from weather + satellite data)
export interface StressIndex {
  fieldId: string;
  timestamp: string;
  grid: {
    resolution: number;
    bounds: {
      north: number;
      south: number;
      east: number;
      west: number;
    };
    values: number[][]; // 2D array of stress values (0-1)
  };
}

// Time series data for charts
export interface TimeSeriesData {
  timestamp: string;
  value: number;
}

export interface SoilMoistureData extends TimeSeriesData {
  fieldId: string;
  depth?: number; // cm
}

export interface YieldPredictionData extends TimeSeriesData {
  fieldId: string;
  confidence?: number; // 0-1
}

export interface CarbonMetricsData extends TimeSeriesData {
  fieldId: string;
  metricType: 'sequestration' | 'emission' | 'net';
}

// API Response types
export interface APIResponse<T> {
  data: T;
  timestamp: string;
  status: 'success' | 'error';
  message?: string;
}

// Dashboard filters
export interface DashboardFilters {
  farmId: string | null;
  cropId: string | null;
  dateRange: {
    start: string;
    end: string;
  } | null;
}

// Map layer configuration
export type MapLayerType = 'boundaries' | 'ndvi' | 'stress' | 'none';

