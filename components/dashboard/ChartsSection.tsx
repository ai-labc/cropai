/**
 * Side charts section (Soil Moisture, Yield Prediction, Carbon Metrics)
 */

'use client';

import { TimeSeriesChart } from './TimeSeriesChart';
import { useDashboardStore } from '@/store/dashboardStore';

export function ChartsSection() {
  const { fieldBoundaries, soilMoisture, yieldPrediction, carbonMetrics } = useDashboardStore();

  // Get data for first field (or combine all fields)
  const firstFieldId = fieldBoundaries.length > 0 ? fieldBoundaries[0].id : null;
  const soilData = firstFieldId ? soilMoisture.get(firstFieldId) || [] : [];
  const yieldData = firstFieldId ? yieldPrediction.get(firstFieldId) || [] : [];
  const carbonData = firstFieldId ? carbonMetrics.get(firstFieldId) || [] : [];

  return (
    <div className="flex flex-col gap-4">
      {/* Weather data is used only for backend calculations (KPI, Yield, Carbon), not displayed in UI */}
      <TimeSeriesChart
        title="SOIL MOISTURE"
        data={soilData}
        yAxisLabel="%"
        xAxisLabel="Last 30 days"
        color="#3b82f6"
      />
      <TimeSeriesChart
        title="YIELD PREDICTION"
        data={yieldData}
        yAxisLabel="tons"
        xAxisLabel="Last 30 days"
        color="#22c55e"
      />
      <TimeSeriesChart
        title="CARBON METRICS"
        data={carbonData}
        yAxisLabel="%"
        xAxisLabel="Last 30 days"
        color="#10b981"
      />
    </div>
  );
}

