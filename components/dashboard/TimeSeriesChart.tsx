/**
 * Reusable time series chart component using Recharts
 */

'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TimeSeriesData } from '@/types';
import { format, parseISO } from 'date-fns';

interface TimeSeriesChartProps {
  title: string;
  data: TimeSeriesData[];
  yAxisLabel?: string;
  xAxisLabel?: string;
  dataKey?: string;
  color?: string;
  className?: string;
}

export function TimeSeriesChart({
  title,
  data,
  yAxisLabel = '',
  xAxisLabel = '',
  dataKey = 'value',
  color = '#3b82f6',
  className = '',
}: TimeSeriesChartProps) {
  // Format data for chart
  const chartData = data && data.length > 0 ? data.map((item) => ({
    ...item,
    date: format(parseISO(item.timestamp), 'MMM dd'),
    fullDate: item.timestamp,
  })) : [];

  // Show placeholder if no data
  if (!data || data.length === 0) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-4 ${className}`}>
        <h3 className="text-sm font-semibold text-gray-700 mb-4">{title}</h3>
        <div className="h-[200px] flex items-center justify-center border-2 border-dashed border-gray-300 rounded">
          <p className="text-gray-400 text-sm">데이터 로딩 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-md p-4 ${className}`}>
      <h3 className="text-sm font-semibold text-gray-700 mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            stroke="#6b7280"
            fontSize={12}
            label={{ value: xAxisLabel, position: 'insideBottom', offset: -5 }}
          />
          <YAxis
            stroke="#6b7280"
            fontSize={12}
            label={{ value: yAxisLabel, angle: -90, position: 'insideLeft' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
            }}
            labelFormatter={(label) => format(parseISO(chartData.find((d) => d.date === label)?.fullDate || ''), 'PPp')}
          />
          <Line
            type="monotone"
            dataKey={dataKey}
            stroke={color}
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

