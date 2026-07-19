import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { qk } from '@/lib/queryClient'
import type {
  ForecastResponse,
  HealthResponse,
  HistoryResponse,
  IndicatorSnapshot,
  InsightsResponse,
  MarketOverview,
  ModelRow,
  MoversResponse,
  PredictionHistoryRow,
  SearchHistoryRow,
  SearchResult,
  StockDetail,
  StockSummary,
  TimeRange,
  TrainResponse,
  WatchlistResponse,
} from '@/types/api'

export function useHealth() {
  return useQuery({ queryKey: qk.health, queryFn: () => api.get<HealthResponse>('health'), staleTime: 60_000 })
}

export function useMarketOverview() {
  return useQuery({
    queryKey: qk.overview,
    queryFn: () => api.get<MarketOverview>('market/overview'),
    staleTime: 30_000,
  })
}

export function useMovers(kind: 'gainers' | 'losers' | 'active', limit = 8) {
  return useQuery({
    queryKey: qk.movers(kind, limit),
    queryFn: () => api.get<MoversResponse>('market/movers', { kind, limit }),
    staleTime: 30_000,
    placeholderData: (prev) => prev,
  })
}

export function useSearch(q: string, limit = 10) {
  const trimmed = q.trim()
  return useQuery({
    queryKey: qk.search(trimmed, limit),
    queryFn: () => api.get<{ items: SearchResult[]; count: number }>('stocks/search', { q: trimmed, limit }),
    enabled: trimmed.length > 0,
    staleTime: 5 * 60_000,
  })
}

export function useStocksList(sector: string | null, limit = 100, offset = 0) {
  return useQuery({
    queryKey: qk.stocksList(sector, limit, offset),
    queryFn: () => api.get<{ items: StockSummary[]; count: number }>('stocks', { sector, limit, offset }),
    staleTime: 5 * 60_000,
  })
}

export function useStockDetail(symbol: string | undefined) {
  return useQuery({
    queryKey: qk.detail(symbol ?? ''),
    queryFn: () => api.get<StockDetail>(`stocks/${symbol}`),
    enabled: !!symbol,
    staleTime: 20_000,
  })
}

export function useStockHistory(symbol: string | undefined, range: TimeRange) {
  return useQuery({
    queryKey: qk.history(symbol ?? '', range),
    queryFn: () => api.get<HistoryResponse>(`stocks/${symbol}/history`, { range }),
    enabled: !!symbol,
    staleTime: 5 * 60_000,
  })
}

export function useIndicators(symbol: string | undefined, range: TimeRange) {
  return useQuery({
    queryKey: qk.indicators(symbol ?? '', range),
    queryFn: () => api.get<IndicatorSnapshot>(`indicators/${symbol}`, { range }),
    enabled: !!symbol,
    staleTime: 5 * 60_000,
  })
}

export function useForecast(symbol: string | undefined, range: TimeRange = '2y', force = false) {
  return useQuery({
    queryKey: [...qk.forecast(symbol ?? ''), range, force],
    queryFn: () => api.get<ForecastResponse>(`predictions/${symbol}`, { range, force_retrain: force ? 'true' : undefined }),
    enabled: !!symbol,
    staleTime: 5 * 60_000,
  })
}

export function useTrainForecast() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (vars: { symbol: string; range: TimeRange }) =>
      api.post<ForecastResponse>(`predictions/${vars.symbol}`, { range: vars.range, force_retrain: true }),
    onSuccess: (data) => {
      qc.setQueryData([...qk.forecast(data.symbol), data.range, true], data)
      qc.setQueryData([...qk.forecast(data.symbol), data.range, false], data)
      qc.invalidateQueries({ queryKey: ['predictions', 'history', data.symbol.toUpperCase()] })
      qc.invalidateQueries({ queryKey: ['predictions', 'models', data.symbol.toUpperCase()] })
    },
  })
}

export function useTrainLeaderboard() {
  return useMutation({
    mutationFn: (vars: { symbol: string; range: TimeRange; models?: string[] }) =>
      api.post<TrainResponse>('predictions/train', { symbol: vars.symbol, range: vars.range, models: vars.models }),
  })
}

export function usePredictionHistory(symbol: string | undefined, limit = 10) {
  return useQuery({
    queryKey: qk.predictionHistory(symbol ?? '', limit),
    queryFn: () =>
      api.get<{ items: PredictionHistoryRow[]; count: number; realized_abs_pct_error_mean: number | null }>(
        `predictions/${symbol}/history`,
        { limit },
      ),
    enabled: !!symbol,
    staleTime: 60_000,
  })
}

export function useModelVersions(symbol: string | undefined) {
  return useQuery({
    queryKey: qk.models(symbol ?? ''),
    queryFn: () => api.get<{ items: ModelRow[]; count: number }>(`predictions/models/${symbol}`),
    enabled: !!symbol,
    staleTime: 60_000,
  })
}

export function useInsights(symbol: string | undefined) {
  return useQuery({
    queryKey: qk.insights(symbol ?? ''),
    queryFn: () => api.get<InsightsResponse>(`insights/${symbol}`),
    enabled: !!symbol,
    staleTime: 2 * 60_000,
  })
}

export function useWatchlist() {
  return useQuery({
    queryKey: qk.watchlist,
    queryFn: () => api.get<WatchlistResponse>('watchlist'),
    staleTime: 20_000,
  })
}

export function useAddWatchlist() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (symbol: string) => api.post<WatchlistResponse>('watchlist', { symbol }),
    onSuccess: (data) => qc.setQueryData(qk.watchlist, data),
  })
}

export function useRemoveWatchlist() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (symbol: string) => api.del<WatchlistResponse>(`watchlist/${symbol}`),
    onSuccess: (data) => qc.setQueryData(qk.watchlist, data),
  })
}

export function useRecentSearches(limit = 10) {
  return useQuery({
    queryKey: qk.recents(limit),
    queryFn: () => api.get<{ items: SearchHistoryRow[]; count: number }>('users/me/searches', { limit }),
    staleTime: 20_000,
  })
}
