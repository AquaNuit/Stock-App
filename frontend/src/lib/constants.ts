import type { TimeRange } from '@/types/api'

// Historical range selectors exposed in the UI (must match backend TimeRange enum).
export const HISTORY_RANGES: { value: TimeRange; label: string }[] = [
  { value: '1m', label: '1M' },
  { value: '3m', label: '3M' },
  { value: '6m', label: '6M' },
  { value: '1y', label: '1Y' },
  { value: '2y', label: '2Y' },
  { value: '5y', label: '5Y' },
  { value: 'max', label: 'MAX' },
]

// Ranges accepted by the prediction/training endpoints.
export const TRAIN_RANGES: { value: TimeRange; label: string }[] = [
  { value: '1y', label: '1 Year' },
  { value: '2y', label: '2 Years' },
  { value: '5y', label: '5 Years' },
  { value: 'max', label: 'Max' },
]

// Human-friendly labels for chart legends etc.
export const RANGE_LABELS: Record<TimeRange, string> = {
  '1m': '1 Month',
  '3m': '3 Months',
  '6m': '6 Months',
  '1y': '1 Year',
  '2y': '2 Years',
  '5y': '5 Years',
  max: 'Maximum',
}

// Forecasting models offered by the registry (subset selectable in the UI).
export const MODEL_OPTIONS: { value: string; label: string; description: string }[] = [
  { value: 'linear', label: 'Linear Regression', description: 'Baseline (persistence/stats)' },
  { value: 'random_forest', label: 'Random Forest', description: 'Tree ensemble' },
  { value: 'xgboost', label: 'XGBoost', description: 'Gradient-boosted trees' },
  { value: 'lightgbm', label: 'LightGBM', description: 'Gradient-boosted trees' },
  { value: 'arima', label: 'ARIMA', description: 'Classical time series' },
  { value: 'prophet', label: 'Prophet', description: 'Additive seasonality' },
  { value: 'lstm', label: 'LSTM', description: 'Deep recurrent net' },
]

export const MODEL_LABEL: Record<string, string> = Object.fromEntries(
  MODEL_OPTIONS.map((m) => [m.value, m.label]),
)

export const CONFIDENCE_META: Record<string, { label: string; color: string }> = {
  high: { label: 'High', color: '#34d399' },
  medium: { label: 'Medium', color: '#fbbf24' },
  low: { label: 'Low', color: '#f87171' },
}

// Curated "featured" symbols used for dashboard previews / quick actions.
export const FEATURED_SYMBOLS = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'SBIN']
