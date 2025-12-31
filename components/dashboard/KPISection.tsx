/**
 * KPI Cards section
 */

'use client';

import { KPICard } from './KPICard';
import { useDashboardStore } from '@/store/dashboardStore';

export function KPISection() {
  const { kpiSummary } = useDashboardStore();

  if (!kpiSummary) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 mb-4 sm:mb-6">
        <div className="bg-white rounded-lg shadow-md p-4 sm:p-6 animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-4 sm:p-6 animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-4 sm:p-6 animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 mb-4 sm:mb-6">
      <KPICard
        title="PRODUCTIVITY INCREASE"
        value={kpiSummary.productivityIncrease}
        trend="up"
      />
      <KPICard
        title="WATER EFFICIENCY"
        value={kpiSummary.waterEfficiency}
        trend="up"
      />
      <KPICard
        title="ESG DATA ACCURACY"
        value={kpiSummary.esgAccuracy}
        unit="%"
        trend="neutral"
      />
    </div>
  );
}

