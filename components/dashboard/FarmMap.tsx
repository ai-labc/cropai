/**
 * Farm Map component using Mapbox GL JS
 * Displays field boundaries and optional heatmap layers (NDVI, Stress)
 */

'use client';

import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import type { Feature, FeatureCollection } from 'geojson';
import { FieldBoundary, NDVIGrid, StressIndex, MapLayerType } from '@/types';
import { useDashboardStore } from '@/store/dashboardStore';

interface FarmMapProps {
  fieldBoundaries: FieldBoundary[];
  ndviGrids: Map<string, NDVIGrid>;
  stressIndices: Map<string, StressIndex>;
  activeLayer: MapLayerType;
  className?: string;
}

export function FarmMap({
  fieldBoundaries,
  ndviGrids,
  stressIndices,
  activeLayer,
  className = '',
}: FarmMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const { loadNDVIGrid, loadStressIndex, isLoadingNDVI, isLoadingStress, mapCenter } = useDashboardStore();
  const prevMapCenterRef = useRef<{ lat: number; lng: number } | null>(null);
  
  // Track previous state to prevent unnecessary re-renders
  const prevActiveLayerRef = useRef<MapLayerType>(activeLayer);
  const prevNdviGridsKeysRef = useRef<string>('');
  const prevStressIndicesKeysRef = useRef<string>('');
  const prevFieldBoundariesIdsRef = useRef<string>('');
  const boundariesLayerAddedRef = useRef<boolean>(false);
  const mapInitializedRef = useRef<boolean>(false);
  // Use a fixed ID to avoid hydration mismatch - Mapbox doesn't require unique IDs
  const mapContainerId = 'farm-map-container';

  useEffect(() => {
    // Prevent double initialization in React Strict Mode
    if (!mapContainer.current) {
      return;
    }
    
    // Check if map already exists in this container
    if (map.current) {
      console.log('[FarmMap] Map instance already exists, skipping initialization');
      return;
    }
    
    // Check if container already has a map instance (React Strict Mode protection)
    const container = mapContainer.current;
    if ((container as any)._mapboxMap) {
      console.log('[FarmMap] Container already has a map instance, cleaning up first');
      try {
        const existingMap = (container as any)._mapboxMap;
        // Remove all layers and sources before removing map
        const allLayers = ['field-boundaries-layer', 'ndvi-heatmap-layer', 'stress-heatmap-layer'];
        const allSources = ['field-boundaries', 'ndvi-heatmap-source', 'stress-heatmap-source'];
        
        allLayers.forEach(layerId => {
          try {
            if (existingMap.getLayer(layerId)) {
              existingMap.removeLayer(layerId);
            }
          } catch (e) {
            // Ignore errors
          }
        });
        
        allSources.forEach(sourceId => {
          try {
            if (existingMap.getSource(sourceId)) {
              existingMap.removeSource(sourceId);
            }
          } catch (e) {
            // Ignore errors
          }
        });
        
        existingMap.remove();
        (container as any)._mapboxMap = null;
      } catch (e) {
        console.warn('[FarmMap] Error removing existing map from container:', e);
      }
    }
    
    if (mapInitializedRef.current) {
      console.log('[FarmMap] Map already initialized, skipping');
      return;
    }
    
    mapInitializedRef.current = true;

    // Initialize map
    const mapboxToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
    if (!mapboxToken) {
      console.error('[FarmMap] Mapbox token is not set. Please set NEXT_PUBLIC_MAPBOX_TOKEN in .env.local');
      return;
    }
    
    // Debug: Log token info (first 10 chars only for security)
    console.log('[FarmMap] Mapbox token loaded:', mapboxToken.substring(0, 10) + '...', 'Length:', mapboxToken.length);
    
    mapboxgl.accessToken = mapboxToken;

    // Default center to Hartland Colony, Alberta (first farm)
    // Will be adjusted when field boundaries are loaded
    try {
      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/satellite-v9',
        center: [-113.092639, 52.619167],  // Hartland Colony, Alberta
        zoom: 13,
      });
      
      // Store reference in container for cleanup detection
      if (mapContainer.current) {
        (mapContainer.current as any)._mapboxMap = map.current;
      }

      map.current.on('load', () => {
        setMapLoaded(true);
      });

      map.current.on('error', (e) => {
        console.error('[FarmMap] Map error:', e);
      });

      map.current.on('style.load', () => {
        // Map style loaded
      });
    } catch (error) {
      console.error('[FarmMap] Error creating map:', error);
    }

    return () => {
      if (map.current) {
        console.log('[FarmMap] Cleaning up map instance');
        // Remove all layers and sources before removing map
        const allLayers = ['field-boundaries-layer', 'ndvi-heatmap-layer', 'stress-heatmap-layer'];
        const allSources = ['field-boundaries', 'ndvi-heatmap-source', 'stress-heatmap-source'];
        
        allLayers.forEach(layerId => {
          try {
            if (map.current?.getLayer(layerId)) {
              map.current.removeLayer(layerId);
              console.log('[FarmMap] Removed layer:', layerId);
            }
          } catch (e) {
            // Ignore errors during cleanup
          }
        });
        
        allSources.forEach(sourceId => {
          try {
            if (map.current?.getSource(sourceId)) {
              map.current.removeSource(sourceId);
              console.log('[FarmMap] Removed source:', sourceId);
            }
          } catch (e) {
            // Ignore errors during cleanup
          }
        });
        
        // Clear container reference
        if (mapContainer.current) {
          (mapContainer.current as any)._mapboxMap = null;
        }
        
        map.current.remove();
        map.current = null;
        setMapLoaded(false);
        boundariesLayerAddedRef.current = false;
        mapInitializedRef.current = false;
        console.log('[FarmMap] Map instance cleaned up');
      }
    };
  }, []);

  // Add field boundaries layer
  useEffect(() => {
    if (!map.current || !mapLoaded || fieldBoundaries.length === 0 || !mapInitializedRef.current) {
      return;
    }

    const sourceId = 'field-boundaries';
    const layerId = 'field-boundaries-layer';
    
    // Check if field boundaries actually changed
    const currentFieldIds = fieldBoundaries.map(b => b.id).sort().join(',');
    if (prevFieldBoundariesIdsRef.current === currentFieldIds && boundariesLayerAddedRef.current) {
      // No change, skip update
      return;
    }

    console.log('[FarmMap] Updating field boundaries layer. Fields:', currentFieldIds);

    // Always remove existing source and layer first (React Strict Mode protection)
    // Remove layer before source (Mapbox requirement)
    const outlineLayerId = `${layerId}-outline`;
    if (map.current.getLayer(outlineLayerId)) {
      try {
        map.current.removeLayer(outlineLayerId);
        console.log('[FarmMap] Removed existing boundaries outline layer');
      } catch (e) {
        console.warn('[FarmMap] Error removing boundaries outline layer:', e);
      }
    }
    if (map.current.getLayer(layerId)) {
      try {
        map.current.removeLayer(layerId);
        console.log('[FarmMap] Removed existing boundaries layer');
      } catch (e) {
        console.warn('[FarmMap] Error removing boundaries layer:', e);
      }
    }
    if (map.current.getSource(sourceId)) {
      try {
        map.current.removeSource(sourceId);
        console.log('[FarmMap] Removed existing boundaries source');
      } catch (e) {
        console.warn('[FarmMap] Error removing boundaries source:', e);
      }
    }
    
    // Reset ref to allow re-adding (important for React Strict Mode)
    boundariesLayerAddedRef.current = false;

    // Create GeoJSON feature collection - all fields use transparent green
    const features: Feature[] = fieldBoundaries.map((boundary) => ({
      type: 'Feature',
      id: boundary.id,
      geometry: boundary.geometry as Feature['geometry'],
      properties: {
        ...boundary.properties,
      },
    }));

    const featureCollection: FeatureCollection = {
      type: 'FeatureCollection',
      features,
    };

    // Ensure source doesn't exist before adding
    if (map.current.getSource(sourceId)) {
      console.warn('[FarmMap] Boundaries source still exists after removal attempt');
      return;
    }

    try {
      map.current.addSource(sourceId, {
        type: 'geojson',
        data: featureCollection,
      });

      if (!map.current.getLayer(layerId)) {
        map.current.addLayer({
          id: layerId,
          type: 'fill',
          source: sourceId,
          paint: {
            'fill-color': '#22c55e', // Transparent green for all fields
            'fill-opacity': 0.3, // Transparent
            'fill-outline-color': '#16a34a', // Slightly darker green for outline
          },
        });
        
        // Add a separate line layer for better visibility of field boundaries
        map.current.addLayer({
          id: `${layerId}-outline`,
          type: 'line',
          source: sourceId,
          paint: {
            'line-color': '#16a34a', // Darker green outline
            'line-width': 2,
            'line-opacity': 0.6,
          },
        });
        boundariesLayerAddedRef.current = true;
        console.log('[FarmMap] Boundaries layer added successfully with', features.length, 'fields');
      } else {
        console.warn('[FarmMap] Boundaries layer already exists');
      }
    } catch (e) {
      console.error('[FarmMap] Error adding boundaries layer:', e);
      boundariesLayerAddedRef.current = false;
    }

    // Fit bounds to show all fields
    if (features.length > 0 && boundariesLayerAddedRef.current) {
      const bounds = new mapboxgl.LngLatBounds();
      features.forEach((feature) => {
        if (feature.geometry.type === 'Polygon') {
          feature.geometry.coordinates[0].forEach((coord) => {
            bounds.extend([coord[0], coord[1]]);
          });
        } else if (feature.geometry.type === 'MultiPolygon') {
          feature.geometry.coordinates.forEach((polygon) => {
            polygon[0].forEach((coord) => {
              bounds.extend([coord[0], coord[1]]);
            });
          });
        }
      });
      map.current.fitBounds(bounds, { padding: 50 });
    }
    
    // Update ref to track current field boundaries
    prevFieldBoundariesIdsRef.current = currentFieldIds;
  }, [mapLoaded, fieldBoundaries]);

  // Convert grid data to GeoJSON polygons for heatmap visualization
  const gridToGeoJSON = (
    grid: number[][],
    bounds: { north: number; south: number; east: number; west: number },
    values: number[][]
  ): Feature[] => {
    const rows = grid.length;
    const cols = grid[0]?.length || 0;
    if (rows === 0 || cols === 0) return [];

    const latRange = bounds.north - bounds.south;
    const lngRange = bounds.east - bounds.west;
    const cellLat = latRange / rows;
    const cellLng = lngRange / cols;

    const features: Feature[] = [];

    for (let i = 0; i < rows; i++) {
      for (let j = 0; j < cols; j++) {
        const value = values[i]?.[j] ?? 0;
        const north = bounds.north - i * cellLat;
        const south = bounds.north - (i + 1) * cellLat;
        const west = bounds.west + j * cellLng;
        const east = bounds.west + (j + 1) * cellLng;

        features.push({
          type: 'Feature',
          geometry: {
            type: 'Polygon',
            coordinates: [[
              [west, south],
              [east, south],
              [east, north],
              [west, north],
              [west, south],
            ]],
          },
          properties: { value },
        });
      }
    }

    return features;
  };

  // Get color based on NDVI value (0-1)
  const getNDVIColor = (value: number): string => {
    // NDVI color scale: brown (low) -> yellow -> green (high)
    if (value < 0.2) return '#8B4513'; // Brown
    if (value < 0.4) return '#DAA520'; // Goldenrod
    if (value < 0.6) return '#9ACD32'; // Yellow-green
    if (value < 0.8) return '#32CD32'; // Lime green
    return '#228B22'; // Forest green
  };

  // Get color based on Stress value (0-1)
  const getStressColor = (value: number): string => {
    // Stress color scale: green (low) -> yellow -> red (high)
    if (value < 0.3) return '#22c55e'; // Green
    if (value < 0.5) return '#eab308'; // Yellow
    if (value < 0.7) return '#f97316'; // Orange
    return '#ef4444'; // Red
  };

  // Handle layer switching and render heatmaps
  useEffect(() => {
    if (!map.current || !mapLoaded || !mapInitializedRef.current) return;

    const boundariesLayer = 'field-boundaries-layer';
    const ndviLayer = 'ndvi-heatmap-layer';
    const stressLayer = 'stress-heatmap-layer';
    const ndviSource = 'ndvi-heatmap-source';
    const stressSource = 'stress-heatmap-source';
    
    // Check if we actually need to update
    const currentNdviKeys = Array.from(ndviGrids.keys()).sort().join(',');
    const currentStressKeys = Array.from(stressIndices.keys()).sort().join(',');
    const currentFieldIds = fieldBoundaries.map(b => b.id).sort().join(',');
    const layerChanged = prevActiveLayerRef.current !== activeLayer;
    const ndviDataChanged = prevNdviGridsKeysRef.current !== currentNdviKeys;
    const stressDataChanged = prevStressIndicesKeysRef.current !== currentStressKeys;
    const fieldBoundariesChanged = prevFieldBoundariesIdsRef.current !== currentFieldIds;
    
    // Only update if layer changed or relevant data changed
    // Field boundaries change should only trigger update if we're switching layers or data actually changed
    const shouldUpdateNDVI = activeLayer === 'ndvi' && (layerChanged || ndviDataChanged || (fieldBoundariesChanged && ndviGrids.size > 0));
    const shouldUpdateStress = activeLayer === 'stress' && (layerChanged || stressDataChanged || (fieldBoundariesChanged && stressIndices.size > 0));
    const shouldUpdateBoundaries = (activeLayer === 'boundaries' || activeLayer === 'none') && (layerChanged || fieldBoundariesChanged);
    
    if (!shouldUpdateNDVI && !shouldUpdateStress && !shouldUpdateBoundaries && !layerChanged) {
      // No changes needed, skip update
      return;
    }
    
    console.log('[FarmMap] Layer update triggered:', {
      activeLayer,
      layerChanged,
      ndviDataChanged,
      stressDataChanged,
      shouldUpdateNDVI,
      shouldUpdateStress,
    });

    // Toggle boundaries layer visibility
    if (map.current.getLayer(boundariesLayer)) {
      if (activeLayer === 'boundaries' || activeLayer === 'none') {
        map.current.setLayoutProperty(boundariesLayer, 'visibility', 'visible');
      } else {
        map.current.setLayoutProperty(boundariesLayer, 'visibility', 'none');
      }
    }

    // Remove existing NDVI/Stress layers and sources ONLY when switching away from them
    // Must remove layer before source (Mapbox requirement)
    // Only remove if we're switching to a different layer (not when updating the same layer)
    if (layerChanged && activeLayer !== 'ndvi') {
      if (map.current.getLayer(ndviLayer)) {
        try {
          map.current.removeLayer(ndviLayer);
        } catch (e) {
          console.warn('[FarmMap] Error removing NDVI layer:', e);
        }
      }
      if (map.current.getSource(ndviSource)) {
        try {
          map.current.removeSource(ndviSource);
        } catch (e) {
          console.warn('[FarmMap] Error removing NDVI source:', e);
        }
      }
    }
    
    if (layerChanged && activeLayer !== 'stress') {
      if (map.current.getLayer(stressLayer)) {
        try {
          map.current.removeLayer(stressLayer);
        } catch (e) {
          console.warn('[FarmMap] Error removing Stress layer:', e);
        }
      }
      if (map.current.getSource(stressSource)) {
        try {
          map.current.removeSource(stressSource);
        } catch (e) {
          console.warn('[FarmMap] Error removing Stress source:', e);
        }
      }
    }

    // Handle NDVI layer
    if (shouldUpdateNDVI) {
      // First, load NDVI data if not available
      const needsDataLoad = fieldBoundaries.some(boundary => !ndviGrids.has(boundary.id));
      if (needsDataLoad) {
        fieldBoundaries.forEach((boundary) => {
          if (!ndviGrids.has(boundary.id)) {
            console.log('[FarmMap] Loading NDVI grid for field:', boundary.id);
            loadNDVIGrid(boundary.id);
          }
        });
        // Don't render layer yet - wait for data to load
        // The useEffect will be triggered again when data arrives
        return;
      }

      // Only render if we have data for all current fields
      const currentFieldIds = new Set(fieldBoundaries.map(b => b.id));
      const filteredNdviGrids = Array.from(ndviGrids.entries()).filter(
        ([fieldId]) => currentFieldIds.has(fieldId)
      );
      
      if (filteredNdviGrids.length > 0) {
        const allFeatures: Feature[] = [];
        
        filteredNdviGrids.forEach(([fieldId, ndviGrid]) => {
          const grid = ndviGrid.grid;
          if (grid && grid.values && grid.bounds) {
            const features = gridToGeoJSON(
              grid.values,
              grid.bounds,
              grid.values
            );
            allFeatures.push(...features);
          }
        });

        if (allFeatures.length > 0) {
          // Remove existing source/layer if updating (not just switching)
          if (ndviDataChanged && map.current.getSource(ndviSource)) {
            try {
              if (map.current.getLayer(ndviLayer)) {
                map.current.removeLayer(ndviLayer);
              }
              map.current.removeSource(ndviSource);
            } catch (e) {
              console.warn('[FarmMap] Error cleaning up existing NDVI source:', e);
            }
          }

          // Only add if source doesn't exist
          if (!map.current.getSource(ndviSource)) {
            try {
              map.current.addSource(ndviSource, {
                type: 'geojson',
                data: {
                  type: 'FeatureCollection',
                  features: allFeatures,
                },
              });

              if (!map.current.getLayer(ndviLayer)) {
                map.current.addLayer({
                  id: ndviLayer,
                  type: 'fill',
                  source: ndviSource,
                  paint: {
                    'fill-color': [
                      'interpolate',
                      ['linear'],
                      ['get', 'value'],
                      0, '#8B4513',    // Brown (low NDVI)
                      0.2, '#DAA520',  // Goldenrod
                      0.4, '#9ACD32',  // Yellow-green
                      0.6, '#32CD32',  // Lime green
                      0.8, '#228B22',  // Forest green
                      1, '#006400',    // Dark green (high NDVI)
                    ],
                    'fill-opacity': 0.7,
                    'fill-outline-color': 'rgba(0,0,0,0.1)',
                  },
                });
                console.log('[FarmMap] NDVI layer added successfully with', allFeatures.length, 'features');
              }
            } catch (e) {
              console.error('[FarmMap] Error adding NDVI layer:', e);
            }
          } else if (ndviDataChanged) {
            // Update existing source data if data changed
            try {
              const source = map.current.getSource(ndviSource) as mapboxgl.GeoJSONSource;
              source.setData({
                type: 'FeatureCollection',
                features: allFeatures,
              });
              console.log('[FarmMap] NDVI layer updated with', allFeatures.length, 'features');
            } catch (e) {
              console.error('[FarmMap] Error updating NDVI layer:', e);
            }
          }
        }
      }
    }

    // Handle Stress layer
    if (shouldUpdateStress) {
      // First, load Stress data if not available
      const needsDataLoad = fieldBoundaries.some(boundary => !stressIndices.has(boundary.id));
      if (needsDataLoad) {
        fieldBoundaries.forEach((boundary) => {
          if (!stressIndices.has(boundary.id)) {
            console.log('[FarmMap] Loading Stress index for field:', boundary.id);
            loadStressIndex(boundary.id);
          }
        });
        // Don't render layer yet - wait for data to load
        // The useEffect will be triggered again when data arrives
        return;
      }

      // Only render if we have data for all current fields
      const currentFieldIdsForStress = new Set(fieldBoundaries.map(b => b.id));
      const filteredStressIndices = Array.from(stressIndices.entries()).filter(
        ([fieldId]) => currentFieldIdsForStress.has(fieldId)
      );
      
      if (filteredStressIndices.length > 0) {
        const allFeatures: Feature[] = [];
        
        filteredStressIndices.forEach(([fieldId, stressIndex]) => {
          const grid = stressIndex.grid;
          if (grid && grid.values && grid.bounds) {
            const features = gridToGeoJSON(
              grid.values,
              grid.bounds,
              grid.values
            );
            allFeatures.push(...features);
          }
        });

        if (allFeatures.length > 0) {
          // Remove existing source/layer if updating (not just switching)
          if (stressDataChanged && map.current.getSource(stressSource)) {
            try {
              if (map.current.getLayer(stressLayer)) {
                map.current.removeLayer(stressLayer);
              }
              map.current.removeSource(stressSource);
            } catch (e) {
              console.warn('[FarmMap] Error cleaning up existing Stress source:', e);
            }
          }

          // Only add if source doesn't exist
          if (!map.current.getSource(stressSource)) {
            try {
              map.current.addSource(stressSource, {
                type: 'geojson',
                data: {
                  type: 'FeatureCollection',
                  features: allFeatures,
                },
              });

              if (!map.current.getLayer(stressLayer)) {
                map.current.addLayer({
                  id: stressLayer,
                  type: 'fill',
                  source: stressSource,
                  paint: {
                    'fill-color': [
                      'interpolate',
                      ['linear'],
                      ['get', 'value'],
                      0, '#22c55e',    // Green (low stress)
                      0.3, '#eab308',  // Yellow
                      0.5, '#f97316',  // Orange
                      0.7, '#ef4444',  // Red
                      1, '#991b1b',    // Dark red (high stress)
                    ],
                    'fill-opacity': 0.7,
                    'fill-outline-color': 'rgba(0,0,0,0.1)',
                  },
                });
                console.log('[FarmMap] Stress layer added successfully with', allFeatures.length, 'features');
              }
            } catch (e) {
              console.error('[FarmMap] Error adding Stress layer:', e);
            }
          } else if (stressDataChanged) {
            // Update existing source data if data changed
            try {
              const source = map.current.getSource(stressSource) as mapboxgl.GeoJSONSource;
              source.setData({
                type: 'FeatureCollection',
                features: allFeatures,
              });
              console.log('[FarmMap] Stress layer updated with', allFeatures.length, 'features');
            } catch (e) {
              console.error('[FarmMap] Error updating Stress layer:', e);
            }
          }
        }
      }
    }
    
    // Update refs to track current state
    prevActiveLayerRef.current = activeLayer;
    prevNdviGridsKeysRef.current = currentNdviKeys;
    prevStressIndicesKeysRef.current = currentStressKeys;
    prevFieldBoundariesIdsRef.current = currentFieldIds;
  }, [activeLayer, mapLoaded, fieldBoundaries, ndviGrids, stressIndices, loadNDVIGrid, loadStressIndex]);

  // Handle map center changes (for location search)
  useEffect(() => {
    if (!map.current || !mapLoaded || !mapCenter || !mapInitializedRef.current) {
      return;
    }

    // Check if center actually changed
    const prevCenter = prevMapCenterRef.current;
    if (prevCenter && 
        prevCenter.lat === mapCenter.lat && 
        prevCenter.lng === mapCenter.lng) {
      return; // No change, skip animation
    }

    console.log('[FarmMap] Moving map to center:', mapCenter);

    try {
      map.current.flyTo({
        center: [mapCenter.lng, mapCenter.lat],
        zoom: 13,
        duration: 1500,
        essential: true, // Animate even if user is interacting
      });
      
      prevMapCenterRef.current = mapCenter;
    } catch (error) {
      console.error('[FarmMap] Error moving map to center:', error);
    }
  }, [mapLoaded, mapCenter]);

  // Get layer info for header and legend
  const getLayerInfo = () => {
    switch (activeLayer) {
      case 'ndvi':
        return {
          name: 'NDVI',
          description: 'Vegetation Health',
          fullName: 'NDVI (Vegetation Health)',
        };
      case 'stress':
        return {
          name: 'Stress Index',
          description: 'Rule-based',
          fullName: 'Stress Index (Rule-based)',
        };
      case 'boundaries':
        return {
          name: 'Field Boundaries',
          description: 'Field Boundaries',
          fullName: 'Field Boundaries',
        };
      default:
        return {
          name: 'Field Boundaries',
          description: 'Field Boundaries',
          fullName: 'Field Boundaries',
        };
    }
  };

  const layerInfo = getLayerInfo();

  return (
    <div className={`relative rounded-lg shadow-lg overflow-hidden ${className}`}>
      {/* Layer Header - Top Left */}
      <div className="absolute top-4 left-4 bg-white rounded-lg shadow-md px-4 py-2.5 z-10 border-l-4 border-blue-600">
        <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">Layer</div>
        <div className="text-base font-bold text-gray-900 mt-0.5">{layerInfo.fullName}</div>
      </div>
      
      <div 
        ref={mapContainer} 
        id={mapContainerId}
        className="w-full h-full" 
        style={{ minHeight: '500px' }} 
      />
      
      {/* Layer toggle controls - Top Right */}
      <div className="absolute top-4 right-4 bg-white rounded-lg shadow-md p-2 flex gap-2 z-10">
        <button
          onClick={() => useDashboardStore.getState().setActiveMapLayer('boundaries')}
          className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
            activeLayer === 'boundaries'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Boundaries
        </button>
        <button
          onClick={() => useDashboardStore.getState().setActiveMapLayer('ndvi')}
          disabled={isLoadingNDVI}
          className={`px-3 py-1 rounded text-sm font-medium transition-colors relative ${
            activeLayer === 'ndvi'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          } ${isLoadingNDVI ? 'opacity-75 cursor-wait' : ''}`}
        >
          {isLoadingNDVI && activeLayer === 'ndvi' ? (
            <span className="flex items-center gap-1">
              <svg className="animate-spin h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Loading...
            </span>
          ) : (
            'NDVI'
          )}
        </button>
        <button
          onClick={() => useDashboardStore.getState().setActiveMapLayer('stress')}
          disabled={isLoadingStress}
          className={`px-3 py-1 rounded text-sm font-medium transition-colors relative ${
            activeLayer === 'stress'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          } ${isLoadingStress ? 'opacity-75 cursor-wait' : ''}`}
        >
          {isLoadingStress && activeLayer === 'stress' ? (
            <span className="flex items-center gap-1">
              <svg className="animate-spin h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Loading...
            </span>
          ) : (
            'Stress'
          )}
        </button>
      </div>
      
      {/* Legend - Bottom Right */}
      {(activeLayer === 'ndvi' || activeLayer === 'stress') && (
        <div className="absolute bottom-4 right-4 bg-white rounded-lg shadow-lg p-3 z-10 w-56 border border-gray-200">
          {activeLayer === 'ndvi' ? (
            <div>
              <div className="text-sm font-bold text-gray-800 mb-2.5">NDVI Scale</div>
              <div className="space-y-1.5">
                <div className="flex items-center gap-2.5">
                  <div className="w-5 h-5 rounded border border-gray-300" style={{ backgroundColor: '#006400' }}></div>
                  <div className="flex-1">
                    <div className="text-xs font-semibold text-gray-700">Healthy</div>
                    <div className="text-xs text-gray-500">0.8 - 1.0</div>
                  </div>
                </div>
                <div className="flex items-center gap-2.5">
                  <div className="w-5 h-5 rounded border border-gray-300" style={{ backgroundColor: '#32CD32' }}></div>
                  <div className="flex-1">
                    <div className="text-xs font-semibold text-gray-700">Moderate</div>
                    <div className="text-xs text-gray-500">0.6 - 0.8</div>
                  </div>
                </div>
                <div className="flex items-center gap-2.5">
                  <div className="w-5 h-5 rounded border border-gray-300" style={{ backgroundColor: '#9ACD32' }}></div>
                  <div className="flex-1">
                    <div className="text-xs font-semibold text-gray-700">Moderate</div>
                    <div className="text-xs text-gray-500">0.4 - 0.6</div>
                  </div>
                </div>
                <div className="flex items-center gap-2.5">
                  <div className="w-5 h-5 rounded border border-gray-300" style={{ backgroundColor: '#DAA520' }}></div>
                  <div className="flex-1">
                    <div className="text-xs font-semibold text-gray-700">Poor</div>
                    <div className="text-xs text-gray-500">0.2 - 0.4</div>
                  </div>
                </div>
                <div className="flex items-center gap-2.5">
                  <div className="w-5 h-5 rounded border border-gray-300" style={{ backgroundColor: '#8B4513' }}></div>
                  <div className="flex-1">
                    <div className="text-xs font-semibold text-gray-700">Poor</div>
                    <div className="text-xs text-gray-500">0.0 - 0.2</div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div>
              <div className="text-sm font-bold text-gray-800 mb-2.5">Stress Index Scale</div>
              <div className="space-y-1.5">
                <div className="flex items-center gap-2.5">
                  <div className="w-5 h-5 rounded border border-gray-300" style={{ backgroundColor: '#22c55e' }}></div>
                  <div className="flex-1">
                    <div className="text-xs font-semibold text-gray-700">Low</div>
                    <div className="text-xs text-gray-500">0 - 30</div>
                  </div>
                </div>
                <div className="flex items-center gap-2.5">
                  <div className="w-5 h-5 rounded border border-gray-300" style={{ backgroundColor: '#eab308' }}></div>
                  <div className="flex-1">
                    <div className="text-xs font-semibold text-gray-700">Medium</div>
                    <div className="text-xs text-gray-500">30 - 50</div>
                  </div>
                </div>
                <div className="flex items-center gap-2.5">
                  <div className="w-5 h-5 rounded border border-gray-300" style={{ backgroundColor: '#f97316' }}></div>
                  <div className="flex-1">
                    <div className="text-xs font-semibold text-gray-700">High</div>
                    <div className="text-xs text-gray-500">50 - 70</div>
                  </div>
                </div>
                <div className="flex items-center gap-2.5">
                  <div className="w-5 h-5 rounded border border-gray-300" style={{ backgroundColor: '#ef4444' }}></div>
                  <div className="flex-1">
                    <div className="text-xs font-semibold text-gray-700">High</div>
                    <div className="text-xs text-gray-500">70 - 100</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* Loading overlay for map */}
      {(isLoadingNDVI && activeLayer === 'ndvi') || (isLoadingStress && activeLayer === 'stress') ? (
        <div className="absolute inset-0 bg-black bg-opacity-20 flex items-center justify-center z-20 rounded-lg">
          <div className="bg-white rounded-lg shadow-lg p-4 flex items-center gap-3">
            <svg className="animate-spin h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span className="text-gray-700 font-medium">
              {activeLayer === 'ndvi' ? 'Loading NDVI data...' : 'Loading Stress data...'}
            </span>
          </div>
        </div>
      ) : null}
    </div>
  );
}

