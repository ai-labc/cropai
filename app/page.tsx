/**
 * Main Dashboard Page
 */

'use client';

import { DashboardHeader } from '@/components/dashboard/DashboardHeader';
import { KPISection } from '@/components/dashboard/KPISection';
import { FarmMap } from '@/components/dashboard/FarmMap';
import { ChartsSection } from '@/components/dashboard/ChartsSection';
import { TimelineChart } from '@/components/dashboard/TimelineChart';
import { useDashboardStore } from '@/store/dashboardStore';

export default function DashboardPage() {
  const {
    fieldBoundaries,
    ndviGrids,
    stressIndices,
    activeMapLayer,
    isLoading,
    error,
  } = useDashboardStore();

  return (
    <div className="min-h-screen bg-gray-100">
      <DashboardHeader />
      
      <div className="container mx-auto px-6 py-6">
        {error && (
          <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        <KPISection />

        <div className="grid grid-cols-12 gap-6">
          {/* Main Map Section */}
          <div className="col-span-8">
            <FarmMap
              fieldBoundaries={fieldBoundaries}
              ndviGrids={ndviGrids}
              stressIndices={stressIndices}
              activeLayer={activeMapLayer}
              className="h-full"
            />
            <TimelineChart />
          </div>

          {/* Side Charts Section */}
          <div className="col-span-4">
            <ChartsSection />
          </div>
        </div>
      </div>
    </div>
  );
}

