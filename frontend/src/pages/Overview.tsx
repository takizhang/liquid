import { useOverview } from '../hooks/useApi';
import { MarketCard } from '../components/MarketCard';
import { SignalAlert } from '../components/SignalAlert';

export const Overview = () => {
  const { data, isLoading, error } = useOverview();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-[#00ff88] animate-pulse tracking-widest">LOADING...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-[#ff3366] mb-2 glow-red">CONNECTION ERROR</p>
          <p className="text-sm text-gray-500">请确保后端服务运行在 8000 端口</p>
        </div>
      </div>
    );
  }

  if (!data || data.markets.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-gray-400 mb-2">NO DATA AVAILABLE</p>
          <p className="text-sm text-gray-600">请运行数据初始化脚本获取数据</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[#00ff88] glow-green mb-2 tracking-wider">
          GLOBAL LIQUIDITY
        </h1>
        <p className="text-gray-500 tracking-wide">全球流动性实时监控</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
        <div className="lg:col-span-3">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {data.markets.map((market) => (
              <MarketCard key={market.market_id} market={market} />
            ))}
          </div>
        </div>

        <div className="lg:col-span-1">
          <SignalAlert limit={5} />
        </div>
      </div>

      <div className="card">
        <h3 className="font-semibold text-[#00ff88] mb-4 tracking-wider">SIGNAL GUIDE</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="p-3 rounded-lg bg-[rgba(0,255,136,0.05)] border border-[rgba(0,255,136,0.1)]">
            <p className="font-medium text-[#00ff88]">🟢 BULLISH</p>
            <p className="text-gray-400 mt-1">流动性扩张，利好风险资产</p>
          </div>
          <div className="p-3 rounded-lg bg-[rgba(255,170,0,0.05)] border border-[rgba(255,170,0,0.1)]">
            <p className="font-medium text-[#ffaa00]">🟡 NEUTRAL</p>
            <p className="text-gray-400 mt-1">信号混合，关注趋势变化</p>
          </div>
          <div className="p-3 rounded-lg bg-[rgba(255,51,102,0.05)] border border-[rgba(255,51,102,0.1)]">
            <p className="font-medium text-[#ff3366]">🔴 BEARISH</p>
            <p className="text-gray-400 mt-1">流动性收紧，建议谨慎</p>
          </div>
        </div>
      </div>

      <div className="mt-4 text-right text-xs text-gray-600 tracking-wider">
        LAST UPDATE: {new Date(data.last_updated).toLocaleString('zh-CN')}
      </div>
    </div>
  );
};
