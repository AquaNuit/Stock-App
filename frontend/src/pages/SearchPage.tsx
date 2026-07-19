import { useMemo, useState } from 'react'
import { SearchX } from 'lucide-react'
import { Page, Stagger, StaggerItem } from '@/components/ui/Page'
import { SearchBar } from '@/components/ui/SearchBar'
import { GlassCard } from '@/components/ui/GlassCard'
import { Spinner, EmptyState, ErrorState } from '@/components/ui/StateViews'
import { StockCard } from '@/components/stock/StockCard'
import { useDebounce } from '@/hooks/useDebounce'
import { useSearch, useStocksList } from '@/hooks/api'
import type { StockSummary } from '@/types/api'

const SECTORS = [
  'Financial Services',
  'Banking',
  'Information Technology',
  'Oil & Gas',
  'Consumer Goods',
  'Automobile',
  'Pharmaceuticals',
  'Energy',
  'Metals',
]

export default function SearchPage() {
  const [q, setQ] = useState('')
  const [sector, setSector] = useState<string | null>(null)
  const debounced = useDebounce(q, 250)
  const { data: search, isFetching: searching } = useSearch(debounced, 24)
  const { data: list, isLoading: listing, isError, error, refetch } = useStocksList(sector, 120, 0)

  const results: StockSummary[] = debounced.trim() ? (search?.items ?? []) : (list?.items ?? [])

  const cards = useMemo(
    () => results.map((r, i) => <StaggerItem key={r.symbol}><StockCard stock={r} /></StaggerItem>),
    [results],
  )

  return (
    <Page title="Search & Discover">
      <div className="search-page__bar glass">
        <SearchBar
          placeholder="Search by ticker, company, sector or industry…"
          onNavigate={() => {}}
        />
      </div>

      {!debounced.trim() && (
        <div className="search-page__sectors">
          <button className={`chip ${!sector ? 'is-active' : ''}`} onClick={() => setSector(null)}>
            All
          </button>
          {SECTORS.map((s) => (
            <button key={s} className={`chip ${sector === s ? 'is-active' : ''}`} onClick={() => setSector(s)}>
              {s}
            </button>
          ))}
        </div>
      )}

      {debounced.trim() && searching && !search && <Spinner label="Searching…" />}
      {isError && <ErrorState message={(error as Error).message} onRetry={() => refetch()} />}
      {!isError && results.length === 0 && !searching && (
        <EmptyState title="No stocks found" hint="Try a different ticker or company name." icon={<SearchX size={26} />} />
      )}

      {results.length > 0 && (
        <GlassCard title={debounced.trim() ? `Results (${results.length})` : `Universe${sector ? ` · ${sector}` : ''}`} padded={false}>
          <Stagger className="stock-grid">{cards}</Stagger>
        </GlassCard>
      )}
    </Page>
  )
}
