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
import { useEffect } from 'react';
import { APICache } from '@/lib/api/cache';

export default function DashboardPage() {
  const {
    fieldBoundaries,
    ndviGrids,
    stressIndices,
    activeMapLayer,
    isLoading,
    error,
    farms,
    crops,
    selectedFarm,
    selectedCrop,
  } = useDashboardStore();

  // Clean up expired cache on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      APICache.clearExpired();
    }
  }, []);


  return (
    <div className="min-h-screen bg-gray-100">
      <DashboardHeader />
      
      <div className="container mx-auto px-6 py-6">
        {error && (
          <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            <strong>Error:</strong> {error}
            <br />
            <small>백엔드 서버가 실행 중인지 확인하세요: http://localhost:8000</small>
          </div>
        )}
        
        {isLoading && (
          <div className="mb-4 p-4 bg-blue-100 border border-blue-400 text-blue-700 rounded">
            데이터를 불러오는 중...
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

