import { compareChartOption } from '@/lib/charts'
import EChart from './EChart'
import type { HistoryBar } from '@/types/api'

export interface CompareSeries {
  symbol: string
  bars: HistoryBar[]
}

// Normalised performance comparison (rebased to 100 at the shared start).
export default function CompareChart({ series, height = 360 }: { series: CompareSeries[]; height?: number }) {
  const built = series
    .filter((s) => s.bars.length > 1)
    .map((s) => ({
      symbol: s.symbol,
      dates: s.bars.map((b) => b.date),
      values: s.bars.map((b) => b.close),
    }))
  if (built.length === 0) return null
  const option = compareChartOption(built)
  return <EChart option={option} height={height} notMerge />
}
