import { useParams, Link } from 'react-router-dom';
import { useMarketIndicators, useIndicatorData } from '../hooks/useApi';
import { IndicatorCard } from '../components/IndicatorCard';
import { AIInsights } from '../components/AIInsights';
import { SignalAlert } from '../components/SignalAlert';

const marketNames: Record<string, { name: string; emoji: string; color: string }> = {
  us: { name: '美国', emoji: '🇺🇸', color: '#00aaff' },
  china: { name: '中国', emoji: '🇨🇳', color: '#ff3366' },
  crypto: { name: '加密货币', emoji: '🪙', color: '#a855f7' },
};

export const MarketDetail = () => {
  const { marketId } = useParams<{ marketId: string }>();
  const { data: indicators, isLoading } = useMarketIndicators(marketId || '');

  const market = marketNames[marketId || ''] || { name: marketId, emoji: '📊', color: '#00ff88' };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-[#00ff88] animate-pulse tracking-widest">LOADING...</div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <Link to="/" className="text-sm tracking-wider mb-2 inline-block text-[#00ff88] hover:text-[#00ff88]/80">
          ← BACK TO OVERVIEW
        </Link>
        <div className="flex items-center gap-3 mt-2">
          <span className="text-4xl">{market.emoji}</span>
          <div>
            <h1 className="text-2xl font-bold tracking-wider" style={{ color: market.color }}>
              {market.name.toUpperCase()} MARKET
            </h1>
            <p className="text-gray-500 tracking-wide">{indicators?.length || 0} INDICATORS</p>
          </div>
        </div>
      </div>

      {/* AI Insights */}
      {marketId && (
        <div className="mb-8">
          <AIInsights marketId={marketId} />
        </div>
      )}

      {/* Signals */}
      <div className="mb-8">
        <SignalAlert marketId={marketId} limit={3} />
      </div>

      {/* Indicators Grid */}
      <div className="mb-6">
        <h2 className="text-xl font-bold text-[#00ff88] mb-4 tracking-wider">ALL INDICATORS</h2>
        {indicators && indicators.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {indicators.map((indicator) => (
              <IndicatorCardWrapper key={indicator.id} indicatorId={indicator.id} />
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500 tracking-wider">
            NO INDICATORS AVAILABLE
          </div>
        )}
      </div>
    </div>
  );
};

// Wrapper component to fetch full indicator data
const IndicatorCardWrapper = ({ indicatorId }: { indicatorId: string }) => {
  const { data, isLoading } = useIndicatorData(indicatorId, 90);

  if (isLoading) {
    return (
      <div className="card animate-pulse">
        <div className="h-4 bg-[rgba(0,255,136,0.1)] rounded w-3/4 mb-4"></div>
        <div className="h-8 bg-[rgba(0,255,136,0.1)] rounded w-1/2 mb-4"></div>
        <div className="h-20 bg-[rgba(0,255,136,0.1)] rounded"></div>
      </div>
    );
  }

  if (!data) return null;

  return <IndicatorCard data={data} />;
};
