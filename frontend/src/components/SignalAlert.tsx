import { useSignals } from '../hooks/useApi';
import type { Signal } from '../types';

interface SignalAlertProps {
  marketId?: string;
  limit?: number;
}

const SeverityIcon = ({ severity }: { severity: string }) => {
  switch (severity) {
    case 'critical':
      return <span className="drop-shadow-[0_0_6px_rgba(255,51,102,0.8)]">🔴</span>;
    case 'warning':
      return <span className="drop-shadow-[0_0_6px_rgba(255,170,0,0.8)]">🟡</span>;
    default:
      return <span className="drop-shadow-[0_0_6px_rgba(0,170,255,0.8)]">🔵</span>;
  }
};

export const SignalAlert = ({ marketId, limit = 5 }: SignalAlertProps) => {
  const { data: signals, isLoading } = useSignals(marketId);

  if (isLoading) {
    return (
      <div className="card">
        <h3 className="font-bold mb-4 text-[#00ff88] tracking-wider">📡 LIVE SIGNALS</h3>
        <div className="animate-pulse space-y-2">
          <div className="h-4 bg-[rgba(0,255,136,0.1)] rounded"></div>
          <div className="h-4 bg-[rgba(0,255,136,0.1)] rounded w-3/4"></div>
        </div>
      </div>
    );
  }

  const displaySignals = (signals || []).slice(0, limit);

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">
        <h3 className="font-bold text-[#00ff88] tracking-wider">📡 LIVE SIGNALS</h3>
        <span className="w-2 h-2 bg-[#00ff88] rounded-full animate-pulse"></span>
      </div>
      <p className="text-xs text-gray-500 mb-4 tracking-wide">
        自动检测 | 🔴≥10% 🟡5-10% 🔵2-5%
      </p>
      {displaySignals.length === 0 ? (
        <div className="text-center py-4">
          <p className="text-gray-500 text-sm">NO ACTIVE SIGNALS</p>
          <p className="text-xs text-gray-600 mt-1">市场平静</p>
        </div>
      ) : (
        <div className="space-y-3">
          {displaySignals.map((signal: Signal, index: number) => (
            <div
              key={index}
              className={`p-3 rounded-lg bg-[rgba(15,15,25,0.5)] signal-${signal.severity} border border-[rgba(255,255,255,0.05)]`}
            >
              <div className="flex items-start gap-2">
                <SeverityIcon severity={signal.severity} />
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-200 tracking-wide">
                    {signal.indicator_name}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    {signal.description}
                  </p>
                  <p className="text-xs text-gray-600 mt-1 tracking-wider">
                    {new Date(signal.detected_at).toLocaleString('zh-CN')}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
