/**
 * API client layer
 * In production, these functions would make actual HTTP requests
 * For MVP, they return mock data with simulated delays
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
  APIResponse,
  DashboardFilters,
} from '@/types';
import {
  mockFarms,
  mockCrops,
  generateMockFieldBoundaries,
  generateMockKPISummary,
  generateMockNDVIGrid,
  generateMockStressIndex,
  generateMockSoilMoisture,
  generateMockYieldPrediction,
  generateMockCarbonMetrics,
} from './mockData';

// Simulate API delay
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export class APIClient {
  private baseUrl: string;

  constructor(baseUrl: string = '/api') {
    this.baseUrl = baseUrl;
  }

  async getFarms(): Promise<APIResponse<Farm[]>> {
    await delay(300);
    return {
      data: mockFarms,
      timestamp: new Date().toISOString(),
      status: 'success',
    };
  }

  async getCrops(): Promise<APIResponse<Crop[]>> {
    await delay(300);
    return {
      data: mockCrops,
      timestamp: new Date().toISOString(),
      status: 'success',
    };
  }

  async getFieldBoundaries(
    farmId: string,
    cropId: string
  ): Promise<APIResponse<FieldBoundary[]>> {
    await delay(400);
    return {
      data: generateMockFieldBoundaries(farmId, cropId),
      timestamp: new Date().toISOString(),
      status: 'success',
    };
  }

  async getKPISummary(filters: DashboardFilters): Promise<APIResponse<KPISummary>> {
    await delay(200);
    return {
      data: generateMockKPISummary(),
      timestamp: new Date().toISOString(),
      status: 'success',
    };
  }

  async getNDVIGrid(fieldId: string): Promise<APIResponse<NDVIGrid>> {
    await delay(500);
    return {
      data: generateMockNDVIGrid(fieldId),
      timestamp: new Date().toISOString(),
      status: 'success',
    };
  }

  async getStressIndex(fieldId: string): Promise<APIResponse<StressIndex>> {
    await delay(500);
    return {
      data: generateMockStressIndex(fieldId),
      timestamp: new Date().toISOString(),
      status: 'success',
    };
  }

  async getSoilMoisture(
    fieldId: string,
    dateRange?: { start: string; end: string }
  ): Promise<APIResponse<SoilMoistureData[]>> {
    await delay(400);
    return {
      data: generateMockSoilMoisture(fieldId),
      timestamp: new Date().toISOString(),
      status: 'success',
    };
  }

  async getYieldPrediction(
    fieldId: string,
    dateRange?: { start: string; end: string }
  ): Promise<APIResponse<YieldPredictionData[]>> {
    await delay(400);
    return {
      data: generateMockYieldPrediction(fieldId),
      timestamp: new Date().toISOString(),
      status: 'success',
    };
  }

  async getCarbonMetrics(
    fieldId: string,
    dateRange?: { start: string; end: string }
  ): Promise<APIResponse<CarbonMetricsData[]>> {
    await delay(400);
    return {
      data: generateMockCarbonMetrics(fieldId),
      timestamp: new Date().toISOString(),
      status: 'success',
    };
  }
}

// Singleton instance
export const apiClient = new APIClient();

