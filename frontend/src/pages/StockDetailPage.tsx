import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Building2, ExternalLink } from 'lucide-react'
import { Page } from '@/components/ui/Page'
import { GlassCard } from '@/components/ui/GlassCard'
import { Badge, SourceBadge } from '@/components/ui/Badge'
import { RangeSelector } from '@/components/ui/RangeSelector'
import { Spinner, ErrorState, EmptyState } from '@/components/ui/StateViews'
import PriceChart from '@/components/charts/PriceChart'
import { KeyStats } from '@/components/stock/KeyStats'
import { IndicatorsPanel } from '@/components/stock/IndicatorsPanel'
import { ForecastPanel } from '@/components/stock/ForecastPanel'
import { InsightsLoader } from '@/components/stock/InsightsPanel'
import { WatchlistButton } from '@/components/stock/WatchlistButton'
import { ExportButtons } from '@/components/stock/ExportButtons'
import { useStockDetail, useStockHistory, useIndicators } from '@/hooks/api'
import { formatINR, formatPct, formatSigned, changeColor } from '@/lib/format'
import type { TimeRange } from '@/types/api'

export default function StockDetailPage() {
  const { symbol = '' } = useParams()
  const sym = symbol.toUpperCase()
  const [range, setRange] = useState<TimeRange>('1y')

  const detail = useStockDetail(sym)
  const { data: hist, isLoading: histLoading } = useStockHistory(sym, range)
  const { data: ind, isLoading: indLoading } = useIndicators(sym, range)

  if (detail.isLoading) return <Page title={sym}><Spinner label="Loading quote…" /></Page>
  if (detail.isError)
    return (
      <Page title={sym}>
        <ErrorState message={(detail.error as Error).message} />
        <Link to="/search" className="card-link">Back to search</Link>
      </Page>
    )
  if (!detail.data)
    return (
      <Page title={sym}>
        <EmptyState title="Stock not found" hint="Try searching for a different ticker." />
      </Page>
    )

  const d = detail.data
  const up = d.change >= 0

  return (
    <Page
      title={
        <span className="detail-title">
          <span className="detail-title__sym">{d.symbol}</span>
          <span className="detail-title__name">{d.company_name}</span>
        </span>
      }
      actions={
        <div className="detail-actions">
          <WatchlistButton symbol={d.symbol} />
          <ExportButtons symbol={d.symbol} range={range} />
        </div>
      }
    >
      <div className="detail-header glass">
        <Link to="/search" className="detail-header__back" aria-label="Back">
          <ArrowLeft size={16} />
        </Link>
        <div className="detail-header__price">
          <span className="detail-header__value">{formatINR(d.price)}</span>
          <span className="detail-header__change" style={{ color: changeColor(d.change) }}>
            {formatSigned(d.change)} ({formatPct(d.change_pct)})
          </span>
        </div>
        <div className="detail-header__meta">
          <SourceBadge source={d.source} />
          <Badge tone="neutral"><Building2 size={12} /> {d.sector || 'N/A'}</Badge>
          <span className="muted">{d.exchange}</span>
        </div>
      </div>

      <GlassCard
        title="Price & Volume"
        subtitle={`${hist?.count ?? 0} sessions · ${hist?.source ?? ''}`}
        actions={<RangeSelector value={range} onChange={setRange} size="sm" />}
        padded={false}
      >
        <div className="chart-card-body">
          {histLoading && <Spinner label="Loading history…" />}
          {hist && <PriceChart bars={hist.bars} height={420} />}
        </div>
      </GlassCard>

      <div className="detail-grid">
        <KeyStats detail={d} />
        {indLoading && <GlassCard title="Technical Indicators"><Spinner label="Computing indicators…" /></GlassCard>}
        {ind && <IndicatorsPanel snapshot={ind} />}
      </div>

      <ForecastPanel symbol={d.symbol} defaultRange="2y" />

      <InsightsLoader symbol={d.symbol} />

      <div className="detail-footer">
        <Link to={`/predict?symbol=${d.symbol}`} className="card-link">
          Open in AI Forecast studio <ExternalLink size={13} />
        </Link>
      </div>
    </Page>
  )
}
