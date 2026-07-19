import { useState } from 'react'
import { priceChartOption } from '@/lib/charts'
import EChart from './EChart'
import type { DayForecastOut, HistoryBar } from '@/types/api'

interface PriceChartProps {
  bars: HistoryBar[]
  forecast?: DayForecastOut[] | null
  height?: number
}

export default function PriceChart({ bars, forecast, height = 420 }: PriceChartProps) {
  const [showSMA20, setSMA20] = useState(true)
  const [showSMA50, setSMA50] = useState(true)
  const [showBB, setBB] = useState(false)
  const [showVolume, setVolume] = useState(true)
  const [showForecast, setForecast] = useState(true)

  const option = priceChartOption(bars, forecast ?? null, {
    showSMA20,
    showSMA50,
    showBB,
    showVolume,
    showForecast: showForecast && !!forecast?.length,
  })

  return (
    <div className="chart-wrap">
      <div className="chart-toolbar">
        <Toggle label="SMA 20" active={showSMA20} onClick={() => setSMA20((v) => !v)} color="var(--sma20)" />
        <Toggle label="SMA 50" active={showSMA50} onClick={() => setSMA50((v) => !v)} color="var(--sma50)" />
        <Toggle label="Bollinger" active={showBB} onClick={() => setBB((v) => !v)} color="var(--bb)" />
        <Toggle label="Volume" active={showVolume} onClick={() => setVolume((v) => !v)} color="var(--accent)" />
        <Toggle label="Forecast" active={showForecast} onClick={() => setForecast((v) => !v)} color="var(--accent)" />
      </div>
      <EChart option={option} height={height} notMerge />
    </div>
  )
}

function Toggle({ label, active, onClick, color }: { label: string; active: boolean; onClick: () => void; color: string }) {
  return (
    <button
      className={`chart-toggle ${active ? 'is-active' : ''}`}
      onClick={onClick}
      style={active ? { borderColor: color, color } : undefined}
    >
      <span className="chart-toggle__dot" style={{ background: color }} />
      {label}
    </button>
  )
}
