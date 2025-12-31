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
  const { loadNDVIGrid, loadStressIndex } = useDashboardStore();

  useEffect(() => {
    if (!mapContainer.current || map.current) {
      return;
    }

    // Initialize map
    const mapboxToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
    if (!mapboxToken) {
      console.error('[FarmMap] Mapbox token is not set. Please set NEXT_PUBLIC_MAPBOX_TOKEN in .env.local');
      return;
    }
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
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  // Add field boundaries layer
  useEffect(() => {
    if (!map.current || !mapLoaded || fieldBoundaries.length === 0) {
      return;
    }

    const sourceId = 'field-boundaries';
    const layerId = 'field-boundaries-layer';

    // Remove existing source and layer if they exist
    if (map.current.getLayer(layerId)) {
      map.current.removeLayer(layerId);
    }
    if (map.current.getSource(sourceId)) {
      map.current.removeSource(sourceId);
    }

    // Create GeoJSON feature collection
    const features: Feature[] = fieldBoundaries.map((boundary) => ({
      type: 'Feature',
      id: boundary.id,
      geometry: boundary.geometry as Feature['geometry'],
      properties: boundary.properties,
    }));

    const featureCollection: FeatureCollection = {
      type: 'FeatureCollection',
      features,
    };

    map.current.addSource(sourceId, {
      type: 'geojson',
      data: featureCollection,
    });

    map.current.addLayer({
      id: layerId,
      type: 'fill',
      source: sourceId,
      paint: {
        'fill-color': '#22c55e',
        'fill-opacity': 0.4,
        'fill-outline-color': '#16a34a',
      },
    });

    // Fit bounds to show all fields
    if (features.length > 0) {
      const bounds = new mapboxgl.LngLatBounds();
      features.forEach((feature) => {
        if (feature.geometry.type === 'Polygon') {
          feature.geometry.coordinates[0].forEach((coord) => {
            bounds.extend([coord[0], coord[1]]);
          });
        }
      });
      map.current.fitBounds(bounds, { padding: 50 });
    }
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
    if (!map.current || !mapLoaded) return;

    const boundariesLayer = 'field-boundaries-layer';
    const ndviLayer = 'ndvi-heatmap-layer';
    const stressLayer = 'stress-heatmap-layer';
    const ndviSource = 'ndvi-heatmap-source';
    const stressSource = 'stress-heatmap-source';

    // Toggle boundaries layer visibility
    if (map.current.getLayer(boundariesLayer)) {
      if (activeLayer === 'boundaries' || activeLayer === 'none') {
        map.current.setLayoutProperty(boundariesLayer, 'visibility', 'visible');
      } else {
        map.current.setLayoutProperty(boundariesLayer, 'visibility', 'none');
      }
    }

    // Remove existing NDVI/Stress layers
    if (map.current.getLayer(ndviLayer)) {
      map.current.removeLayer(ndviLayer);
    }
    if (map.current.getSource(ndviSource)) {
      map.current.removeSource(ndviSource);
    }
    if (map.current.getLayer(stressLayer)) {
      map.current.removeLayer(stressLayer);
    }
    if (map.current.getSource(stressSource)) {
      map.current.removeSource(stressSource);
    }

    // Handle NDVI layer
    if (activeLayer === 'ndvi') {
      // First, load NDVI data if not available
      fieldBoundaries.forEach((boundary) => {
        if (!ndviGrids.has(boundary.id)) {
          console.log('[FarmMap] Loading NDVI grid for field:', boundary.id);
          loadNDVIGrid(boundary.id);
        }
      });

      // Then, render NDVI heatmap if data is available
      // Only render data for fields that are currently in fieldBoundaries
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
          map.current.addSource(ndviSource, {
            type: 'geojson',
            data: {
              type: 'FeatureCollection',
              features: allFeatures,
            },
          });

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
        }
      }
    }

    // Handle Stress layer
    if (activeLayer === 'stress') {
      // First, load Stress data if not available
      fieldBoundaries.forEach((boundary) => {
        if (!stressIndices.has(boundary.id)) {
          console.log('[FarmMap] Loading Stress index for field:', boundary.id);
          loadStressIndex(boundary.id);
        }
      });

      // Then, render Stress heatmap if data is available
      // Only render data for fields that are currently in fieldBoundaries
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
          map.current.addSource(stressSource, {
            type: 'geojson',
            data: {
              type: 'FeatureCollection',
              features: allFeatures,
            },
          });

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
        }
      }
    }
  }, [activeLayer, mapLoaded, fieldBoundaries, ndviGrids, stressIndices, loadNDVIGrid, loadStressIndex]);

  return (
    <div className={`relative rounded-lg shadow-lg overflow-hidden ${className}`}>
      <div ref={mapContainer} className="w-full h-full" style={{ minHeight: '500px' }} />
      
      {/* Layer toggle controls */}
      <div className="absolute top-4 right-4 bg-white rounded-lg shadow-md p-2 flex gap-2">
        <button
          onClick={() => useDashboardStore.getState().setActiveMapLayer('boundaries')}
          className={`px-3 py-1 rounded text-sm font-medium ${
            activeLayer === 'boundaries'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Boundaries
        </button>
        <button
          onClick={() => useDashboardStore.getState().setActiveMapLayer('ndvi')}
          className={`px-3 py-1 rounded text-sm font-medium ${
            activeLayer === 'ndvi'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          NDVI
        </button>
        <button
          onClick={() => useDashboardStore.getState().setActiveMapLayer('stress')}
          className={`px-3 py-1 rounded text-sm font-medium ${
            activeLayer === 'stress'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Stress
        </button>
      </div>
    </div>
  );
}

