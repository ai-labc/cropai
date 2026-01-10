/**
 * Dashboard header with filters (Farm, Crop selectors)
 */

'use client';

import { Select } from '@/components/ui/Select';
import { LocationInput } from '@/components/ui/LocationInput';
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
    locationInput,
    setLocationInput,
    findNearestFarm,
    searchResult,
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

  // Sort farms alphabetically by name
  const farmOptions = [...farms]
    .sort((a, b) => a.name.localeCompare(b.name))
    .map((farm) => ({ id: farm.id, name: farm.name }));
  
  // Filter and sort crops based on selected farm
  // Hartland Colony (farm-1) only has Canola (crop-1)
  // BC farm (farm-2) only has Timothy Hay (crop-2)
  const cropOptions = selectedFarm
    ? crops
        .filter((crop) => {
          if (selectedFarm.id === 'farm-1') {
            return crop.id === 'crop-1'; // AB only has Canola
          } else if (selectedFarm.id === 'farm-2') {
            return crop.id === 'crop-2'; // BC only has Timothy Hay
          }
          return true; // Fallback: show all crops
        })
        .sort((a, b) => a.name.localeCompare(b.name))
        .map((crop) => ({ id: crop.id, name: crop.name }))
    : [];

  return (
    <div className="bg-primary-dark px-4 sm:px-6 py-4 flex flex-col gap-4">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <h1 className="text-2xl sm:text-3xl font-bold text-white">Dashboard</h1>
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 sm:gap-6 w-full sm:w-auto flex-wrap">
          <Select
            label="Farm"
            options={farmOptions}
            selected={selectedFarm ? { id: selectedFarm.id, name: selectedFarm.name } : null}
            onChange={(option) => {
              const farm = farms.find((f) => f.id === option?.id);
              
              // Clear search result when farm is manually selected from dropdown
              useDashboardStore.getState().setSearchResult(null);
              
              // Auto-select default crop when farm is selected
              if (farm) {
                // First set the farm (this will update locationInput)
                setSelectedFarm(farm);
                
                // Then set the default crop for this farm
                if (farm.defaultCropId && crops.length > 0) {
                  const defaultCrop = crops.find(c => c.id === farm.defaultCropId);
                  if (defaultCrop) {
                    // Use setTimeout to ensure farm is set before crop
                    setTimeout(() => {
                      setSelectedCrop(defaultCrop);
                    }, 0);
                  } else {
                    setSelectedCrop(null);
                  }
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
          <LocationInput
            value={locationInput}
            onChange={setLocationInput}
            onSearch={findNearestFarm}
            disabled={farms.length === 0}
            searchResult={searchResult}
          />
        </div>
      </div>
      {searchResult && searchResult.status !== 'idle' && searchResult.status !== 'searching' && searchResult.message && (
        <div className={`w-full px-3 py-2 rounded-lg text-sm ${
          searchResult.status === 'success' 
            ? 'bg-green-100 text-green-800 border border-green-300' 
            : 'bg-yellow-100 text-yellow-800 border border-yellow-300'
        }`}>
          {searchResult.status === 'success' ? '✓ ' : '⚠ '}
          {searchResult.message}
        </div>
      )}
    </div>
  );
}

