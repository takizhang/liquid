import { useNavigate } from 'react-router-dom';
import { IndicatorChart } from './IndicatorChart';
import { StatusBadge } from './StatusBadge';
import type { IndicatorData } from '../types';

interface IndicatorCardProps {
  data: IndicatorData;
  showChart?: boolean;
}

export const IndicatorCard = ({ data, showChart = true }: IndicatorCardProps) => {
  const navigate = useNavigate();
  const { indicator, current_value, changes, status, data_points } = data;

  const formatValue = (value: number | undefined | null, unit?: string) => {
    if (value === undefined || value === null) return '-';
    if (unit === 'T') return `$${value.toFixed(2)}T`;
    if (unit === 'B') return `$${value.toFixed(1)}B`;
    if (unit === '%') return `${value.toFixed(2)}%`;
    return value.toFixed(2);
  };

  const formatChange = (change: number | undefined) => {
    if (change === undefined) return '-';
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(2)}%`;
  };

  const change30d = changes['30d']?.change_pct;
  const change7d = changes['7d']?.change_pct;

  return (
    <div
      className="card cursor-pointer hover:shadow-[0_0_25px_rgba(0,255,136,0.1)] transition-all duration-300 group"
      onClick={() => navigate(`/indicator/${indicator.id}`)}
    >
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="font-semibold text-gray-200 tracking-wide group-hover:text-[#00ff88] transition-colors">
            {indicator.name}
          </h3>
          {indicator.name_en && (
            <p className="text-xs text-gray-500">{indicator.name_en}</p>
          )}
        </div>
        <StatusBadge status={status} size="sm" />
      </div>

      <div className="mb-4">
        <p className="text-2xl font-bold text-[#00ff88] data-value">
          {formatValue(current_value, indicator.unit)}
        </p>
        <div className="flex gap-4 mt-1">
          {change7d !== undefined && (
            <span className={`text-sm data-value ${change7d >= 0 ? 'text-[#00ff88]' : 'text-[#ff3366]'}`}>
              7D: {formatChange(change7d)}
            </span>
          )}
          {change30d !== undefined && (
            <span className={`text-sm data-value ${change30d >= 0 ? 'text-[#00ff88]' : 'text-[#ff3366]'}`}>
              30D: {formatChange(change30d)}
            </span>
          )}
        </div>
      </div>

      {showChart && data_points && data_points.length > 0 && (
        <div className="mb-4 -mx-2">
          <IndicatorChart dataPoints={data_points.slice(-90)} height={80} mini />
        </div>
      )}

      <div className="border-t border-[rgba(255,255,255,0.05)] pt-3 mt-auto">
        <p className="text-xs font-medium text-gray-500 mb-1 tracking-wide">
          {indicator.direction === 'up_is_loose' ? '▲ 上升' : '▼ 下降'}
        </p>
        <p className="text-xs text-gray-400">
          {indicator.direction === 'up_is_loose' ? indicator.impact_up : indicator.impact_down}
        </p>
      </div>
    </div>
  );
};
