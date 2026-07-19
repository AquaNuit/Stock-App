import type { EChartsOption } from 'echarts'
import type { DayForecastOut, HistoryBar } from '@/types/api'

export const PALETTE = {
  up: '#34d399',
  down: '#f87171',
  accent: '#22d3ee',
  accent2: '#a78bfa',
  text: '#e5e7eb',
  dim: '#94a3b8',
  grid: 'rgba(148,163,184,0.10)',
  axis: 'rgba(148,163,184,0.35)',
  band: 'rgba(34,211,238,0.18)',
  bandBorder: 'rgba(34,211,238,0.55)',
  sma20: '#fbbf24',
  sma50: '#60a5fa',
  bb: '#a78bfa',
}

export function sma(values: number[], period: number): (number | null)[] {
  const out: (number | null)[] = []
  let sum = 0
  for (let i = 0; i < values.length; i++) {
    sum += values[i]
    if (i >= period) sum -= values[i - period]
    out.push(i >= period - 1 ? sum / period : null)
  }
  return out
}

export function bollinger(values: number[], period = 20, mult = 2) {
  const mid = sma(values, period)
  const upper: (number | null)[] = []
  const lower: (number | null)[] = []
  for (let i = 0; i < values.length; i++) {
    if (i < period - 1) {
      upper.push(null)
      lower.push(null)
      continue
    }
    let variance = 0
    for (let j = i - period + 1; j <= i; j++) variance += (values[j] - (mid[i] as number)) ** 2
    const sd = Math.sqrt(variance / period)
    upper.push((mid[i] as number) + mult * sd)
    lower.push((mid[i] as number) - mult * sd)
  }
  return { mid, upper, lower }
}

export interface PriceChartOptions {
  showSMA20?: boolean
  showSMA50?: boolean
  showBB?: boolean
  showVolume?: boolean
  showForecast?: boolean
}

type Series = Record<string, unknown>

