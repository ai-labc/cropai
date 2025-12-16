/**
 * Bottom timeline/trend chart
 */

'use client';

import { TimeSeriesChart } from './TimeSeriesChart';
import { useDashboardStore } from '@/store/dashboardStore';

export function TimelineChart() {
  const { fieldBoundaries, soilMoisture } = useDashboardStore();
  
  // Use soil moisture as example for timeline (can be replaced with any aggregated metric)
  const firstFieldId = fieldBoundaries.length > 0 ? fieldBoundaries[0].id : null;
  const data = firstFieldId ? soilMoisture.get(firstFieldId) || [] : [];

  return (
    <div className="mt-6">
      <TimeSeriesChart
        title="TREND ANALYSIS"
        data={data}
        yAxisLabel="%"
        xAxisLabel="Time"
        color="#22c55e"
        className="h-64"
      />
    </div>
  );
}

