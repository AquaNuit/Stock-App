import { technicalChartOption } from '@/lib/charts'
import EChart from './EChart'
import type { IndicatorSnapshot } from '@/types/api'

export default function TechnicalChart({ snapshot, height = 240 }: { snapshot: IndicatorSnapshot; height?: number }) {
  const option = technicalChartOption({
    dates: snapshot.series.dates,
    sma20: snapshot.series.sma20,
    sma50: snapshot.series.sma50,
  })
  return <EChart option={option} height={height} notMerge />
}