export function priceChartOption(
  bars: HistoryBar[],
  forecast: DayForecastOut[] | null,
  opts: PriceChartOptions = {},
): EChartsOption {
  const { showSMA20 = true, showSMA50 = true, showBB = false, showVolume = true, showForecast = true } = opts

  const dates = bars.map((b) => b.date)
  const closes = bars.map((b) => b.close)
  const opens = bars.map((b) => b.open)
  const candle = bars.map((b) => [b.open, b.close, b.low, b.high])

  const ma20 = sma(closes, 20)
  const ma50 = sma(closes, 50)
  const bb = bollinger(closes, 20, 2)

  const lastDate = dates[dates.length - 1]
  const lastClose = closes[closes.length - 1] ?? 0
  const fcDates = (forecast ?? []).map((f) => f.date)
  const allDates = [...dates, ...fcDates.filter((d) => d !== lastDate)]
  const fcMap = new Map((forecast ?? []).map((f) => [f.date, f]))

  const predLine: (number | null)[] = allDates.map((d) => {
    if (d === lastDate) return lastClose
    const f = fcMap.get(d)
    return f ? f.predicted_price : null
  })
  const bandLower: number[] = allDates.map((d) => (fcMap.get(d)?.lower_bound ?? 0))
  const bandSpan: number[] = allDates.map((d) => {
    const f = fcMap.get(d)
    return f ? f.upper_bound - f.lower_bound : 0
  })
  const nullTail = <T,>(arr: T[]) =>
    [...arr, ...fcDates.map(() => null as unknown as T)].slice(0, allDates.length)

  const series: Series[] = [
    {
      name: 'Price',
      type: 'candlestick',
      data: nullTail(candle),
      xAxisIndex: 0,
      yAxisIndex: 0,
      itemStyle: {
        color: PALETTE.up,
        color0: PALETTE.down,
        borderColor: PALETTE.up,
        borderColor0: PALETTE.down,
      },
    },
  ]

  if (showSMA20) {
    series.push({ name: 'SMA 20', type: 'line', data: nullTail(ma20), smooth: true, showSymbol: false, lineStyle: { width: 1.4, color: PALETTE.sma20 }, z: 5 })
  }
  if (showSMA50) {
    series.push({ name: 'SMA 50', type: 'line', data: nullTail(ma50), smooth: true, showSymbol: false, lineStyle: { width: 1.4, color: PALETTE.sma50 }, z: 5 })
  }
  if (showBB) {
    series.push(
      { name: 'BB Upper', type: 'line', data: nullTail(bb.upper), showSymbol: false, lineStyle: { width: 1, color: PALETTE.bb, opacity: 0.7 }, z: 4 },
      { name: 'BB Lower', type: 'line', data: nullTail(bb.lower), showSymbol: false, lineStyle: { width: 1, color: PALETTE.bb, opacity: 0.7 }, z: 4 },
    )
  }
  if (showForecast && forecast && forecast.length) {
    series.push(
      { name: 'Confidence', type: 'line', data: bandLower, stack: 'conf', symbol: 'none', lineStyle: { opacity: 0 }, areaStyle: { opacity: 0 }, silent: true, z: 3 },
      { name: 'Confidence Band', type: 'line', data: bandSpan, stack: 'conf', symbol: 'none', lineStyle: { opacity: 0 }, areaStyle: { color: PALETTE.band }, silent: true, z: 3 },
      { name: 'Forecast', type: 'line', data: predLine, smooth: false, showSymbol: true, symbolSize: 6, connectNulls: false, lineStyle: { width: 2, color: PALETTE.accent, type: 'dashed' }, itemStyle: { color: PALETTE.accent }, z: 6 },
    )
  }
  if (showVolume) {
    series.push({
      name: 'Volume',
      type: 'bar',
      xAxisIndex: 1,
      yAxisIndex: 1,
      data: bars.map((b, i) => ({
        value: b.volume,
        itemStyle: { color: closes[i] >= opens[i] ? 'rgba(52,211,153,0.45)' : 'rgba(248,113,113,0.45)' },
      })),
    })
  }

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    animation: true,
    grid: showVolume
      ? [{ left: 56, right: 24, top: 16, height: '62%' }, { left: 56, right: 24, top: '74%', height: '16%' }]
      : [{ left: 56, right: 24, top: 16, bottom: 32 }],
    axisPointer: { link: [{ xAxisIndex: 'all' }], label: { backgroundColor: '#1f2937' } },
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(15,23,42,0.92)', borderColor: 'rgba(148,163,184,0.25)', textStyle: { color: PALETTE.text, fontSize: 12 }, axisPointer: { type: 'cross' } },
    legend: {
      data: [
        'Price',
        ...(showSMA20 ? ['SMA 20'] : []),
        ...(showSMA50 ? ['SMA 50'] : []),
        ...(showBB ? ['BB Upper', 'BB Lower'] : []),
        ...(showForecast && forecast?.length ? ['Forecast'] : []),
      ],
      top: 0,
      textStyle: { color: PALETTE.dim, fontSize: 11 },
      inactiveColor: 'rgba(148,163,184,0.3)',
    },
    xAxis: [
      { type: 'category', data: allDates, boundaryGap: true, axisLine: { lineStyle: { color: PALETTE.axis } }, axisLabel: { color: PALETTE.dim, fontSize: 10 }, splitLine: { show: false }, min: 'dataMin', max: 'dataMax' },
      { type: 'category', gridIndex: 1, data: allDates, boundaryGap: true, axisLine: { lineStyle: { color: PALETTE.axis } }, axisLabel: { show: false }, axisTick: { show: false }, splitLine: { show: false } },
    ],
    yAxis: [
      { scale: true, position: 'left', axisLine: { show: false }, axisLabel: { color: PALETTE.dim, fontSize: 10, formatter: (v: number) => `₹${v >= 1000 ? (v / 1000).toFixed(1) + 'k' : v}` }, splitLine: { lineStyle: { color: PALETTE.grid } } },
      { gridIndex: 1, scale: true, axisLine: { show: false }, axisLabel: { show: false }, splitLine: { show: false } },
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: showVolume ? 55 : 20, end: 100 },
      { type: 'slider', xAxisIndex: [0, 1], bottom: 4, height: 16, start: showVolume ? 55 : 20, end: 100, borderColor: 'transparent', backgroundColor: 'rgba(148,163,184,0.06)', fillerColor: 'rgba(34,211,238,0.12)', handleStyle: { color: PALETTE.accent }, textStyle: { color: PALETTE.dim, fontSize: 9 }, dataBackground: { lineStyle: { color: PALETTE.axis }, areaStyle: { color: 'rgba(34,211,238,0.08)' } } },
    ],
    series: series as EChartsOption['series'],
  }
  return option
}

