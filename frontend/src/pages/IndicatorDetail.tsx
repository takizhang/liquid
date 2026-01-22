import { useParams, Link } from 'react-router-dom';
import { useIndicatorData } from '../hooks/useApi';
import { IndicatorChart } from '../components/IndicatorChart';
import { StatusBadge } from '../components/StatusBadge';

export const IndicatorDetail = () => {
  const { indicatorId } = useParams<{ indicatorId: string }>();
  const { data, isLoading, error } = useIndicatorData(indicatorId || '', 365);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-[#00ff88] animate-pulse tracking-widest">LOADING...</div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-[#ff3366] mb-2 glow-red">ERROR</p>
          <Link to="/" className="text-[#00aaff] hover:text-[#00ff88] tracking-wider">
            ← BACK TO OVERVIEW
          </Link>
        </div>
      </div>
    );
  }

  const { indicator, current_value, changes, status, data_points } = data;

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

  return (
    <div>
      {/* Breadcrumb */}
      <div className="mb-6 text-sm tracking-wider">
        <Link to="/" className="text-[#00ff88] hover:text-[#00ff88]/80">
          OVERVIEW
        </Link>
        <span className="mx-2 text-gray-600">/</span>
        <Link
          to={`/market/${indicator.market}`}
          className="text-[#00aaff] hover:text-[#00aaff]/80"
        >
          {indicator.market.toUpperCase()}
        </Link>
        <span className="mx-2 text-gray-600">/</span>
        <span className="text-gray-400">{indicator.name}</span>
      </div>

      {/* Header */}
      <div className="card mb-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-2xl font-bold text-[#00ff88] glow-green tracking-wider">{indicator.name}</h1>
            {indicator.name_en && (
              <p className="text-gray-500 tracking-wide">{indicator.name_en}</p>
            )}
          </div>
          <StatusBadge status={status} size="lg" />
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="p-3 rounded-lg bg-[rgba(0,255,136,0.05)] border border-[rgba(0,255,136,0.1)]">
            <p className="text-sm text-gray-500 tracking-wide">当前值</p>
            <p className="text-2xl font-bold text-[#00ff88] data-value">
              {formatValue(current_value, indicator.unit)}
            </p>
          </div>
          <div className="p-3 rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.05)]">
            <p className="text-sm text-gray-500 tracking-wide">7D</p>
            <p className={`text-xl font-semibold data-value ${
              (changes['7d']?.change_pct || 0) >= 0 ? 'text-[#00ff88]' : 'text-[#ff3366]'
            }`}>
              {formatChange(changes['7d']?.change_pct)}
            </p>
          </div>
          <div className="p-3 rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.05)]">
            <p className="text-sm text-gray-500 tracking-wide">30D</p>
            <p className={`text-xl font-semibold data-value ${
              (changes['30d']?.change_pct || 0) >= 0 ? 'text-[#00ff88]' : 'text-[#ff3366]'
            }`}>
              {formatChange(changes['30d']?.change_pct)}
            </p>
          </div>
          <div className="p-3 rounded-lg bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.05)]">
            <p className="text-sm text-gray-500 tracking-wide">90D</p>
            <p className={`text-xl font-semibold data-value ${
              (changes['90d']?.change_pct || 0) >= 0 ? 'text-[#00ff88]' : 'text-[#ff3366]'
            }`}>
              {formatChange(changes['90d']?.change_pct)}
            </p>
          </div>
        </div>

        {/* Chart */}
        <div className="border-t border-[rgba(0,255,136,0.1)] pt-4">
          <IndicatorChart
            dataPoints={data_points}
            title="HISTORICAL DATA (1 YEAR)"
            unit={indicator.unit}
            height={400}
          />
        </div>
      </div>

      {/* Impact Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="card" style={{ borderColor: 'rgba(0, 255, 136, 0.2)' }}>
          <h3 className="font-semibold text-[#00ff88] mb-2 tracking-wider">▲ 上涨影响</h3>
          <p className="text-gray-400">{indicator.impact_up || '暂无信息'}</p>
        </div>
        <div className="card" style={{ borderColor: 'rgba(255, 51, 102, 0.2)' }}>
          <h3 className="font-semibold text-[#ff3366] mb-2 tracking-wider">▼ 下跌影响</h3>
          <p className="text-gray-400">{indicator.impact_down || '暂无信息'}</p>
        </div>
      </div>

      {/* Metadata */}
      <div className="card">
        <h3 className="font-semibold text-[#00ff88] mb-4 tracking-wider">INDICATOR DETAILS</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-gray-500 tracking-wide">数据源</p>
            <p className="font-medium text-gray-300">{indicator.source}</p>
          </div>
          <div>
            <p className="text-gray-500 tracking-wide">市场</p>
            <p className="font-medium text-gray-300">{indicator.market.toUpperCase()}</p>
          </div>
          <div>
            <p className="text-gray-500 tracking-wide">单位</p>
            <p className="font-medium text-gray-300">{indicator.unit || '-'}</p>
          </div>
          <div>
            <p className="text-gray-500 tracking-wide">方向</p>
            <p className="font-medium text-gray-300">
              {indicator.direction === 'up_is_loose' ? '↑ = 宽松' : '↓ = 宽松'}
            </p>
          </div>
        </div>
        {indicator.description && (
          <div className="mt-4 pt-4 border-t border-[rgba(255,255,255,0.05)]">
            <p className="text-gray-500 text-sm tracking-wide">描述</p>
            <p className="text-gray-400">{indicator.description}</p>
          </div>
        )}
      </div>
    </div>
  );
};
