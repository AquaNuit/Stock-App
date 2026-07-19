import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowDown, ArrowUp, Star } from 'lucide-react'
import clsx from 'clsx'
import { useMovers } from '@/hooks/api'
import { useAddWatchlist, useRemoveWatchlist, useWatchlist } from '@/hooks/api'
import { RangeSelector } from '@/components/ui/RangeSelector'
import { Spinner, EmptyState } from '@/components/ui/StateViews'
import { formatInt, formatNumber, formatPct, changeColor } from '@/lib/format'

type Kind = 'gainers' | 'losers' | 'active'

export function MoversTable({ limit = 8 }: { limit?: number }) {
  const [kind, setKind] = useState<Kind>('gainers')
  const { data, isLoading } = useMovers(kind, limit)

  const TABS: { value: Kind; label: string }[] = [
    { value: 'gainers', label: 'Top Gainers' },
    { value: 'losers', label: 'Top Losers' },
    { value: 'active', label: 'Most Active' },
  ]

  return (
    <div className="movers">
      <div className="movers__tabs">
        {TABS.map((t) => (
          <button
            key={t.value}
            className={clsx('movers__tab', kind === t.value && 'is-active')}
            onClick={() => setKind(t.value)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {isLoading && <Spinner label="Loading movers…" />}
      {!isLoading && data && data.items.length === 0 && (
        <EmptyState title="No movers available" hint="Try again shortly." />
      )}

      {!isLoading && data && data.items.length > 0 && (
        <div className="movers__list">
          {data.items.map((row) => (
            <MoverRow key={row.symbol} row={row} />
          ))}
        </div>
      )}
    </div>
  )
}

function MoverRow({ row }: { row: { symbol: string; company_name: string; price: number; change: number; change_pct: number; volume: number } }) {
  const { data: watchlist } = useWatchlist()
  const add = useAddWatchlist()
  const remove = useRemoveWatchlist()
  const inList = (watchlist?.items ?? []).some((w) => w.symbol.toUpperCase() === row.symbol.toUpperCase())
  const up = row.change >= 0

  return (
    <Link to={`/stocks/${row.symbol}`} className="mover-row">
      <span className="mover-row__sym">
        {up ? <ArrowUp size={13} className="mover-row__arrow mover-row__arrow--up" /> : <ArrowDown size={13} className="mover-row__arrow mover-row__arrow--down" />}
        {row.symbol}
      </span>
      <span className="mover-row__name">{row.company_name}</span>
      <span className="mover-row__price">₹{formatNumber(row.price)}</span>
      <span className="mover-row__chg" style={{ color: changeColor(row.change) }}>
        {formatPct(row.change_pct)}
      </span>
      <span className="mover-row__vol">{formatInt(row.volume)}</span>
      <button
        className="mover-row__star"
        onClick={(e) => {
          e.preventDefault()
          inList ? remove.mutate(row.symbol) : add.mutate(row.symbol)
        }}
        aria-label="Toggle watchlist"
      >
        <Star size={14} fill={inList ? 'currentColor' : 'none'} />
      </button>
    </Link>
  )
}
