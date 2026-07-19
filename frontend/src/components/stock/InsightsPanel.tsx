import { GlassCard } from '@/components/ui/GlassCard'
import { Badge } from '@/components/ui/Badge'
import { useInsights } from '@/hooks/api'
import { Spinner, ErrorState } from '@/components/ui/StateViews'
import { formatINR } from '@/lib/format'
import type { InsightsResponse } from '@/types/api'

const OUTLOOK_TONE = (l: string) => (l === 'bullish' ? 'up' : l === 'bearish' ? 'down' : 'neutral')
const RISK_TONE = (r: string) => (r === 'high' ? 'down' : r === 'moderate' ? 'warn' : 'up')
const TREND_TONE = (t: string) => (t === 'uptrend' ? 'up' : t === 'downtrend' ? 'down' : 'neutral')

export function InsightsPanel({ symbol, insights }: { symbol: string; insights?: InsightsResponse }) {
  if (!insights) return null
  const out = insights
  return (
    <GlassCard title="AI Insights" subtitle={`Generated narrative for ${symbol}`}>
      <div className="insights">
        <div className="insights__top">
          <Metric label="Trend" value={cap(out.trend)} tone={TREND_TONE(out.trend)} />
          <Metric label="Outlook" value={cap(out.outlook_label)} tone={OUTLOOK_TONE(out.outlook_label)} />
          <Metric label="Risk" value={cap(out.risk_level)} tone={RISK_TONE(out.risk_level)} />
          <Metric label="Outlook Score" value={`${out.outlook_score}/100`} />
        </div>

        <div className="insights__sr glass-sub">
          <div>
            <span className="insights__sr-label">Support</span>
            <strong>{formatINR(out.support_resistance.support)}</strong>
          </div>
          <div>
            <span className="insights__sr-label">Resistance</span>
            <strong>{formatINR(out.support_resistance.resistance)}</strong>
          </div>
          <div>
            <span className="insights__sr-label">Method</span>
            <strong>{out.support_resistance.method}</strong>
          </div>
        </div>

        <div className="insights__bullets">
          {out.bullets.map((b, i) => (
            <div key={i} className="insights__bullet glass-sub">
              <span className="insights__bullet-dot" />
              {b}
            </div>
          ))}
        </div>

        <p className="insights__note">
          <strong>Momentum:</strong> {out.momentum_summary} &nbsp;·&nbsp; <strong>Volatility:</strong>{' '}
          {out.volatility_summary}
        </p>
        <div className="insights__confidence glass-sub">
          <span className="insights__sr-label">Model confidence</span>
          <p>{out.confidence_explanation}</p>
        </div>
      </div>
    </GlassCard>
  )
}

function Metric({ label, value, tone }: { label: string; value: string; tone?: 'up' | 'down' | 'neutral' | 'warn' }) {
  return (
    <div className="insights__metric">
      <span className="insights__sr-label">{label}</span>
      {tone ? <Badge tone={tone}>{value}</Badge> : <strong>{value}</strong>}
    </div>
  )
}

function cap(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1)
}

export function InsightsLoader({ symbol }: { symbol: string }) {
  const { data, isLoading, isError, error, refetch } = useInsights(symbol)
  if (isLoading) return <GlassCard title="AI Insights"><Spinner label="Analysing…" /></GlassCard>
  if (isError) return <GlassCard title="AI Insights"><ErrorState message={(error as Error).message} onRetry={() => refetch()} /></GlassCard>
  if (!data) return null
  return <InsightsPanel symbol={symbol} insights={data} />
}
