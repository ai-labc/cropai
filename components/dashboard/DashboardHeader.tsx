/**
 * Dashboard header with filters (Farm, Crop selectors)
 */

'use client';

import { Select } from '@/components/ui/Select';
import { useDashboardStore } from '@/store/dashboardStore';
import { useEffect } from 'react';

export function DashboardHeader() {
  const {
    farms,
    crops,
    selectedFarm,
    selectedCrop,
    setSelectedFarm,
    setSelectedCrop,
    initializeDashboard,
  } = useDashboardStore();

  useEffect(() => {
    // Only initialize once on mount
    // Use requestIdleCallback to prevent blocking initial render
    if (farms.length === 0 && crops.length === 0) {
      if (typeof window !== 'undefined' && 'requestIdleCallback' in window) {
        requestIdleCallback(() => {
          initializeDashboard();
        }, { timeout: 500 });
      } else {
        // Fallback: small delay to let UI render first
        setTimeout(() => {
          initializeDashboard();
        }, 100);
      }
    }
  }, []); // Empty dependency array - only run once

  const farmOptions = farms.map((farm) => ({ id: farm.id, name: farm.name }));
  
  // Filter crops based on selected farm
  // Only show crops that have actual data:
  // - farm-1 (AB) → crop-1 (Canola) only
  // - farm-2 (BC) → crop-2 (Timothy Hay) only
  const cropOptions = selectedFarm
    ? crops.filter((crop) => {
        if (selectedFarm.id === 'farm-1') {
          return crop.id === 'crop-1'; // AB only has Canola
        } else if (selectedFarm.id === 'farm-2') {
          return crop.id === 'crop-2'; // BC only has Timothy Hay
        }
        return true; // Fallback: show all crops
      }).map((crop) => ({ id: crop.id, name: crop.name }))
    : crops.map((crop) => ({ id: crop.id, name: crop.name }));

  return (
    <div className="bg-primary-dark px-6 py-4 flex items-center justify-between">
      <h1 className="text-3xl font-bold text-white">Dashboard</h1>
      <div className="flex items-center gap-6">
        <Select
          label="Farm"
          options={farmOptions}
          selected={selectedFarm ? { id: selectedFarm.id, name: selectedFarm.name } : null}
          onChange={(option) => {
            const farm = farms.find((f) => f.id === option?.id);
            setSelectedFarm(farm || null);
            // Reset crop selection when farm changes (since available crops change)
            setSelectedCrop(null);
          }}
          disabled={farms.length === 0}
        />
        <Select
          label="Crop"
          options={cropOptions}
          selected={selectedCrop ? { id: selectedCrop.id, name: selectedCrop.name } : null}
          onChange={(option) => {
            const crop = crops.find((c) => c.id === option?.id);
            setSelectedCrop(crop || null);
          }}
          disabled={crops.length === 0 || !selectedFarm || cropOptions.length === 0}
        />
      </div>
    </div>
  );
}