export function predictionChartOption(bars: HistoryBar[], forecast: DayForecastOut[] | null): EChartsOption {
  const tail = bars.slice(-30)
  const dates = tail.map((b) => b.date)
  const closes = tail.map((b) => b.close)
  const fc = forecast ?? []
  const fcX = [...dates, ...fc.map((f) => f.date)]
  const predLine: (number | null)[] = [...dates.map(() => null), ...fc.map((f) => f.predicted_price)]
  const bandLower: number[] = [...dates.map(() => 0), ...fc.map((f) => f.lower_bound)]
  const bandSpan: number[] = [...dates.map(() => 0), ...fc.map((f) => f.upper_bound - f.lower_bound)]

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    animation: true,
    grid: { left: 56, right: 20, top: 30, bottom: 40 },
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(15,23,42,0.92)', borderColor: 'rgba(148,163,184,0.25)', textStyle: { color: PALETTE.text } },
    legend: { data: ['Close', 'Forecast'], top: 0, textStyle: { color: PALETTE.dim, fontSize: 11 } },
    xAxis: { type: 'category', data: fcX, axisLine: { lineStyle: { color: PALETTE.axis } }, axisLabel: { color: PALETTE.dim, fontSize: 10 }, splitLine: { show: false } },
    yAxis: { scale: true, axisLine: { show: false }, axisLabel: { color: PALETTE.dim, fontSize: 10, formatter: (v: number) => `₹${v >= 1000 ? (v / 1000).toFixed(1) + 'k' : v}` }, splitLine: { lineStyle: { color: PALETTE.grid } } },
    dataZoom: [{ type: 'inside' }, { type: 'slider', bottom: 4, height: 14, borderColor: 'transparent', backgroundColor: 'rgba(148,163,184,0.06)', fillerColor: 'rgba(34,211,238,0.12)', handleStyle: { color: PALETTE.accent }, textStyle: { color: PALETTE.dim, fontSize: 9 } }],
    series: [
      { name: 'Close', type: 'line', data: [...closes, ...fc.map(() => null)], smooth: true, showSymbol: false, lineStyle: { width: 2, color: PALETTE.accent2 }, z: 4 },
      { name: 'Confidence', type: 'line', data: bandLower, stack: 'c', symbol: 'none', lineStyle: { opacity: 0 }, areaStyle: { opacity: 0 }, silent: true, z: 2 },
      { name: 'Confidence Band', type: 'line', data: bandSpan, stack: 'c', symbol: 'none', lineStyle: { opacity: 0 }, areaStyle: { color: PALETTE.band }, silent: true, z: 2 },
      { name: 'Forecast', type: 'line', data: predLine, smooth: false, showSymbol: true, symbolSize: 6, connectNulls: false, lineStyle: { width: 2.4, color: PALETTE.accent, type: 'dashed' }, itemStyle: { color: PALETTE.accent }, z: 5 },
    ] as EChartsOption['series'],
  }
  return option
}

export function technicalChartOption(series: { dates: string[]; sma20: (number | null)[]; sma50: (number | null)[] }): EChartsOption {
  const option: EChartsOption = {
    backgroundColor: 'transparent',
    grid: { left: 56, right: 16, top: 28, bottom: 36 },
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(15,23,42,0.92)', borderColor: 'rgba(148,163,184,0.25)', textStyle: { color: PALETTE.text } },
    legend: { data: ['SMA 20', 'SMA 50'], top: 0, textStyle: { color: PALETTE.dim, fontSize: 11 } },
    xAxis: { type: 'category', data: series.dates, axisLine: { lineStyle: { color: PALETTE.axis } }, axisLabel: { color: PALETTE.dim, fontSize: 10 }, boundaryGap: false },
    yAxis: { scale: true, axisLine: { show: false }, axisLabel: { color: PALETTE.dim, fontSize: 10 }, splitLine: { lineStyle: { color: PALETTE.grid } } },
    dataZoom: [{ type: 'inside' }, { type: 'slider', bottom: 4, height: 14, borderColor: 'transparent', backgroundColor: 'rgba(148,163,184,0.06)', fillerColor: 'rgba(34,211,238,0.12)', handleStyle: { color: PALETTE.accent }, textStyle: { color: PALETTE.dim, fontSize: 9 } }],
    series: [
      { name: 'SMA 20', type: 'line', data: series.sma20, smooth: true, showSymbol: false, lineStyle: { width: 1.5, color: PALETTE.sma20 } },
      { name: 'SMA 50', type: 'line', data: series.sma50, smooth: true, showSymbol: false, lineStyle: { width: 1.5, color: PALETTE.sma50 } },
    ] as EChartsOption['series'],
  }
  return option
}

