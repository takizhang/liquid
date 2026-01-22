import axios from 'axios';
import type {
  OverviewResponse,
  IndicatorData,
  Indicator,
  Market,
  Category,
  AnalysisSummary,
  Signal,
  AskResponse
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // Health
  health: async () => {
    const { data } = await client.get('/api/health');
    return data;
  },

  // Markets
  getMarkets: async (): Promise<Market[]> => {
    const { data } = await client.get('/api/markets');
    return data;
  },

  getCategories: async (): Promise<Category[]> => {
    const { data } = await client.get('/api/categories');
    return data;
  },

  getOverview: async (): Promise<OverviewResponse> => {
    const { data } = await client.get('/api/overview');
    return data;
  },

  getMarketIndicators: async (marketId: string): Promise<Indicator[]> => {
    const { data } = await client.get(`/api/markets/${marketId}/indicators`);
    return data;
  },

  // Indicators
  getIndicatorData: async (indicatorId: string, days: number = 365): Promise<IndicatorData> => {
    const { data } = await client.get(`/api/indicators/${indicatorId}`, {
      params: { days },
    });
    return data;
  },

  getIndicatorRawData: async (
    indicatorId: string,
    startDate?: string,
    endDate?: string,
    limit: number = 500
  ) => {
    const { data } = await client.get(`/api/indicators/${indicatorId}/data`, {
      params: { start_date: startDate, end_date: endDate, limit },
    });
    return data;
  },

  // AI Analysis
  getMarketSummary: async (marketId: string, refresh: boolean = false): Promise<AnalysisSummary> => {
    const { data } = await client.get(`/api/analysis/markets/${marketId}/summary`, {
      params: { refresh },
    });
    return data;
  },

  getSignals: async (marketId?: string, severity?: string): Promise<Signal[]> => {
    const { data } = await client.get('/api/analysis/signals', {
      params: { market_id: marketId, severity },
    });
    return data;
  },

  acknowledgeSignal: async (signalId: number): Promise<{ success: boolean }> => {
    const { data } = await client.post(`/api/analysis/signals/${signalId}/acknowledge`);
    return data;
  },

  getAnalysisHistory: async (marketId: string, limit: number = 10) => {
    const { data } = await client.get(`/api/analysis/history/${marketId}`, {
      params: { limit },
    });
    return data;
  },

  askQuestion: async (question: string, contextMarket?: string): Promise<AskResponse> => {
    const { data } = await client.post('/api/analysis/ask', {
      question,
      context_market: contextMarket,
    });
    return data;
  },

  // Data Sources
  getDataSources: async () => {
    const { data } = await client.get('/api/sources');
    return data;
  },
};

export default api;
