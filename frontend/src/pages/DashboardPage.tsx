import { Link } from 'react-router-dom'
import { Star, TrendingUp } from 'lucide-react'
import { Page } from '@/components/ui/Page'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { SourceBadge } from '@/components/ui/Badge'
import { Spinner, ErrorState, EmptyState } from '@/components/ui/StateViews'
import { SearchBar } from '@/components/ui/SearchBar'
import { MarketIndices } from '@/components/dashboard/MarketIndices'
import { MoversTable } from '@/components/dashboard/MoversTable'
import { SentimentPanel } from '@/components/dashboard/SentimentPanel'
import { useMarketOverview, useWatchlist } from '@/hooks/api'
import { formatNumber, formatPct, changeColor } from '@/lib/format'

export default function DashboardPage() {
  const { data: overview, isLoading, isError, error, refetch } = useMarketOverview()
  const { data: watchlist } = useWatchlist()

  return (
    <Page title="Market Dashboard" actions={<SourceBadge source={overview?.source ?? 'Loading...'} />}>
      <div className="dashboard-hero glass">
        <div>
          <h2>Indian markets, decoded by AI.</h2>
          <p>Search any NSE stock, visualise performance, and forecast the next 7 trading days.</p>
        </div>
        <div className="dashboard-hero__search">
          <SearchBar placeholder="Try “RELIANCE”, “TCS”, “Banks”…" />
        </div>
      </div>

      {isLoading && <Spinner label="Loading market overview…" />}
      {isError && <ErrorState message={(error as Error).message} onRetry={() => refetch()} />}

      {overview && (
        <>
          <MarketIndices indices={overview.indices} />

          <div className="dashboard-grid">
            <GlassCard title="Market Movers" className="dashboard-grid__movers">
              <MoversTable limit={8} />
            </GlassCard>

            <div className="dashboard-grid__side">
              <SentimentPanel overview={overview} />
              <WatchlistPreview items={watchlist?.items ?? []} />
            </div>
          </div>
        </>
      )}
    </Page>
  )
}

function WatchlistPreview({ items }: { items: { symbol: string; company_name: string; price: number | null; change_pct: number | null; latest_forecast_change_pct: number | null }[] }) {
  const top = items.slice(0, 5)
  return (
    <GlassCard
      title="Your Watchlist"
      actions={
        <Link to="/watchlist" className="card-link">
          View all
        </Link>
      }
      className="watchlist-preview"
    >
      {top.length === 0 ? (
        <EmptyState
          title="Nothing watched yet"
          hint="Star a stock to track it here."
          icon={<Star size={24} />}
        />
      ) : (
        <div className="watchlist-preview__list">
          {top.map((w) => (
            <Link key={w.symbol} to={`/stocks/${w.symbol}`} className="watchlist-preview__row">
              <span className="watchlist-preview__sym">
                <TrendingUp size={13} /> {w.symbol}
              </span>
              <span className="watchlist-preview__name">{w.company_name}</span>
              <span className="watchlist-preview__price">
                {w.price != null ? `₹${formatNumber(w.price)}` : '—'}
                {w.change_pct != null && (
                  <small style={{ color: changeColor(w.change_pct) }}>{formatPct(w.change_pct)}</small>
                )}
              </span>
            </Link>
          ))}
        </div>
      )}
      <Link to="/search" className="watchlist-preview__cta">
        <Button variant="outline" size="sm" block>
          Discover stocks
        </Button>
      </Link>
    </GlassCard>
  )
}
