/**
 * Zustand store for dashboard state management
 */

import { create } from 'zustand';
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
  DashboardFilters,
  MapLayerType,
  APIResponse,
} from '@/types';
import { apiClient } from '@/lib/api/client';

interface DashboardState {
  // Filters
  filters: DashboardFilters;
  selectedFarm: Farm | null;
  selectedCrop: Crop | null;
  
  // Data
  farms: Farm[];
  crops: Crop[];
  fieldBoundaries: FieldBoundary[];
  kpiSummary: KPISummary | null;
  ndviGrids: Map<string, NDVIGrid>;
  stressIndices: Map<string, StressIndex>;
  soilMoisture: Map<string, SoilMoistureData[]>;
  yieldPrediction: Map<string, YieldPredictionData[]>;
  carbonMetrics: Map<string, CarbonMetricsData[]>;
  // weatherData: Map<string, TimeSeriesData[]>; // Removed: Weather data is only used in backend calculations, not in UI
  
  // UI State
  activeMapLayer: MapLayerType;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setFilters: (filters: Partial<DashboardFilters>) => void;
  setSelectedFarm: (farm: Farm | null) => void;
  setSelectedCrop: (crop: Crop | null) => void;
  setActiveMapLayer: (layer: MapLayerType) => void;
  
  // Data fetching actions
  loadFarms: () => Promise<void>;
  loadCrops: () => Promise<void>;
  loadFieldBoundaries: () => Promise<void>;
  loadKPISummary: () => Promise<void>;
  loadNDVIGrid: (fieldId: string) => Promise<void>;
  loadStressIndex: (fieldId: string) => Promise<void>;
  loadSoilMoisture: (fieldId: string, dateRange?: { start: string; end: string }, location?: { lat: number; lng: number }) => Promise<void>;
  loadYieldPrediction: (fieldId: string, dateRange?: { start: string; end: string }, location?: { lat: number; lng: number }) => Promise<void>;
  loadCarbonMetrics: (fieldId: string, dateRange?: { start: string; end: string }, location?: { lat: number; lng: number }) => Promise<void>;
  // loadWeatherData: (fieldId: string, location: { lat: number; lng: number }, dateRange?: { start: string; end: string }) => Promise<void>; // Removed: Weather data is only used in backend calculations
  
  // Initialize dashboard
  initializeDashboard: () => Promise<void>;
}

