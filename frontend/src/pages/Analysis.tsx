import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useSignals } from '../hooks/useApi';
import { AIInsights } from '../components/AIInsights';

const markets = [
  { id: 'us', name: '美国', emoji: '🇺🇸' },
  { id: 'china', name: '中国', emoji: '🇨🇳' },
  { id: 'crypto', name: '加密货币', emoji: '🪙' },
];

export const Analysis = () => {
  const { marketId } = useParams<{ marketId: string }>();
  const [selectedMarket, setSelectedMarket] = useState(marketId || 'us');
  const { data: signals } = useSignals();

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">🤖 AI Analysis Center</h1>
        <p className="text-gray-600">AI-powered market insights</p>
      </div>

      {/* Market Selector */}
      <div className="flex gap-2 mb-6">
        {markets.map((m) => (
          <button
            key={m.id}
            onClick={() => setSelectedMarket(m.id)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              selectedMarket === m.id
                ? 'bg-purple-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {m.emoji} {m.name}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* AI Insights */}
        <div className="lg:col-span-2">
          <AIInsights marketId={selectedMarket} />
        </div>

        {/* Sidebar */}
        <div className="lg:col-span-1 space-y-6">
          {/* Active Signals */}
          <div className="card">
            <h3 className="font-bold mb-4">📡 Active Signals</h3>
            {signals && signals.length > 0 ? (
              <div className="space-y-3">
                {signals.slice(0, 5).map((signal, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg bg-gray-50 border-l-4 ${
                      signal.severity === 'critical'
                        ? 'border-red-500'
                        : signal.severity === 'warning'
                        ? 'border-yellow-500'
                        : 'border-blue-500'
                    }`}
                  >
                    <p className="text-sm font-medium">{signal.indicator_name}</p>
                    <p className="text-xs text-gray-600 mt-1">{signal.description}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">暂无活跃信号</p>
            )}
          </div>

          {/* Quick Links */}
          <div className="card">
            <h3 className="font-bold mb-4">🔗 Quick Links</h3>
            <div className="space-y-2">
              {markets.map((m) => (
                <Link
                  key={m.id}
                  to={`/market/${m.id}`}
                  className="block p-2 rounded hover:bg-gray-50 text-sm"
                >
                  {m.emoji} {m.name} Market →
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
