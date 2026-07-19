import ReactECharts from 'echarts-for-react'
import type { EChartsOption } from 'echarts'
import type { CSSProperties } from 'react'

interface EChartProps {
  option: EChartsOption
  height?: number | string
  style?: CSSProperties
  onEvents?: Record<string, (params: unknown) => void>
  notMerge?: boolean
}

// Thin wrapper around echarts-for-react with sensible defaults for the
// StockSense dark/glass theme. Auto-resizes via the underlying lib.
export default function EChart({ option, height = 320, style, onEvents, notMerge = true }: EChartProps) {
  return (
    <ReactECharts
      option={option}
      notMerge={notMerge}
      lazyUpdate
      style={{ height, width: '100%', ...style }}
      opts={{ renderer: 'canvas' }}
      onEvents={onEvents}
    />
  )
}
