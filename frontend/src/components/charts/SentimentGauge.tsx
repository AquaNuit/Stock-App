import { sentimentGaugeOption } from '@/lib/charts'
import EChart from './EChart'

export default function SentimentGauge({ score, height = 180 }: { score: number; height?: number }) {
  return <EChart option={sentimentGaugeOption(score)} height={height} notMerge />
}
