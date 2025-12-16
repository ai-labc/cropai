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
  DashboardFilters,
  MapLayerType,
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
  loadSoilMoisture: (fieldId: string) => Promise<void>;
  loadYieldPrediction: (fieldId: string) => Promise<void>;
  loadCarbonMetrics: (fieldId: string) => Promise<void>;
  
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
    set({ selectedFarm: farm, filters: { ...get().filters, farmId: farm?.id || null } });
    if (farm) {
      get().loadFieldBoundaries();
    }
  },

  setSelectedCrop: (crop) => {
    set({ selectedCrop: crop, filters: { ...get().filters, cropId: crop?.id || null } });
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
      set({ error: error instanceof Error ? error.message : 'Failed to load farms' });
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
      set({ error: error instanceof Error ? error.message : 'Failed to load crops' });
    } finally {
      set({ isLoading: false });
    }
  },

  loadFieldBoundaries: async () => {
    const { selectedFarm, selectedCrop } = get();
    if (!selectedFarm || !selectedCrop) return;

    try {
      set({ isLoading: true, error: null });
      const response = await apiClient.getFieldBoundaries(selectedFarm.id, selectedCrop.id);
      if (response.status === 'success') {
        set({ fieldBoundaries: response.data });
        // Load data for first field
        if (response.data.length > 0) {
          const firstFieldId = response.data[0].id;
          get().loadKPISummary();
          get().loadSoilMoisture(firstFieldId);
          get().loadYieldPrediction(firstFieldId);
          get().loadCarbonMetrics(firstFieldId);
        }
      }
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to load field boundaries' });
    } finally {
      set({ isLoading: false });
    }
  },

  loadKPISummary: async () => {
    try {
      const response = await apiClient.getKPISummary(get().filters);
      if (response.status === 'success') {
        set({ kpiSummary: response.data });
      }
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to load KPI summary' });
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

  loadSoilMoisture: async (fieldId: string) => {
    try {
      const response = await apiClient.getSoilMoisture(fieldId);
      if (response.status === 'success') {
        const moisture = new Map(get().soilMoisture);
        moisture.set(fieldId, response.data);
        set({ soilMoisture: moisture });
      }
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to load soil moisture' });
    }
  },

  loadYieldPrediction: async (fieldId: string) => {
    try {
      const response = await apiClient.getYieldPrediction(fieldId);
      if (response.status === 'success') {
        const prediction = new Map(get().yieldPrediction);
        prediction.set(fieldId, response.data);
        set({ yieldPrediction: prediction });
      }
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to load yield prediction' });
    }
  },

  loadCarbonMetrics: async (fieldId: string) => {
    try {
      const response = await apiClient.getCarbonMetrics(fieldId);
      if (response.status === 'success') {
        const metrics = new Map(get().carbonMetrics);
        metrics.set(fieldId, response.data);
        set({ carbonMetrics: metrics });
      }
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to load carbon metrics' });
    }
  },

  initializeDashboard: async () => {
    await Promise.all([
      get().loadFarms(),
      get().loadCrops(),
    ]);
  },
}));

