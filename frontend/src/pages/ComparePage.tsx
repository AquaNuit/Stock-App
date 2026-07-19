import { useState } from 'react'
import { Link } from 'react-router-dom'
import { GitCompareArrows, Plus, X } from 'lucide-react'
import { Page } from '@/components/ui/Page'
import { GlassCard } from '@/components/ui/GlassCard'
import { Button } from '@/components/ui/Button'
import { RangeSelector } from '@/components/ui/RangeSelector'
import { Spinner, EmptyState } from '@/components/ui/StateViews'
import { SymbolInput } from '@/components/stock/SymbolInput'
import CompareChart from '@/components/charts/CompareChart'
import { useQueries } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { qk } from '@/lib/queryClient'
import { Badge } from '@/components/ui/Badge'
import { formatINR, formatNumber, formatPct, changeColor } from '@/lib/format'
import type { HistoryResponse, TimeRange } from '@/types/api'

const MAX = 3

export default function ComparePage() {
  const [symbols, setSymbols] = useState<string[]>(['RELIANCE', 'TCS'])
  const [draft, setDraft] = useState('')
  const [range, setRange] = useState<TimeRange>('1y')

  const results = useQueries({
    queries: symbols.map((s) => ({
      queryKey: qk.history(s, range),
      queryFn: () => api.get<HistoryResponse>(`stocks/${s}/history`, { range }),
      staleTime: 5 * 60_000,
    })),
  })

  const loading = results.some((r) => r.isLoading)
  const series = results
    .map((r, i) => ({ symbol: symbols[i], bars: r.data?.bars ?? [] }))
    .filter((s) => s.bars.length > 0)

  function add(sym: string) {
    const s = sym.trim().toUpperCase()
    if (!s) return
    if (symbols.includes(s)) {
      setDraft('')
      return
    }
    if (symbols.length >= MAX) return
    setSymbols((prev) => [...prev, s])
    setDraft('')
  }

  function remove(sym: string) {
    setSymbols((prev) => prev.filter((x) => x !== sym))
  }

  return (
    <Page title="Compare Stocks" actions={<Badge tone="accent"><GitCompareArrows size={14} /> Normalised</Badge>}>
      {symbols.length >= MAX && (
        <p className="muted compare-note">Maximum {MAX} symbols reached — remove one to add another.</p>
      )}
      <GlassCard title="Selection" subtitle={`Compare up to ${MAX} symbols (rebased to 100 at range start).`}>
        <div className="compare-bar">
          <SymbolInput value={draft} onChange={setDraft} placeholder="Add a symbol to compare…" />
          <Button
            variant="primary"
            size="sm"
            icon={<Plus size={15} />}
            disabled={symbols.length >= MAX}
            onClick={() => add(draft)}
          >
            Add
          </Button>
          <RangeSelector value={range} onChange={setRange} size="sm" />
        </div>
        <div className="compare-chips">
          {symbols.map((s) => (
            <span key={s} className="compare-chip">
              <Link to={`/stocks/${s}`}>{s}</Link>
              <button onClick={() => remove(s)} aria-label={`Remove ${s}`}>
                <X size={12} />
              </button>
            </span>
          ))}
          {symbols.length === 0 && <span className="muted">Add at least one symbol.</span>}
        </div>
      </GlassCard>

      {loading && <Spinner label="Loading histories…" />}

      {!loading && series.length === 0 && (
        <EmptyState title="Nothing to compare yet" hint="Add symbols above to plot their relative performance." />
      )}

      {!loading && series.length > 0 && (
        <>
          <GlassCard title="Relative Performance" subtitle="Indexed to 100 at the start of the selected window" padded={false}>
            <div className="chart-card-body">
              <CompareChart series={series} height={380} />
            </div>
          </GlassCard>

          <GlassCard title="Snapshot">
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th className="num">Latest</th>
                    <th className="num">Window Change</th>
                    <th className="num">High</th>
                    <th className="num">Low</th>
                    <th className="num">Avg Volume</th>
                  </tr>
                </thead>
                <tbody>
                  {series.map((s) => {
                    const bars = s.bars
                    const first = bars[0].close
                    const last = bars[bars.length - 1].close
                    const chg = ((last - first) / first) * 100
                    const high = Math.max(...bars.map((b) => b.high))
                    const low = Math.min(...bars.map((b) => b.low))
                    const avgVol = bars.reduce((a, b) => a + b.volume, 0) / bars.length
                    return (
                      <tr key={s.symbol}>
                        <td>
                          <Link to={`/stocks/${s.symbol}`} className="row-link">
                            <strong>{s.symbol}</strong>
                          </Link>
                        </td>
                        <td className="num">{formatINR(last)}</td>
                        <td className="num" style={{ color: changeColor(chg) }}>{formatPct(chg)}</td>
                        <td className="num">{formatINR(high)}</td>
                        <td className="num">{formatINR(low)}</td>
                        <td className="num">{formatNumber(Math.round(avgVol))}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </GlassCard>
        </>
      )}
    </Page>
  )
}
