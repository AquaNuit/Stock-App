import { Link } from 'react-router-dom'
import { ArrowDownRight, ArrowUpRight } from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { Sparkline } from '@/components/ui/Sparkline'
import { Stagger, StaggerItem } from '@/components/ui/Page'
import { formatPct, formatNumber, changeColor } from '@/lib/format'
import type { IndexQuote } from '@/types/api'

export function MarketIndices({ indices }: { indices: IndexQuote[] }) {
  return (
    <Stagger className="index-grid">
      {indices.map((idx) => {
        const up = idx.change >= 0
        return (
          <StaggerItem key={idx.key}>
            <GlassCard className="index-card" hover>
              <div className="index-card__top">
                <span className="index-card__name">{idx.name}</span>
                <span className="index-card__source">{idx.source}</span>
              </div>
              <div className="index-card__value">{formatNumber(idx.value, '0')}</div>
              <div className="index-card__row">
                <span className="index-card__change" style={{ color: changeColor(idx.change) }}>
                  {up ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                  {formatPct(idx.change_pct)}
                </span>
                <div className="index-card__spark">
                  <Sparkline values={idx.spark} height={30} />
                </div>
              </div>
            </GlassCard>
          </StaggerItem>
        )
      })}
    </Stagger>
  )
}

export function IndexLink({ name }: { name: string }) {
  return <Link to="/search">{name}</Link>
}