export function sentimentGaugeOption(score: number): EChartsOption {
  const color = score >= 66 ? PALETTE.up : score >= 40 ? PALETTE.sma20 : PALETTE.down
  const option: EChartsOption = {
    backgroundColor: 'transparent',
    series: [
      {
        type: 'gauge',
        startAngle: 210,
        endAngle: -30,
        min: 0,
        max: 100,
        radius: '92%',
        center: ['50%', '56%'],
        progress: { show: true, width: 12, itemStyle: { color } },
        axisLine: { lineStyle: { width: 12, color: [[1, 'rgba(148,163,184,0.18)']] } },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { color: PALETTE.dim, fontSize: 9, distance: 14 },
        pointer: { show: false },
        anchor: { show: false },
        title: { show: false },
        detail: { valueAnimation: true, fontSize: 26, fontWeight: 700, color: PALETTE.text, offsetCenter: [0, '4%'], formatter: (v: number) => `${Math.round(v)}` },
        data: [{ value: score }],
      },
    ],
  }
  return option
}

export function sparklineOption(values: number[], color = PALETTE.accent): EChartsOption {
  const option: EChartsOption = {
    backgroundColor: 'transparent',
    grid: { left: 1, right: 1, top: 2, bottom: 2 },
    xAxis: { type: 'category', show: false, boundaryGap: false, data: values.map((_, i) => i) },
    yAxis: { type: 'value', show: false, scale: true },
    tooltip: { show: false },
    series: [
      { type: 'line', data: values, smooth: true, showSymbol: false, lineStyle: { width: 1.8, color }, areaStyle: { color: `${color}22` } },
    ],
  }
  return option
}

export function compareChartOption(series: { symbol: string; values: number[]; dates: string[] }[]): EChartsOption {
  const allDates = Array.from(new Set(series.flatMap((s) => s.dates)))
  const legend = series.map((s) => s.symbol)
  const colors = [PALETTE.accent, PALETTE.accent2, PALETTE.sma20]
  const built = series.map((s, idx) => {
    const color = colors[idx % 3]
    const map = new Map(s.dates.map((d, i) => [d, s.values[i]]))
    const base = s.values[0] || 1
    const norm = allDates.map((d) => (map.has(d) ? (map.get(d) as number) / base * 100 : null))
    return {
      name: s.symbol,
      type: 'line',
      data: norm,
      smooth: true,
      showSymbol: false,
      connectNulls: true,
      lineStyle: { width: 2, color },
      itemStyle: { color },
    }
  })
  const option: EChartsOption = {
    backgroundColor: 'transparent',
    grid: { left: 52, right: 18, top: 30, bottom: 36 },
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(15,23,42,0.92)', borderColor: 'rgba(148,163,184,0.25)', textStyle: { color: PALETTE.text }, valueFormatter: (v) => (v == null ? '—' : `${Number(v).toFixed(1)}`) },
    legend: { data: legend, top: 0, textStyle: { color: PALETTE.dim, fontSize: 11 } },
    xAxis: { type: 'category', data: allDates, axisLine: { lineStyle: { color: PALETTE.axis } }, axisLabel: { color: PALETTE.dim, fontSize: 10 } },
    yAxis: { scale: true, axisLine: { show: false }, axisLabel: { color: PALETTE.dim, fontSize: 10 }, splitLine: { lineStyle: { color: PALETTE.grid } } },
    dataZoom: [{ type: 'inside' }, { type: 'slider', bottom: 4, height: 14, borderColor: 'transparent', backgroundColor: 'rgba(148,163,184,0.06)', fillerColor: 'rgba(34,211,238,0.12)', handleStyle: { color: PALETTE.accent }, textStyle: { color: PALETTE.dim, fontSize: 9 } }],
    series: built as EChartsOption['series'],
  }
  return option
}
