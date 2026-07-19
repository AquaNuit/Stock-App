import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { FlaskConical, Layers, Play } from 'lucide-react'
import { Page } from '@/components/ui/Page'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { RangeSelector } from '@/components/ui/RangeSelector'
import { Spinner, EmptyState } from '@/components/ui/StateViews'
import { SymbolInput } from '@/components/stock/SymbolInput'
import { ForecastPanel } from '@/components/stock/ForecastPanel'
import { useTrainLeaderboard } from '@/hooks/api'
import { useToast } from '@/context/ToastContext'
import { MODEL_LABEL, MODEL_OPTIONS, TRAIN_RANGES } from '@/lib/constants'
import type { TimeRange } from '@/types/api'

export default function PredictPage() {
  const [params] = useSearchParams()
  const [symbol, setSymbol] = useState((params.get('symbol') || '').toUpperCase())
  const [range, setRange] = useState<TimeRange>('2y')
  const [selected, setSelected] = useState<string[]>([])
  const toast = useToast()
  const train = useTrainLeaderboard()

  function toggleModel(m: string) {
    setSelected((s) => (s.includes(m) ? s.filter((x) => x !== m) : [...s, m]))
  }

  async function runComparison() {
    if (!symbol.trim()) {
      toast.error('Enter a symbol first')
      return
    }
    try {
      await train.mutateAsync({ symbol: symbol.trim().toUpperCase(), range, models: selected.length ? selected : undefined })
      toast.success('Model comparison complete')
    } catch (e) {
      toast.error((e as Error).message || 'Training failed')
    }
  }

  return (
    <Page title="AI Forecast Studio" actions={<Badge tone="accent"><FlaskConical size={13} /> Model Zoo</Badge>}>
      <GlassCard title="Configure Run" subtitle="Pick a stock, history window and (optionally) a model subset to benchmark.">
        <div className="studio">
          <div className="studio__row">
            <label className="studio__label">Symbol</label>
            <SymbolInput value={symbol} onChange={(s) => setSymbol(s.toUpperCase())} />
          </div>

          <div className="studio__row">
            <label className="studio__label">Training Window</label>
            <RangeSelector value={range} onChange={setRange} size="md" options={TRAIN_RANGES} />
          </div>

          <div className="studio__row studio__row--col">
            <label className="studio__label">
              <Layers size={13} /> Models to compare{' '}
              <span className="muted">({selected.length === 0 ? 'all available' : `${selected.length} selected`})</span>
            </label>
            <div className="model-chips">
              {MODEL_OPTIONS.map((m) => (
                <button
                  key={m.value}
                  className={`model-chip ${selected.includes(m.value) ? 'is-active' : ''}`}
                  onClick={() => toggleModel(m.value)}
                  title={m.description}
                >
                  {MODEL_LABEL[m.value]}
                </button>
              ))}
            </div>
          </div>

          <div className="studio__actions">
            <Button
              variant="outline"
              icon={train.isPending ? undefined : <Play size={15} />}
              loading={train.isPending}
              onClick={runComparison}
            >
              {train.isPending ? 'Benchmarking…' : 'Run Model Comparison'}
            </Button>
            {selected.length > 0 && (
              <Button variant="ghost" size="sm" onClick={() => setSelected([])}>
                Clear selection
              </Button>
            )}
          </div>
        </div>
      </GlassCard>

      {train.data && (
        <GlassCard title="Comparison Result" subtitle={train.data.leadership_note}>
          <div className="compare-result">
            <div className="compare-result__stats">
              <span><strong>{MODEL_LABEL[train.data.best_model] ?? train.data.best_model}</strong> selected</span>
              <span>RMSE <strong>{train.data.best_rmse != null ? train.data.best_rmse.toFixed(2) : '—'}</strong></span>
              <span>Duration <strong>{train.data.duration_s}s</strong></span>
              <span>Run #{train.data.training_run_id}</span>
            </div>
            <div className="table-wrap">
              <table className="data-table data-table--compact">
                <thead>
                  <tr>
                    <th>#</th><th>Model</th><th className="num">RMSE</th><th className="num">MAE</th>
                    <th className="num">MAPE</th><th className="num">R²</th><th className="num">Time (s)</th>
                  </tr>
                </thead>
                <tbody>
                  {train.data.leaderboard.map((r) => (
                    <tr key={r.model} className={r.rank === 1 ? 'is-best' : ''}>
                      <td>{r.rank}</td>
                      <td>
                        {MODEL_LABEL[r.model] ?? r.model}
                        {r.benchmark && <Badge tone="neutral" className="leaderboard__bench">baseline</Badge>}
                        {r.error && <span className="muted"> · {r.error}</span>}
                      </td>
                      <td className="num">{r.rmse != null ? r.rmse.toFixed(2) : '—'}</td>
                      <td className="num">{r.mae != null ? r.mae.toFixed(2) : '—'}</td>
                      <td className="num">{r.mape != null ? r.mape.toFixed(2) : '—'}</td>
                      <td className="num">{r.r2 != null ? r.r2.toFixed(3) : '—'}</td>
                      <td className="num">{r.train_seconds.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </GlassCard>
      )}

      {!symbol && (
        <EmptyState
          title="Select a symbol to begin"
          hint="Use the picker above — try RELIANCE, TCS or HDFCBANK."
          icon={<FlaskConical size={26} />}
        />
      )}

      {symbol && <ForecastPanel symbol={symbol} defaultRange={range} />}
    </Page>
  )
}
