import { GlassCard } from '@/components/ui/GlassCard'
import SentimentGauge from '@/components/charts/SentimentGauge'
import type { MarketOverview } from '@/types/api'

export function SentimentPanel({ overview }: { overview: MarketOverview }) {
  const total = overview.advancers + overview.decliners + overview.unchanged
  const advPct = total ? (overview.advancers / total) * 100 : 0
  const decPct = total ? (overview.decliners / total) * 100 : 0
  const label = overview.sentiment_label

  return (
    <GlassCard
      title="Market Sentiment"
      subtitle={`Breadth ${overview.advancers}↑ / ${overview.decliners}↓`}
      className="sentiment-card"
    >
      <div className="sentiment-card__body">
        <div className="sentiment-card__gauge">
          <SentimentGauge score={overview.sentiment_score} />
          <span className={`sentiment-card__label sentiment-card__label--${label.toLowerCase()}`}>{label}</span>
        </div>
        <div className="sentiment-card__bars">
          <div className="breadth">
            <div className="breadth__track">
              <div className="breadth__adv" style={{ width: `${advPct}%` }} />
              <div className="breadth__dec" style={{ width: `${decPct}%` }} />
            </div>
            <div className="breadth__legend">
              <span><i className="dot dot--up" /> Advancers {overview.advancers}</span>
              <span><i className="dot dot--down" /> Decliners {overview.decliners}</span>
              <span><i className="dot dot--flat" /> Unchanged {overview.unchanged}</span>
            </div>
          </div>
        </div>
      </div>
    </GlassCard>
  )
}
