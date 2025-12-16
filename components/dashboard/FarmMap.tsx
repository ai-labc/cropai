/**
 * Farm Map component using Mapbox GL JS
 * Displays field boundaries and optional heatmap layers (NDVI, Stress)
 */

'use client';

import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
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
    if (!mapContainer.current || map.current) return;

    // Initialize map
    // Note: In production, you'd need to set MAPBOX_ACCESS_TOKEN in .env.local
    mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || 'pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw';

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/satellite-v9',
      center: [-122.4194, 37.7749],
      zoom: 13,
    });

    map.current.on('load', () => {
      setMapLoaded(true);
    });

    return () => {
      map.current?.remove();
    };
  }, []);

  // Add field boundaries layer
  useEffect(() => {
    if (!map.current || !mapLoaded || fieldBoundaries.length === 0) return;

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
    const features = fieldBoundaries.map((boundary) => ({
      type: 'Feature' as const,
      id: boundary.id,
      geometry: boundary.geometry,
      properties: boundary.properties,
    }));

    map.current.addSource(sourceId, {
      type: 'geojson',
      data: {
        type: 'FeatureCollection',
        features,
      },
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

  // Handle layer switching
  useEffect(() => {
    if (!map.current || !mapLoaded) return;

    // For MVP, we'll just toggle visibility
    // In production, you'd render actual heatmap tiles from NDVI/Stress grids
    const boundariesLayer = 'field-boundaries-layer';
    
    if (map.current.getLayer(boundariesLayer)) {
      if (activeLayer === 'boundaries' || activeLayer === 'none') {
        map.current.setLayoutProperty(boundariesLayer, 'visibility', 'visible');
      } else {
        map.current.setLayoutProperty(boundariesLayer, 'visibility', 'none');
      }
    }

    // Load NDVI/Stress data when layer is activated
    if (activeLayer === 'ndvi' && fieldBoundaries.length > 0) {
      fieldBoundaries.forEach((boundary) => {
        if (!ndviGrids.has(boundary.id)) {
          loadNDVIGrid(boundary.id);
        }
      });
    }

    if (activeLayer === 'stress' && fieldBoundaries.length > 0) {
      fieldBoundaries.forEach((boundary) => {
        if (!stressIndices.has(boundary.id)) {
          loadStressIndex(boundary.id);
        }
      });
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

