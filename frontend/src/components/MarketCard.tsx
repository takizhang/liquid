import { useNavigate } from 'react-router-dom';
import { StatusBadge } from './StatusBadge';
import type { MarketOverview } from '../types';

interface MarketCardProps {
  market: MarketOverview;
}

export const MarketCard = ({ market }: MarketCardProps) => {
  const navigate = useNavigate();
  const { market_id, market_name, emoji, status, primary_indicator, indicators_count } = market;

  const formatValue = (value: number | undefined | null, unit?: string) => {
    if (value === undefined || value === null) return '-';

    // Format number with appropriate precision
    let formatted: string;
    if (value >= 1000) {
      formatted = value.toLocaleString('en-US', { maximumFractionDigits: 2 });
    } else if (value >= 1) {
      formatted = value.toFixed(2);
    } else {
      formatted = value.toFixed(4);
    }

    // Add unit
    if (!unit) return formatted;
    if (unit === '$') return `$${formatted}`;
    if (unit === '%') return `${formatted}%`;
    if (unit === 'T') return `$${formatted}T`;
    if (unit === 'B') return `$${formatted}B`;
    return `${formatted} ${unit}`;
  };

  const formatChange = (change: number | undefined) => {
    if (change === undefined) return '-';
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(2)}%`;
  };

  const change30d = primary_indicator?.changes['30d']?.change_pct;

  const getMarketColor = () => {
    if (market_id === 'us') return '#00aaff';
    if (market_id === 'china') return '#ff3366';
    return '#a855f7';
  };

  const color = getMarketColor();

  return (
    <div
      className="card cursor-pointer hover:shadow-[0_0_30px_rgba(0,255,136,0.15)] transition-all duration-300 transform hover:-translate-y-1 group"
      onClick={() => navigate(`/market/${market_id}`)}
      style={{ borderColor: `${color}20` }}
    >
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-3">
          <span className="text-3xl group-hover:scale-110 transition-transform">{emoji}</span>
          <h2 className="text-xl font-bold text-gray-200 tracking-wide">{market_name}</h2>
        </div>
        <StatusBadge status={status} size="lg" />
      </div>

      {primary_indicator ? (
        <div className="mb-4">
          <p className="text-sm text-gray-500 mb-1 tracking-wide">{primary_indicator.indicator.name}</p>
          <p className="text-3xl font-bold data-value" style={{ color }}>
            {formatValue(primary_indicator.current_value, primary_indicator.indicator.unit)}
          </p>
          {change30d !== undefined && (
            <p className={`text-sm font-medium mt-1 ${change30d >= 0 ? 'text-[#00ff88]' : 'text-[#ff3366]'}`}>
              30D: {formatChange(change30d)}{change30d >= 0 ? ' ▲' : ' ▼'}
            </p>
          )}
        </div>
      ) : (
        <div className="mb-4">
          <p className="text-gray-500">NO DATA</p>
        </div>
      )}

      <div className="border-t border-[rgba(255,255,255,0.05)] pt-3">
        <p className="text-sm text-gray-400">
          {status.status === 'bullish' && '🟢 流动性充裕，利好风险资产'}
          {status.status === 'slightly_bullish' && '🟢 流动性边际改善'}
          {status.status === 'neutral' && '🟡 流动性中性'}
          {status.status === 'slightly_bearish' && '🔴 流动性边际收紧'}
          {status.status === 'bearish' && '🔴 流动性收紧，风险资产承压'}
        </p>
        <p className="text-xs text-gray-600 mt-2 tracking-wider">{indicators_count} INDICATORS</p>
      </div>

      <div className="mt-4 text-center">
        <span
          className="text-sm tracking-wider transition-all group-hover:tracking-widest"
          style={{ color }}
        >
          EXPLORE →
        </span>
      </div>
    </div>
  );
};
