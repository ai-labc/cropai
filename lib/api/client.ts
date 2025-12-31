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
  TimeSeriesData,
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
import { APICache } from './cache';

// Simulate API delay (for fallback)
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export class APIClient {
  private baseUrl: string;
  private useMock: boolean;

  constructor(baseUrl?: string) {
    // Use environment variable or default to localhost:8000
    const envApiUrl = process.env.NEXT_PUBLIC_API_URL;
    this.baseUrl = baseUrl || envApiUrl || 'http://localhost:8000/api';
    // Use mock data only if explicitly set to 'true', otherwise use real API
    this.useMock = process.env.NEXT_PUBLIC_USE_MOCK === 'true';
    
    if (!this.useMock) {
      console.log(`[APIClient] Using backend API: ${this.baseUrl}`);
    } else {
      console.log('[APIClient] Using mock data');
    }
  }

  private async fetchAPI<T>(endpoint: string, options?: RequestInit, useCache: boolean = true): Promise<APIResponse<T>> {
    if (this.useMock) {
      // Fallback to mock data
      await delay(300);
      throw new Error('Using mock data - backend not configured');
    }

    // Check cache first (for GET requests only)
    if (useCache && (!options || !options.method || options.method === 'GET')) {
      const cached = APICache.get<APIResponse<T>>(endpoint);
      if (cached) {
        return cached;
      }
    }

    try {
      const url = `${this.baseUrl}${endpoint}`;
      
      // Add timeout to fetch requests (60 seconds for slow APIs like ERA5)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        controller.abort();
      }, 60000);
      
      try {
        const response = await fetch(url, {
          ...options,
          signal: controller.signal,
          headers: {
            'Content-Type': 'application/json',
            ...options?.headers,
          },
        });
        
        clearTimeout(timeoutId);

        if (!response.ok) {
          const errorText = await response.text();
          console.error(`[APIClient] Request failed: ${endpoint} - ${response.status} ${response.statusText}`);
          throw new Error(`API error: ${response.status} ${response.statusText} - ${errorText}`);
        }

        const data = await response.json();
        
        // Cache successful responses (for GET requests only)
        if (useCache && (!options || !options.method || options.method === 'GET')) {
          APICache.set(endpoint, data);
        }
        
        return data;
      } catch (fetchError) {
        clearTimeout(timeoutId);
        if (fetchError instanceof Error && fetchError.name === 'AbortError') {
          const timeoutError = new Error(`Request timeout after 60s: ${endpoint}`);
          (timeoutError as any).errorType = 'timeout';
          throw timeoutError;
        }
        throw fetchError;
      }
    } catch (error) {
      if (error instanceof Error) {
        // Network errors
        if (error.name === 'AbortError' || error.message.includes('timeout')) {
          const timeoutError = new Error(`요청 시간이 초과되었습니다. 네트워크 연결을 확인해주세요. (${endpoint})`);
          (timeoutError as any).errorType = 'timeout';
          throw timeoutError;
        }
        
        // Network connectivity errors
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
          const networkError = new Error(`네트워크 연결에 실패했습니다. 백엔드 서버가 실행 중인지 확인해주세요. (${this.baseUrl})`);
          (networkError as any).errorType = 'network';
          throw networkError;
        }
        
        // CORS errors
        if (error.message.includes('CORS') || error.message.includes('blocked')) {
          const corsError = new Error(`CORS 오류가 발생했습니다. 백엔드 CORS 설정을 확인해주세요.`);
          (corsError as any).errorType = 'network';
          throw corsError;
        }
        
        // API errors (already handled above, but add errorType)
        if (error.message.includes('API error:')) {
          (error as any).errorType = 'api';
        }
      }
      
      console.error(`[APIClient] Request failed: ${endpoint}`, error);
      throw error;
    }
  }

  async getFarms(): Promise<APIResponse<Farm[]>> {
    if (this.useMock) {
      await delay(300);
      return {
        data: mockFarms,
        timestamp: new Date().toISOString(),
        status: 'success',
      };
    }
    return this.fetchAPI<Farm[]>('/farms');
  }

  async getCrops(): Promise<APIResponse<Crop[]>> {
    if (this.useMock) {
      await delay(300);
      return {
        data: mockCrops,
        timestamp: new Date().toISOString(),
        status: 'success',
      };
    }
    return this.fetchAPI<Crop[]>('/crops');
  }

  async getFieldBoundaries(
    farmId: string,
    cropId: string
  ): Promise<APIResponse<FieldBoundary[]>> {
    if (this.useMock) {
      await delay(400);
      return {
        data: generateMockFieldBoundaries(farmId, cropId),
        timestamp: new Date().toISOString(),
        status: 'success',
      };
    }
    return this.fetchAPI<FieldBoundary[]>(`/fields?farm_id=${farmId}&crop_id=${cropId}`);
  }

  async getKPISummary(filters: DashboardFilters, lat?: number, lng?: number, fieldId?: string): Promise<APIResponse<KPISummary>> {
    if (this.useMock) {
      await delay(200);
      return {
        data: generateMockKPISummary(),
        timestamp: new Date().toISOString(),
        status: 'success',
      };
    }
    const params = new URLSearchParams();
    if (filters.farmId) params.append('farm_id', filters.farmId);
    if (filters.cropId) params.append('crop_id', filters.cropId);
    if (lat !== undefined) params.append('lat', lat.toString());
    if (lng !== undefined) params.append('lng', lng.toString());
    if (fieldId) params.append('field_id', fieldId);
    return this.fetchAPI<KPISummary>(`/kpi?${params.toString()}`);
  }

  async getNDVIGrid(fieldId: string): Promise<APIResponse<NDVIGrid>> {
    if (this.useMock) {
      await delay(500);
      return {
        data: generateMockNDVIGrid(fieldId),
        timestamp: new Date().toISOString(),
        status: 'success',
      };
    }
    // TODO: This requires field geometry and date range
    // For now, return timeline which is simpler
    const timeline = await this.getNDVITimeline(fieldId);
    // Convert timeline to grid format (placeholder)
    return this.fetchAPI<NDVIGrid>(`/ndvi/${fieldId}/grid`);
  }

  async getNDVITimeline(fieldId: string, dateRange?: { start: string; end: string }): Promise<APIResponse<TimeSeriesData[]>> {
    if (this.useMock) {
      await delay(400);
      return {
        data: [],
        timestamp: new Date().toISOString(),
        status: 'success',
      };
    }
    const params = new URLSearchParams();
    if (dateRange?.start) params.append('date_start', dateRange.start);
    if (dateRange?.end) params.append('date_end', dateRange.end);
    return this.fetchAPI<TimeSeriesData[]>(`/ndvi/${fieldId}/timeline?${params.toString()}`);
  }

  async getStressIndex(fieldId: string): Promise<APIResponse<StressIndex>> {
    if (this.useMock) {
      await delay(500);
      return {
        data: generateMockStressIndex(fieldId),
        timestamp: new Date().toISOString(),
        status: 'success',
      };
    }
    // TODO: Implement stress index endpoint in backend
    return this.fetchAPI<StressIndex>(`/stress/${fieldId}`);
  }

  async getSoilMoisture(
    fieldId: string,
    dateRange?: { start: string; end: string },
    location?: { lat: number; lng: number }
  ): Promise<APIResponse<SoilMoistureData[]>> {
    if (this.useMock) {
      await delay(400);
      return {
        data: generateMockSoilMoisture(fieldId),
        timestamp: new Date().toISOString(),
        status: 'success',
      };
    }
    const params = new URLSearchParams();
    // Always include location if provided, otherwise backend will use defaults
    if (location) {
      params.append('lat', location.lat.toString());
      params.append('lng', location.lng.toString());
    }
    if (dateRange?.start) params.append('date_start', dateRange.start);
    if (dateRange?.end) params.append('date_end', dateRange.end);
    const queryString = params.toString();
    const url = queryString ? `/soil-moisture/${fieldId}?${queryString}` : `/soil-moisture/${fieldId}`;
    return this.fetchAPI<SoilMoistureData[]>(url);
  }

  async getYieldPrediction(
    fieldId: string,
    dateRange?: { start: string; end: string },
    location?: { lat: number; lng: number }
  ): Promise<APIResponse<YieldPredictionData[]>> {
    if (this.useMock) {
      await delay(400);
      return {
        data: generateMockYieldPrediction(fieldId),
        timestamp: new Date().toISOString(),
        status: 'success',
      };
    }
    const params = new URLSearchParams();
    if (location) {
      params.append('lat', location.lat.toString());
      params.append('lng', location.lng.toString());
    }
    if (dateRange?.start) params.append('date_start', dateRange.start);
    if (dateRange?.end) params.append('date_end', dateRange.end);
    return this.fetchAPI<YieldPredictionData[]>(`/yield-prediction/${fieldId}?${params.toString()}`);
  }

  async getCarbonMetrics(
    fieldId: string,
    dateRange?: { start: string; end: string },
    location?: { lat: number; lng: number }
  ): Promise<APIResponse<CarbonMetricsData[]>> {
    if (this.useMock) {
      await delay(400);
      return {
        data: generateMockCarbonMetrics(fieldId),
        timestamp: new Date().toISOString(),
        status: 'success',
      };
    }
    const params = new URLSearchParams();
    if (location) {
      params.append('lat', location.lat.toString());
      params.append('lng', location.lng.toString());
    }
    if (dateRange?.start) params.append('date_start', dateRange.start);
    if (dateRange?.end) params.append('date_end', dateRange.end);
    return this.fetchAPI<CarbonMetricsData[]>(`/carbon-metrics/${fieldId}?${params.toString()}`);
  }

  async getWeatherData(
    fieldId: string,
    location: { lat: number; lng: number },
    dateRange?: { start: string; end: string }
  ): Promise<APIResponse<TimeSeriesData[]>> {
    if (this.useMock) {
      await delay(400);
      // Generate mock weather data
      const mockData: TimeSeriesData[] = [];
      const endDate = dateRange?.end ? new Date(dateRange.end) : new Date();
      const startDate = dateRange?.start ? new Date(dateRange.start) : new Date(endDate.getTime() - 30 * 24 * 60 * 60 * 1000);
      
      for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
        mockData.push({
          timestamp: d.toISOString(),
          value: 15 + Math.random() * 10, // Mock temperature
        });
      }
      
      return {
        data: mockData,
        timestamp: new Date().toISOString(),
        status: 'success',
      };
    }
    // Use real ERA5 weather data from backend
    const params = new URLSearchParams();
    params.append('lat', location.lat.toString());
    params.append('lng', location.lng.toString());
    if (dateRange?.start) params.append('date_start', dateRange.start);
    if (dateRange?.end) params.append('date_end', dateRange.end);
    return this.fetchAPI<TimeSeriesData[]>(`/weather/${fieldId}?${params.toString()}`);
  }
}

// Singleton instance
export const apiClient = new APIClient();

