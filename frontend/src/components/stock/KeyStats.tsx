import { GlassCard } from '@/components/ui/GlassCard'
import { StatTile } from '@/components/ui/StatTile'
import {
  formatINR,
  formatInt,
  formatNumber,
  formatPct,
  formatSigned,
  marketCapLabel,
  changeColor,
} from '@/lib/format'
import type { StockDetail } from '@/types/api'

export function KeyStats({ detail }: { detail: StockDetail }) {
  const up = detail.change >= 0
  return (
    <GlassCard title="Key Statistics" subtitle={detail.exchange}>
      <div className="stat-grid">
        <StatTile label="Open" value={formatINR(detail.open)} />
        <StatTile label="High" value={formatINR(detail.high)} />
        <StatTile label="Low" value={formatINR(detail.low)} />
        <StatTile label="Prev Close" value={formatINR(detail.prev_close)} />
        <StatTile label="Volume" value={formatInt(detail.volume)} />
        <StatTile
          label="Change"
          value={<span style={{ color: changeColor(detail.change) }}>{formatINR(detail.change)}</span>}
          sub={<span style={{ color: changeColor(detail.change) }}>{formatPct(detail.change_pct)}</span>}
        />
        <StatTile label="Market Cap" value={marketCapLabel(detail.market_cap)} />
        <StatTile label="P/E Ratio" value={detail.pe_ratio != null ? formatNumber(detail.pe_ratio) : '—'} />
        <StatTile label="EPS" value={detail.eps != null ? formatINR(detail.eps) : '—'} />
        <StatTile
          label="Dividend Yield"
          value={detail.dividend_yield != null ? formatPct(detail.dividend_yield, 2) : '—'}
        />
        <StatTile label="52W High" value={formatINR(detail.week52_high)} />
        <StatTile label="52W Low" value={formatINR(detail.week52_low)} />
        <StatTile label="Sector" value={detail.sector || '—'} />
        <StatTile label="Industry" value={detail.industry || '—'} />
      </div>
      <p className="keystats__foot">
        {up ? '▲' : '▼'} As of {new Date(detail.as_of).toLocaleString('en-IN')}
      </p>
    </GlassCard>
  )
}
