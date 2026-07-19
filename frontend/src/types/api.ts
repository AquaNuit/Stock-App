// TypeScript mirrors of the StockSense AI backend Pydantic schemas.
// Keep these in sync with backend/app/schemas/* and docs/api_reference.md.

export type TimeRange = '1m' | '3m' | '6m' | '1y' | '2y' | '5y' | 'max'
export type ConfidenceLabel = 'high' | 'medium' | 'low'
export type DataSource = 'nse' | 'yfinance' | 'seed' | 'cache' | 'db'

export interface SearchResult {
  symbol: string
  company_name: string
  sector: string
  industry: string
  match_field: string
}

export interface StockSummary {
  symbol: string
  company_name: string
  sector: string
  industry: string
}

export interface HistoryBar {
  date: string // ISO date (YYYY-MM-DD)
  open: number
  high: number
  low: number
  close: number
  adj_close: number
  volume: number
}

export interface HistoryResponse {
  symbol: string
  range: TimeRange
  source: DataSource
  count: number
  start: string
  end: string
  bars: HistoryBar[]
  meta: Record<string, unknown>
}

export interface StockDetail {
  symbol: string
  company_name: string
  sector: string
  industry: string
  exchange: string
  price: number
  open: number
  high: number
  low: number
  prev_close: number
  change: number
  change_pct: number
  volume: number
  as_of: string
  source: DataSource
  market_cap: number | null
  pe_ratio: number | null
  eps: number | null
  dividend_yield: number | null
  week52_high: number | null
  week52_low: number | null
}

export interface IndexQuote {
  key: string
  name: string
  value: number
  change: number
  change_pct: number
  spark: number[]
  source: DataSource
}

export interface MarketOverview {
  indices: IndexQuote[]
  advancers: number
  decliners: number
  unchanged: number
  sentiment_score: number // 0..100
  sentiment_label: string
  source: DataSource
}

export interface MoverRow {
  symbol: string
  company_name: string
  price: number
  change: number
  change_pct: number
  volume: number
}

export interface MoversResponse {
  kind: string
  count: number
  source: DataSource
  items: MoverRow[]
}

export interface DayForecastOut {
  date: string
  day: string
  horizon: number
  predicted_price: number
  lower_bound: number
  upper_bound: number
  expected_change: number
  expected_change_pct: number
  confidence: ConfidenceLabel
}

export interface LeaderboardRow {
  rank: number
  model: string
  rmse: number | null
  mae: number | null
  mape: number | null
  r2: number | null
  train_seconds: number
  benchmark: boolean
  error: string | null
}

export interface TrainResponse {
  symbol: string
  range: TimeRange
  training_run_id: number
  best_model: string
  best_rmse: number | null
  leadership_note: string
  leaderboard: LeaderboardRow[]
  duration_s: number
}

export interface ForecastResponse {
  symbol: string
  range: TimeRange
  generated_at: string
  last_close: number
  last_date: string
  model: string
  model_version: string
  model_rmse: number | null
  training_run_id: number
  cached: boolean
  forecasts: DayForecastOut[]
  leaderboard: LeaderboardRow[] | null
}

export interface IndicatorSeries {
  dates: string[]
  sma20: (number | null)[]
  sma50: (number | null)[]
  bb_upper: (number | null)[]
  bb_lower: (number | null)[]
  bb_mid: (number | null)[]
}

export interface IndicatorSnapshot {
  symbol: string
  range: TimeRange
  latest_close: number
  sma: Record<string, number | null>
  ema_cross_12_26: number | null
  rsi_14: number | null
  rsi_state: string // overbought | neutral | oversold
  macd: number | null
  macd_signal: number | null
  macd_hist: number | null
  atr_14: number | null
  atr_pct: number | null
  bb_width: number | null
  bb_pct_b: number | null
  vol_21: number | null
  series: IndicatorSeries
}

export interface SupportResistance {
  support: number
  resistance: number
  method: string
}

export interface InsightsResponse {
  symbol: string
  trend: string
  trend_strength: string
  momentum_summary: string
  volatility_summary: string
  support_resistance: SupportResistance
  outlook_label: string
  outlook_score: number
  risk_level: string
  confidence_explanation: string
  bullets: string[]
}

export interface WatchlistRow {
  symbol: string
  company_name: string
  price: number | null
  change_pct: number | null
  added_at: string
  latest_forecast_change_pct: number | null
}

export interface WatchlistResponse {
  user: string
  count: number
  items: WatchlistRow[]
}

export interface SearchHistoryRow {
  query: string
  matched_symbol: string
  created_at: string
}

export interface PredictionHistoryRow {
  prediction_date: string
  target_date: string
  horizon: number
  predicted_price: number
  lower_bound: number
  upper_bound: number
  model_name: string
  realized_close: number | null
  abs_pct_error: number | null
}

export interface ModelRow {
  id: number
  name: string
  version: string
  status: string
  rmse: number | null
  mae: number | null
  mape: number | null
  r2: number | null
  data_range: TimeRange
  trained_at: string
  train_rows: number
  val_rows: number
}

export interface HealthResponse {
  status: string
  version: string
  time: string
}

export interface ApiErrorShape {
  detail: string
  code: string
}
