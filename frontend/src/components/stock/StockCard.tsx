import { Link } from 'react-router-dom'
import { Star } from 'lucide-react'
import { useAddWatchlist, useRemoveWatchlist, useWatchlist } from '@/hooks/api'
import type { StockSummary } from '@/types/api'

export function StockCard({ stock }: { stock: StockSummary }) {
  const { data: watchlist } = useWatchlist()
  const add = useAddWatchlist()
  const remove = useRemoveWatchlist()
  const inList = (watchlist?.items ?? []).some((w) => w.symbol.toUpperCase() === stock.symbol.toUpperCase())

  return (
    <Link to={`/stocks/${stock.symbol}`} className="stock-card glass">
      <div className="stock-card__main">
        <span className="stock-card__sym">{stock.symbol}</span>
        <span className="stock-card__name">{stock.company_name}</span>
      </div>
      <div className="stock-card__meta">
        {stock.sector && <span className="stock-card__sector">{stock.sector}</span>}
        {stock.industry && <span className="stock-card__industry">{stock.industry}</span>}
      </div>
      <button
        className="stock-card__star"
        onClick={(e) => {
          e.preventDefault()
          inList ? remove.mutate(stock.symbol) : add.mutate(stock.symbol)
        }}
        aria-label="Toggle watchlist"
      >
        <Star size={15} fill={inList ? 'currentColor' : 'none'} />
      </button>
    </Link>
  )
}
