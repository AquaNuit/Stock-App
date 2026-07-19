import { predictionChartOption } from '@/lib/charts'
import EChart from './EChart'
import type { DayForecastOut, HistoryBar } from '@/types/api'

export default function PredictionChart({
  bars,
  forecast,
  height = 320,
}: {
  bars: HistoryBar[]
  forecast: DayForecastOut[] | null
  height?: number
}) {
  const option = predictionChartOption(bars, forecast)
  return <EChart option={option} height={height} notMerge />
}
