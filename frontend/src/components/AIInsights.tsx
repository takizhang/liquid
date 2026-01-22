import { useState } from 'react';
import { useMarketSummary } from '../hooks/useApi';
import type { AnalysisSummary } from '../types';

interface AIInsightsProps {
  marketId: string;
}

const RiskBadge = ({ level }: { level: string }) => {
  const styles: Record<string, string> = {
    low: 'bg-[rgba(0,255,136,0.15)] text-[#00ff88] border-[rgba(0,255,136,0.3)]',
    medium: 'bg-[rgba(255,170,0,0.15)] text-[#ffaa00] border-[rgba(255,170,0,0.3)]',
    high: 'bg-[rgba(255,51,102,0.15)] text-[#ff3366] border-[rgba(255,51,102,0.3)]',
    unknown: 'bg-[rgba(128,128,128,0.15)] text-gray-400 border-[rgba(128,128,128,0.3)]',
  };

  return (
    <span className={`px-3 py-1 rounded-full text-xs font-medium border ${styles[level] || styles.unknown}`}>
      {level === 'low' && 'LOW RISK'}
      {level === 'medium' && 'MEDIUM RISK'}
      {level === 'high' && 'HIGH RISK'}
      {level === 'unknown' && 'NOT CONFIGURED'}
    </span>
  );
};

const SignalItem = ({ signal }: { signal: { name: string; direction: string; significance: string } }) => {
  const directionIcon = signal.direction === 'up' ? '▲' : signal.direction === 'down' ? '▼' : '→';
  const color = signal.direction === 'up' ? '#00ff88' : signal.direction === 'down' ? '#ff3366' : '#ffaa00';

  return (
    <div className="flex items-center gap-2 text-sm">
      <span style={{ color }}>{directionIcon}</span>
      <span className="text-gray-300">{signal.name}</span>
      {signal.significance === 'high' && (
        <span className="text-xs text-[#ff3366]">HIGH</span>
      )}
    </div>
  );
};

export const AIInsights = ({ marketId }: AIInsightsProps) => {
  const { data, isLoading, error } = useMarketSummary(marketId);
  const [showReasoning, setShowReasoning] = useState(false);

  if (isLoading) {
    return (
      <div className="ai-card card">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-xl animate-pulse">🤖</span>
          <span className="text-[#a855f7] tracking-wider">AI ANALYZING...</span>
        </div>
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-[rgba(168,85,247,0.2)] rounded w-3/4"></div>
          <div className="h-4 bg-[rgba(168,85,247,0.2)] rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="ai-card card">
        <div className="flex items-center gap-2 text-[#ff3366]">
          <span>⚠️</span>
          <span className="tracking-wider">AI ANALYSIS FAILED</span>
        </div>
      </div>
    );
  }

  const summary = data as AnalysisSummary;

  return (
    <div className="ai-card card">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-bold text-lg flex items-center gap-2 text-[#a855f7] tracking-wider">
          <span>🤖</span> AI INSIGHTS
        </h3>
      </div>

      {summary.error ? (
        <div className="p-4 bg-[rgba(255,51,102,0.1)] rounded-lg border border-[rgba(255,51,102,0.2)]">
          <p className="text-[#ff3366]">{summary.summary}</p>
        </div>
      ) : (
        <>
          {/* 核心结论 */}
          <div className="mb-4 p-4 bg-[rgba(168,85,247,0.1)] rounded-lg border border-[rgba(168,85,247,0.2)]">
            <p className="text-gray-200">{summary.summary}</p>
          </div>

          {/* 风险等级 */}
          <div className="flex items-center gap-3 mb-4">
            <span className="text-sm text-gray-500 tracking-wide">RISK:</span>
            <RiskBadge level={summary.risk_level} />
            <span className="text-xs text-gray-500 tracking-wider">
              CONFIDENCE: {(summary.confidence * 100).toFixed(0)}%
            </span>
          </div>

          {/* 关键信号 */}
          {summary.signals && summary.signals.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-[#a855f7] mb-2 tracking-wider">KEY SIGNALS</h4>
              <div className="space-y-2">
                {summary.signals.map((signal, i) => (
                  <SignalItem key={i} signal={signal} />
                ))}
              </div>
            </div>
          )}

          {/* 建议 */}
          {summary.recommendations && summary.recommendations.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-[#a855f7] mb-2 tracking-wider">RECOMMENDATIONS</h4>
              <ul className="space-y-1">
                {summary.recommendations.map((rec, i) => (
                  <li key={i} className="text-sm text-gray-400 flex items-start gap-2">
                    <span className="text-[#a855f7]">›</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 推理过程 */}
          {summary.reasoning && (
            <div className="mt-4">
              <button
                onClick={() => setShowReasoning(!showReasoning)}
                className="text-sm text-[#a855f7] hover:text-[#a855f7]/80 tracking-wider"
              >
                {showReasoning ? '▼ HIDE' : '▶ SHOW'} REASONING
              </button>
              {showReasoning && (
                <p className="mt-2 text-sm text-gray-400 bg-[rgba(168,85,247,0.05)] p-3 rounded border border-[rgba(168,85,247,0.1)]">
                  {summary.reasoning}
                </p>
              )}
            </div>
          )}

          {/* 生成时间 */}
          <div className="mt-4 text-xs text-gray-600 tracking-wider">
            GENERATED: {new Date(summary.generated_at).toLocaleString('zh-CN')}
          </div>
        </>
      )}
    </div>
  );
};
