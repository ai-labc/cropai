/**
 * Main Dashboard Page
 */

'use client';

import { DashboardHeader } from '@/components/dashboard/DashboardHeader';
import { KPISection } from '@/components/dashboard/KPISection';
import { FarmMap } from '@/components/dashboard/FarmMap';
import { ChartsSection } from '@/components/dashboard/ChartsSection';
import { TimelineChart } from '@/components/dashboard/TimelineChart';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
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
      
      <div className="container mx-auto px-4 sm:px-6 py-4 sm:py-6">
        {error && (
          <ErrorMessage
            message={error}
            details={error.includes('http://') || error.includes('https://') ? `API URL: ${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}` : undefined}
            onRetry={() => {
              const store = useDashboardStore.getState();
              if (store.selectedFarm && store.selectedCrop) {
                store.loadFieldBoundaries();
                store.loadKPISummary();
              } else {
                store.initializeDashboard();
              }
            }}
            onDismiss={() => useDashboardStore.getState().error && useDashboardStore.setState({ error: null })}
            errorType={
              error.includes('timeout') || error.includes('시간이 초과') ? 'timeout' :
              error.includes('네트워크') || error.includes('CORS') || error.includes('Failed to fetch') ? 'network' :
              error.includes('API error') || error.includes('404') || error.includes('500') ? 'api' :
              'unknown'
            }
          />
        )}
        
        {isLoading && (
          <div className="mb-4 p-4 bg-blue-100 border border-blue-400 text-blue-700 rounded flex items-center gap-2">
            <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>데이터를 불러오는 중...</span>
          </div>
        )}

        <KPISection />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 sm:gap-6">
          {/* Main Map Section */}
          <div className="lg:col-span-8 order-1">
            <div className="h-[400px] sm:h-[500px] lg:h-[600px] mb-4">
              <FarmMap
                fieldBoundaries={fieldBoundaries}
                ndviGrids={ndviGrids}
                stressIndices={stressIndices}
                activeLayer={activeMapLayer}
                className="h-full w-full"
              />
            </div>
            <TimelineChart />
          </div>

          {/* Side Charts Section */}
          <div className="lg:col-span-4 order-2">
            <ChartsSection />
          </div>
        </div>
      </div>
    </div>
  );
}

