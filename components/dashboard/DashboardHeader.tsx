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
    initializeDashboard();
  }, [initializeDashboard]);

  const farmOptions = farms.map((farm) => ({ id: farm.id, name: farm.name }));
  const cropOptions = crops.map((crop) => ({ id: crop.id, name: crop.name }));

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
          disabled={crops.length === 0}
        />
      </div>
    </div>
  );
}

