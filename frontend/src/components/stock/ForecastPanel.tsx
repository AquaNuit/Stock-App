import { useState } from 'react'
import { BrainCircuit, RefreshCw, Sparkles, Target } from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { Badge, ConfidenceBadge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { RangeSelector } from '@/components/ui/RangeSelector'
import { Spinner, EmptyState } from '@/components/ui/StateViews'
import PredictionChart from '@/components/charts/PredictionChart'
import {
  useModelVersions,
  usePredictionHistory,
  useStockHistory,
  useTrainForecast,
} from '@/hooks/api'
import { useToast } from '@/context/ToastContext'
import { formatDate, formatINR, formatNumber, formatPct, formatSigned } from '@/lib/format'
import { MODEL_LABEL, TRAIN_RANGES } from '@/lib/constants'
import type { ForecastResponse, ModelRow, TimeRange } from '@/types/api'

export function ForecastPanel({ symbol, defaultRange = '2y' }: { symbol: string; defaultRange?: TimeRange }) {
  const [range, setRange] = useState<TimeRange>(defaultRange)
  const toast = useToast()

  const { data: hist } = useStockHistory(symbol, range)
  const train = useTrainForecast()
  const { data: predHist } = usePredictionHistory(symbol, 10)
  const { data: models } = useModelVersions(symbol)

  const forecast: ForecastResponse | undefined = train.data

  async function generate() {
    try {
      await train.mutateAsync({ symbol, range })
      toast.success(`Forecast ready for ${symbol}`)
    } catch (e) {
      toast.error((e as Error).message || 'Forecast failed')
    }
  }

  return (
    <GlassCard
      title={`7-Day AI Forecast · ${symbol}`}
      subtitle="Trained ensemble · next 7 trading days"
      actions={
        <div className="forecast__head-actions">
          <RangeSelector
            value={range}
            onChange={(r) => setRange(r)}
            size="sm"
            options={TRAIN_RANGES}
          />
          <Button
            variant="primary"
            size="sm"
            icon={train.isPending ? undefined : <BrainCircuit size={15} />}
            loading={train.isPending}
            onClick={generate}
          >
            {train.isPending ? 'Training…' : 'Generate Forecast'}
          </Button>
        </div>
      }
    >
      {train.isPending && !forecast && <Spinner label="Training model ensemble…" />}

      {!forecast && !train.isPending && (
        <EmptyState
          title="No forecast generated yet"
          hint="Train the model ensemble on the selected history to predict the next 7 trading days."
          icon={<Sparkles size={28} />}
        />
      )}

      {forecast && (
        <div className="forecast">
          <div className="forecast__summary">
            <Summary label="Best Model" value={MODEL_LABEL[forecast.model] ?? forecast.model} icon={<Target size={14} />} />
            <Summary label="RMSE" value={forecast.model_rmse != null ? formatNumber(forecast.model_rmse) : '—'} />
            <Summary label="Last Close" value={formatINR(forecast.last_close)} />
            <Summary
              label="7-Day Net"
              value={formatSigned(forecast.forecasts.at(-1)?.expected_change ?? 0)}
              tone={
                (forecast.forecasts.at(-1)?.expected_change ?? 0) >= 0 ? 'up' : 'down'
              }
              sub={formatPct(forecast.forecasts.at(-1)?.expected_change_pct ?? 0)}
            />
            {forecast.cached && <Badge tone="info" className="forecast__cached">cached</Badge>}
          </div>

          <div className="forecast__chart">
            {hist && <PredictionChart bars={hist.bars} forecast={forecast.forecasts} />}
          </div>

          <ForecastTable forecast={forecast} />

          {models?.items && models.items.length > 0 && (
            <ModelRegistryTable rows={models.items} bestModel={forecast?.model} />
          )}

          <AccuracyBlock meanError={predHist?.realized_abs_pct_error_mean} count={predHist?.count} />
        </div>
      )}
    </GlassCard>
  )
}

function Summary({
  label,
  value,
  sub,
  icon,
  tone,
}: {
  label: string
  value: string
  sub?: string
  icon?: React.ReactNode
  tone?: 'up' | 'down'
}) {
  return (
    <div className="forecast__summary-item">
      <span className="forecast__summary-label">{label}</span>
      <span className="forecast__summary-value" style={tone === 'up' ? { color: 'var(--up)' } : tone === 'down' ? { color: 'var(--down)' } : undefined}>
        {icon} {value}
      </span>
      {sub && <span className="forecast__summary-sub">{sub}</span>}
    </div>
  )
}

function ForecastTable({ forecast }: { forecast: ForecastResponse }) {
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th>Date</th>
            <th className="num">Predicted</th>
            <th className="num">Confidence Interval</th>
            <th className="num">Change</th>
            <th className="num">%</th>
            <th>Confidence</th>
          </tr>
        </thead>
        <tbody>
          {forecast.forecasts.map((f) => (
            <tr key={f.date}>
              <td>
                <strong>{formatDate(f.date, 'dd MMM')}</strong>
                <small className="muted">{f.day}</small>
              </td>
              <td className="num">₹{formatNumber(f.predicted_price)}</td>
              <td className="num muted">
                ₹{formatNumber(f.lower_bound)} – ₹{formatNumber(f.upper_bound)}
              </td>
              <td className="num" style={{ color: f.expected_change >= 0 ? 'var(--up)' : 'var(--down)' }}>
                {formatSigned(f.expected_change)}
              </td>
              <td className="num" style={{ color: f.expected_change_pct >= 0 ? 'var(--up)' : 'var(--down)' }}>
                {formatPct(f.expected_change_pct)}
              </td>
              <td>
                <ConfidenceBadge confidence={f.confidence} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ModelRegistryTable({ rows, bestModel }: { rows: ModelRow[]; bestModel?: string }) {
  return (
    <div className="leaderboard">
      <h4 className="leaderboard__title">Trained Models · Validation Metrics</h4>
      <div className="table-wrap">
        <table className="data-table data-table--compact">
          <thead>
            <tr>
              <th>Model</th>
              <th>Version</th>
              <th className="num">RMSE</th>
              <th className="num">MAE</th>
              <th className="num">MAPE</th>
              <th className="num">R²</th>
              <th className="num">Rows</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className={r.name === bestModel ? 'is-best' : ''}>
                <td>
                  {MODEL_LABEL[r.name] ?? r.name}
                  {r.name === bestModel && <Badge tone="accent" className="leaderboard__bench">best</Badge>}
                </td>
                <td className="muted">{r.version}</td>
                <td className="num">{r.rmse != null ? formatNumber(r.rmse) : '—'}</td>
                <td className="num">{r.mae != null ? formatNumber(r.mae) : '—'}</td>
                <td className="num">{r.mape != null ? formatNumber(r.mape) : '—'}</td>
                <td className="num">{r.r2 != null ? formatNumber(r.r2) : '—'}</td>
                <td className="num">{formatNumber(r.train_rows)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function AccuracyBlock({ meanError, count }: { meanError: number | null | undefined; count?: number }) {
  if (meanError == null) return null
  return (
    <div className="accuracy glass-sub">
      <RefreshCw size={14} />
      <span>
        Realized accuracy across {count ?? 0} matured prediction{count === 1 ? '' : 's'}: mean absolute error{' '}
        <strong>{formatPct(meanError, 2)}</strong>
      </span>
    </div>
  )
}