export const useDashboardStore = create<DashboardState>((set, get) => ({
  // Initial state
  filters: {
    farmId: null,
    cropId: null,
    dateRange: null,
  },
  selectedFarm: null,
  selectedCrop: null,
  farms: [],
  crops: [],
  fieldBoundaries: [],
  kpiSummary: null,
  ndviGrids: new Map(),
  stressIndices: new Map(),
  soilMoisture: new Map(),
  yieldPrediction: new Map(),
  carbonMetrics: new Map(),
  // weatherData: new Map(), // Removed: Weather data is only used in backend calculations
  activeMapLayer: 'boundaries',
  isLoading: false,
  error: null,

  // Filter actions
  setFilters: (newFilters) => {
    set((state) => ({
      filters: { ...state.filters, ...newFilters },
    }));
  },

  setSelectedFarm: (farm) => {
    set({ 
      selectedFarm: farm, 
      filters: { ...get().filters, farmId: farm?.id || null },
      activeMapLayer: 'boundaries', // Reset to boundaries when farm changes
      // Clear NDVI/Stress data when farm changes to prevent showing wrong data
      ndviGrids: new Map(),
      stressIndices: new Map(),
    });
    if (farm) {
      get().loadFieldBoundaries();
    }
  },

  setSelectedCrop: (crop) => {
    set({ 
      selectedCrop: crop, 
      filters: { ...get().filters, cropId: crop?.id || null },
      activeMapLayer: 'boundaries', // Reset to boundaries when crop changes
      // Clear NDVI/Stress data when crop changes to prevent showing wrong data
      ndviGrids: new Map(),
      stressIndices: new Map(),
    });
    if (crop) {
      get().loadFieldBoundaries();
    }
  },

  setActiveMapLayer: (layer) => {
    set({ activeMapLayer: layer });
  },

  // Data loading actions
  loadFarms: async () => {
    try {
      set({ isLoading: true, error: null });
      const response = await apiClient.getFarms();
      if (response.status === 'success') {
        set({ farms: response.data });
        // Auto-select first farm if none selected
        if (!get().selectedFarm && response.data.length > 0) {
          get().setSelectedFarm(response.data[0]);
        }
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load farms';
      console.error('[DashboardStore] Error loading farms:', errorMessage);
      set({ error: errorMessage });
      // Fallback to empty array on error
      set({ farms: [] });
    } finally {
      set({ isLoading: false });
    }
  },

  loadCrops: async () => {
    try {
      set({ isLoading: true, error: null });
      const response = await apiClient.getCrops();
      if (response.status === 'success') {
        set({ crops: response.data });
        // Auto-select first crop if none selected
        if (!get().selectedCrop && response.data.length > 0) {
          get().setSelectedCrop(response.data[0]);
        }
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load crops';
      console.error('[DashboardStore] Error loading crops:', errorMessage);
      set({ error: errorMessage });
      // Fallback to empty array on error
      set({ crops: [] });
    } finally {
      set({ isLoading: false });
    }
  },

  loadFieldBoundaries: async () => {
    const state = get();
    const { selectedFarm, selectedCrop } = state;
    
    console.log('[DashboardStore] loadFieldBoundaries called. Farm:', selectedFarm?.id, 'Crop:', selectedCrop?.id);
    
    if (!selectedFarm || !selectedCrop) {
      console.log('[DashboardStore] No farm or crop selected, skipping field boundaries load');
      set({ fieldBoundaries: [] });
      return;
    }

    try {
      set({ isLoading: true, error: null });
      console.log('[DashboardStore] Loading field boundaries for farm:', selectedFarm.id, 'crop:', selectedCrop.id);
      const response = await apiClient.getFieldBoundaries(selectedFarm.id, selectedCrop.id);
      console.log('[DashboardStore] Field boundaries response:', response.status, 'fields:', response.data?.length || 0);
      
      if (response.status === 'success') {
        set({ fieldBoundaries: response.data });
        
        // Load data for first field
        if (response.data.length > 0) {
          const firstField = response.data[0];
          const firstFieldId = firstField.id;
          console.log('[DashboardStore] Loading data for first field:', firstFieldId);
          
          // Get field location from geometry or farm location
          let lat = selectedFarm.location.lat;
          let lng = selectedFarm.location.lng;
          
          // Try to extract center from field geometry
          if (firstField.geometry && firstField.geometry.coordinates) {
            try {
              // Handle Polygon coordinates: number[][][]
              if (firstField.geometry.type === 'Polygon') {
                const coords = firstField.geometry.coordinates[0] as number[][];
                if (coords && coords.length > 0) {
                  const lngs = coords.map((c: number[]) => c[0]);
                  const lats = coords.map((c: number[]) => c[1]);
                  lat = (Math.max(...lats) + Math.min(...lats)) / 2;
                  lng = (Math.max(...lngs) + Math.min(...lngs)) / 2;
                  console.log('[DashboardStore] Extracted field center:', lat, lng);
                }
              }
            } catch (e) {
              console.warn('[DashboardStore] Error extracting field center, using farm location:', e);
              // Use farm location as fallback
            }
          }
          
          // Load KPI summary first (fast, needed for UI)
          get().loadKPISummary();
          
          // Load other data asynchronously in parallel (don't block UI)
          // Use setTimeout to prevent blocking the main thread
          setTimeout(() => {
            Promise.allSettled([
              // Weather data is only used in backend calculations, not loaded in frontend
              get().loadSoilMoisture(firstFieldId, undefined, { lat, lng }),
              get().loadYieldPrediction(firstFieldId, undefined, { lat, lng }),
              get().loadCarbonMetrics(firstFieldId, undefined, { lat, lng }),
            ]).then(results => {
              const failed = results.filter(r => r.status === 'rejected').length;
              if (failed > 0) {
                console.warn(`[DashboardStore] ${failed} data loading requests failed`);
              }
            });
          }, 100);
        }
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load field boundaries';
      console.error('[DashboardStore] Error loading field boundaries:', errorMessage, error);
      set({ error: errorMessage, fieldBoundaries: [] });
    } finally {
      set({ isLoading: false });
    }
  },

  loadKPISummary: async () => {
    try {
      const filters = get().filters;
      
      // Try to load from cache first (synchronous, instant)
      const { APICache } = await import('@/lib/api/cache');
      const cacheKey = `/kpi?farm_id=${filters.farmId || ''}&crop_id=${filters.cropId || ''}`;
      const cached = APICache.get<APIResponse<KPISummary>>(cacheKey);
      
      if (cached && cached.status === 'success') {
        set({ kpiSummary: cached.data });
      }
      
      // Then fetch fresh data in background (will update cache)
      apiClient.getKPISummary(filters).then(response => {
        if (response.status === 'success') {
          set({ kpiSummary: response.data });
        }
      }).catch(error => {
        // Keep cached data if available, silently fail
      });
    } catch (error) {
      // Silently fail - cached data will be used if available
    }
  },

  loadNDVIGrid: async (fieldId: string) => {
    try {
      const response = await apiClient.getNDVIGrid(fieldId);
      if (response.status === 'success') {
        const grids = new Map(get().ndviGrids);
        grids.set(fieldId, response.data);
        set({ ndviGrids: grids });
      }
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to load NDVI grid' });
    }
  },

  loadStressIndex: async (fieldId: string) => {
    try {
      const response = await apiClient.getStressIndex(fieldId);
      if (response.status === 'success') {
        const indices = new Map(get().stressIndices);
        indices.set(fieldId, response.data);
        set({ stressIndices: indices });
      }
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to load stress index' });
    }
  },

  loadSoilMoisture: async (fieldId: string, dateRange?: { start: string; end: string }, location?: { lat: number; lng: number }) => {
    try {
      // Try cache first for instant display
      const { APICache } = await import('@/lib/api/cache');
      const params = new URLSearchParams();
      if (location) {
        params.append('lat', location.lat.toString());
        params.append('lng', location.lng.toString());
      }
      if (dateRange?.start) params.append('date_start', dateRange.start);
      if (dateRange?.end) params.append('date_end', dateRange.end);
      const cacheKey = `/soil-moisture/${fieldId}?${params.toString()}`;
      const cached = APICache.get<APIResponse<SoilMoistureData[]>>(cacheKey);
      
      if (cached && cached.status === 'success') {
        const moisture = new Map(get().soilMoisture);
        moisture.set(fieldId, cached.data);
        set({ soilMoisture: moisture });
      }
      
      // Fetch fresh data in background
      apiClient.getSoilMoisture(fieldId, dateRange, location).then(response => {
        if (response.status === 'success') {
          const moisture = new Map(get().soilMoisture);
          moisture.set(fieldId, response.data);
          set({ soilMoisture: moisture });
        }
      }).catch(() => {
        // Silently fail - cached data will be used if available
      });
    } catch (error) {
      console.warn('[DashboardStore] Soil moisture loading failed or timed out:', error instanceof Error ? error.message : error);
    }
  },

  loadYieldPrediction: async (fieldId: string, dateRange?: { start: string; end: string }, location?: { lat: number; lng: number }) => {
    try {
      // Try cache first for instant display
      const { APICache } = await import('@/lib/api/cache');
      const params = new URLSearchParams();
      if (location) {
        params.append('lat', location.lat.toString());
        params.append('lng', location.lng.toString());
      }
      if (dateRange?.start) params.append('date_start', dateRange.start);
      if (dateRange?.end) params.append('date_end', dateRange.end);
      const cacheKey = `/yield-prediction/${fieldId}?${params.toString()}`;
      const cached = APICache.get<APIResponse<YieldPredictionData[]>>(cacheKey);
      
      if (cached && cached.status === 'success') {
        const prediction = new Map(get().yieldPrediction);
        prediction.set(fieldId, cached.data);
        set({ yieldPrediction: prediction });
      }
      
      // Fetch fresh data in background
      apiClient.getYieldPrediction(fieldId, dateRange, location).then(response => {
        if (response.status === 'success') {
          const prediction = new Map(get().yieldPrediction);
          prediction.set(fieldId, response.data);
          set({ yieldPrediction: prediction });
        }
      }).catch(() => {
        // Silently fail - cached data will be used if available
      });
    } catch (error) {
      console.warn('[DashboardStore] Yield prediction loading failed or timed out:', error instanceof Error ? error.message : error);
    }
  },

  loadCarbonMetrics: async (fieldId: string, dateRange?: { start: string; end: string }, location?: { lat: number; lng: number }) => {
    try {
      // Try cache first for instant display
      const { APICache } = await import('@/lib/api/cache');
      const params = new URLSearchParams();
      if (location) {
        params.append('lat', location.lat.toString());
        params.append('lng', location.lng.toString());
      }
      if (dateRange?.start) params.append('date_start', dateRange.start);
      if (dateRange?.end) params.append('date_end', dateRange.end);
      const cacheKey = `/carbon-metrics/${fieldId}?${params.toString()}`;
      const cached = APICache.get<APIResponse<CarbonMetricsData[]>>(cacheKey);
      
      if (cached && cached.status === 'success') {
        const metrics = new Map(get().carbonMetrics);
        metrics.set(fieldId, cached.data);
        set({ carbonMetrics: metrics });
      }
      
      // Fetch fresh data in background
      apiClient.getCarbonMetrics(fieldId, dateRange, location).then(response => {
        if (response.status === 'success') {
          const metrics = new Map(get().carbonMetrics);
          metrics.set(fieldId, response.data);
          set({ carbonMetrics: metrics });
        }
      }).catch(() => {
        // Silently fail - cached data will be used if available
      });
    } catch (error) {
      console.warn('[DashboardStore] Carbon metrics loading failed or timed out:', error instanceof Error ? error.message : error);
    }
  },

  // loadWeatherData: Removed - Weather data is only used in backend calculations
  // Weather data is fetched by backend services (kpi_calculator, yield_calculator, carbon_calculator)
  // No need to load it in frontend since it's not displayed in UI

  initializeDashboard: async () => {
    try {
      await Promise.all([
        get().loadFarms(),
        get().loadCrops(),
      ]);
    } catch (error) {
      console.error('[DashboardStore] Error initializing dashboard:', error);
      set({ error: error instanceof Error ? error.message : 'Failed to initialize dashboard' });
    }
  },
}));

