import { GlassCard } from '@/components/ui/GlassCard'
import { Badge } from '@/components/ui/Badge'
import TechnicalChart from '@/components/charts/TechnicalChart'
import { formatNumber, formatPct, formatSigned } from '@/lib/format'
import type { IndicatorSnapshot } from '@/types/api'

const RSI_TONE = (state: string) =>
  state === 'overbought' ? 'down' : state === 'oversold' ? 'up' : 'neutral'

export function IndicatorsPanel({ snapshot }: { snapshot: IndicatorSnapshot }) {
  const s = snapshot
  return (
    <GlassCard title="Technical Indicators" subtitle={`Latest close ₹${formatNumber(s.latest_close)}`}>
      <div className="indicator-grid">
        <Indicator label="RSI (14)" value={s.rsi_14 != null ? s.rsi_14.toFixed(1) : '—'} badge={s.rsi_state} tone={RSI_TONE(s.rsi_state)} hint={rsiHint(s.rsi_state)} />
        <Indicator label="MACD" value={fmt(s.macd)} sub={s.macd_hist != null ? `hist ${formatSigned(s.macd_hist)}` : undefined} />
        <Indicator label="MACD Signal" value={fmt(s.macd_signal)} />
        <Indicator label="EMA 12/26 Cross" value={s.ema_cross_12_26 != null ? formatSigned(s.ema_cross_12_26) : '—'} />
        <Indicator label="ATR (14)" value={fmt(s.atr_14)} sub={s.atr_pct != null ? `${formatPct(s.atr_pct, 2)}` : undefined} hint="Volatility" />
        <Indicator label="Bollinger %B" value={s.bb_pct_b != null ? s.bb_pct_b.toFixed(2) : '—'} sub={s.bb_width != null ? `width ${formatNumber(s.bb_width)}` : undefined} />
        <Indicator label="Volatility (21d)" value={s.vol_21 != null ? formatPct(s.vol_21, 2) : '—'} />
        <Indicator label="SMA 20" value={fmt(s.sma?.['20'])} sub={s.sma?.['50'] != null ? `SMA50 ${fmt(s.sma?.['50'])}` : undefined} />
      </div>

      <div className="indicator-chart">
        <TechnicalChart snapshot={s} />
      </div>
    </GlassCard>
  )
}

function Indicator({
  label,
  value,
  sub,
  badge,
  tone,
  hint,
}: {
  label: string
  value: string
  sub?: string
  badge?: string
  tone?: 'up' | 'down' | 'neutral'
  hint?: string
}) {
  return (
    <div className="indicator">
      <div className="indicator__label">
        {label}
        {badge && <Badge tone={tone}>{badge}</Badge>}
      </div>
      <div className="indicator__value">{value}</div>
      {(sub || hint) && <div className="indicator__sub">{sub ?? hint}</div>}
    </div>
  )
}

function fmt(v: number | null | undefined): string {
  return v == null ? '—' : formatNumber(v)
}

function rsiHint(state: string): string {
  if (state === 'overbought') return 'Overbought'
  if (state === 'oversold') return 'Oversold'
  return 'Neutral'
}
