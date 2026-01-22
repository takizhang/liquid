export interface Market {
  id: string;
  name: string;
  emoji: string;
}

export interface Category {
  id: string;
  name: string;
  name_en: string;
  description: string;
  color: string;
}

export interface Indicator {
  id: string;
  name: string;
  name_en?: string;
  source: string;
  market: string;
  category?: string;
  unit?: string;
  direction?: string;
  impact_up?: string;
  impact_down?: string;
  description?: string;
  is_primary: boolean;
}

export interface DataPoint {
  timestamp: string;
  value: number;
  indicator_id: string;
}

export interface ChangeStats {
  change: number;
  change_pct: number;
  from_value: number;
  from_date: string;
}

export interface Status {
  status: string;
  color: string;
  emoji: string;
}

export interface IndicatorData {
  indicator: Indicator;
  current_value?: number;
  current_date?: string;
  changes: Record<string, ChangeStats>;
  status: Status;
  data_points: DataPoint[];
}

export interface MarketOverview {
  market_id: string;
  market_name: string;
  emoji: string;
  status: Status;
  primary_indicator?: IndicatorData;
  indicators_count: number;
}

export interface OverviewResponse {
  markets: MarketOverview[];
  last_updated: string;
}

export interface Signal {
  indicator_id: string;
  indicator_name: string;
  signal_type: string;
  severity: string;
  description: string;
  current_value: number;
  change_pct?: number;
  detected_at: string;
}

export interface AnalysisSummary {
  summary: string;
  signals: Array<{
    name: string;
    direction: string;
    significance: string;
  }>;
  risk_level: string;
  recommendations: string[];
  confidence: number;
  reasoning: string;
  generated_at: string;
  cached?: boolean;
  error?: boolean;
}

export interface AskResponse {
  question: string;
  answer: string;
  context_market?: string;
  error?: boolean;
}
