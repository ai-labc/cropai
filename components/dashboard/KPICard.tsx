/**
 * KPI Card component for displaying key metrics
 */

'use client';

interface KPICardProps {
  title: string;
  value: string | number;
  unit?: string;
  trend?: 'up' | 'down' | 'neutral';
  className?: string;
}

export function KPICard({ title, value, unit, trend = 'neutral', className = '' }: KPICardProps) {
  const trendColor = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-gray-700',
  }[trend];

  const displayValue = typeof value === 'number' 
    ? `${value > 0 ? '+' : ''}${value}${unit || '%'}`
    : `${value}${unit || ''}`;

  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-2">
        {title}
      </h3>
      <p className={`text-3xl font-bold ${trendColor}`}>
        {displayValue}
      </p>
    </div>
  );
}

