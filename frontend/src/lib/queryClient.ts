import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      gcTime: 5 * 60_000,
      refetchOnWindowFocus: false,
      retry: (failureCount, error: unknown) => {
        const e = error as { status?: number }
        if (e?.status && (e.status === 404 || e.status === 400 || e.status === 422)) return false
        return failureCount < 1
      },
    },
    mutations: {
      retry: false,
    },
  },
})

// Stable query keys so hooks & invalidation stay consistent across the app.
export const qk = {
  health: ['health'] as const,
  overview: ['market', 'overview'] as const,
  movers: (kind: string, limit: number) => ['market', 'movers', kind, limit] as const,
  search: (q: string, limit: number) => ['stocks', 'search', q, limit] as const,
  stocksList: (sector: string | null, limit: number, offset: number) =>
    ['stocks', 'list', sector, limit, offset] as const,
  detail: (symbol: string) => ['stocks', 'detail', symbol.toUpperCase()] as const,
  history: (symbol: string, range: string) => ['stocks', 'history', symbol.toUpperCase(), range] as const,
  indicators: (symbol: string, range: string) =>
    ['indicators', symbol.toUpperCase(), range] as const,
  forecast: (symbol: string) => ['predictions', 'forecast', symbol.toUpperCase()] as const,
  predictionHistory: (symbol: string, limit: number) =>
    ['predictions', 'history', symbol.toUpperCase(), limit] as const,
  models: (symbol: string) => ['predictions', 'models', symbol.toUpperCase()] as const,
  insights: (symbol: string) => ['insights', symbol.toUpperCase()] as const,
  watchlist: ['watchlist'] as const,
  recents: (limit: number) => ['users', 'me', 'searches', limit] as const,
}
