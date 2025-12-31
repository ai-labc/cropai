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
    <div className="bg-primary-dark px-4 sm:px-6 py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <h1 className="text-2xl sm:text-3xl font-bold text-white">Dashboard</h1>
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 sm:gap-6 w-full sm:w-auto">
        <Select
          label="Farm"
          options={farmOptions}
          selected={selectedFarm ? { id: selectedFarm.id, name: selectedFarm.name } : null}
          onChange={(option) => {
            const farm = farms.find((f) => f.id === option?.id);
            
            // Auto-select first available crop when farm is selected
            if (farm) {
              const availableCrops = crops.filter((crop) => {
                if (farm.id === 'farm-1') {
                  return crop.id === 'crop-1'; // AB only has Canola
                } else if (farm.id === 'farm-2') {
                  return crop.id === 'crop-2'; // BC only has Timothy Hay
                }
                return true; // Fallback: show all crops
              });
              
              // First set the farm
              setSelectedFarm(farm);
              
              // Then set the crop (this will trigger loadFieldBoundaries and loadKPISummary)
              if (availableCrops.length > 0) {
                // Use setTimeout to ensure farm is set before crop
                setTimeout(() => {
                  setSelectedCrop(availableCrops[0]);
                }, 0);
              } else {
                setSelectedCrop(null);
              }
            } else {
              setSelectedFarm(null);
              setSelectedCrop(null);
            }
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

