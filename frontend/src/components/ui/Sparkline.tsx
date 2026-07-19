import { PALETTE, sparklineOption } from '@/lib/charts'
import EChart from '@/components/charts/EChart'

export function Sparkline({ values, height = 36 }: { values: number[]; height?: number }) {
  if (!values || values.length < 2) return <div style={{ height }} />
  const color = values[values.length - 1] >= values[0] ? PALETTE.up : PALETTE.down
  return <EChart option={sparklineOption(values, color)} height={height} notMerge />
}
