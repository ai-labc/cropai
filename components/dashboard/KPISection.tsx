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
      <div className="grid grid-cols-3 gap-6 mb-6">
        <div className="bg-white rounded-lg shadow-md p-6 animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6 animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-3 gap-6 mb-6">
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

