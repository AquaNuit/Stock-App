import { Link } from 'react-router-dom'
import { History, Star, Trash2 } from 'lucide-react'
import { Page } from '@/components/ui/Page'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { Spinner, EmptyState } from '@/components/ui/StateViews'
import { useRecentSearches, useRemoveWatchlist, useWatchlist } from '@/hooks/api'
import { formatDate, formatNumber, formatPct, changeColor } from '@/lib/format'
import { timeAgo } from '@/lib/format'

export default function WatchlistPage() {
  const { data, isLoading } = useWatchlist()
  const remove = useRemoveWatchlist()
  const recents = useRecentSearches(8)

  return (
    <Page title="Watchlist & Recents">
      {isLoading && <Spinner label="Loading watchlist…" />}
      {!isLoading && data && data.items.length === 0 && (
        <EmptyState
          title="Your watchlist is empty"
          hint="Star a stock from search or its detail page to track it here."
          icon={<Star size={26} />}
        />
      )}

      {data && data.items.length > 0 && (
        <GlassCard title={`Watched (${data.count})`} subtitle={`User: ${data.user}`}>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Company</th>
                  <th className="num">Price</th>
                  <th className="num">Change</th>
                  <th className="num">7d Forecast</th>
                  <th>Added</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((w) => (
                  <tr key={w.symbol}>
                    <td>
                      <Link to={`/stocks/${w.symbol}`} className="row-link">
                        <strong>{w.symbol}</strong>
                      </Link>
                    </td>
                    <td className="muted">{w.company_name}</td>
                    <td className="num">{w.price != null ? `₹${formatNumber(w.price)}` : '—'}</td>
                    <td className="num" style={{ color: changeColor(w.change_pct) }}>
                      {w.change_pct != null ? formatPct(w.change_pct) : '—'}
                    </td>
                    <td className="num" style={{ color: changeColor(w.latest_forecast_change_pct) }}>
                      {w.latest_forecast_change_pct != null ? formatPct(w.latest_forecast_change_pct) : '—'}
                    </td>
                    <td className="muted">{formatDate(w.added_at, 'dd MMM yy')}</td>
                    <td>
                      <button
                        className="icon-btn icon-btn--danger"
                        onClick={() => remove.mutate(w.symbol)}
                        aria-label="Remove"
                      >
                        <Trash2 size={15} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </GlassCard>
      )}

      <GlassCard title="Recent Searches" actions={<History size={15} />}>
        {recents.isLoading && <Spinner />}
        {recents.data && recents.data.items.length === 0 && (
          <EmptyState title="No recent searches" hint="Your search history will appear here." />
        )}
        {recents.data && recents.data.items.length > 0 && (
          <div className="recents">
            {recents.data.items.map((r, i) => (
              <div key={i} className="recents__row">
                <span className="recents__query">{r.query}</span>
                {r.matched_symbol && (
                  <Link to={`/stocks/${r.matched_symbol}`} className="recents__match">
                    {r.matched_symbol}
                  </Link>
                )}
                <span className="recents__time">{timeAgo(r.created_at)}</span>
              </div>
            ))}
          </div>
        )}
      </GlassCard>
    </Page>
  )
}
