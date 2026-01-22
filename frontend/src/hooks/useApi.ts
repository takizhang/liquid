import { useQuery, useMutation } from '@tanstack/react-query';
import api from '../api/client';

export const useOverview = () => {
  return useQuery({
    queryKey: ['overview'],
    queryFn: api.getOverview,
    refetchInterval: 60000,
  });
};

export const useMarkets = () => {
  return useQuery({
    queryKey: ['markets'],
    queryFn: api.getMarkets,
  });
};

export const useCategories = () => {
  return useQuery({
    queryKey: ['categories'],
    queryFn: api.getCategories,
  });
};

export const useMarketIndicators = (marketId: string) => {
  return useQuery({
    queryKey: ['market-indicators', marketId],
    queryFn: () => api.getMarketIndicators(marketId),
    enabled: !!marketId,
  });
};

export const useIndicatorData = (indicatorId: string, days: number = 365) => {
  return useQuery({
    queryKey: ['indicator', indicatorId, days],
    queryFn: () => api.getIndicatorData(indicatorId, days),
    enabled: !!indicatorId,
  });
};

export const useMarketSummary = (marketId: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: ['market-summary', marketId],
    queryFn: () => api.getMarketSummary(marketId),
    enabled: enabled && !!marketId,
    staleTime: 24 * 60 * 60 * 1000, // 24 hours
    gcTime: 24 * 60 * 60 * 1000,    // 24 hours cache
  });
};

export const useSignals = (marketId?: string, severity?: string) => {
  return useQuery({
    queryKey: ['signals', marketId, severity],
    queryFn: () => api.getSignals(marketId, severity),
    refetchInterval: 30000,
  });
};

export const useAskQuestion = () => {
  return useMutation({
    mutationFn: ({ question, contextMarket }: { question: string; contextMarket?: string }) =>
      api.askQuestion(question, contextMarket),
  });
};

export const useDataSources = () => {
  return useQuery({
    queryKey: ['data-sources'],
    queryFn: api.getDataSources,
  });
};
