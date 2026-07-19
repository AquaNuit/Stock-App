# UI Wireframes — StockSense AI

> Status: v1.0 · Last updated: 2026-07-19
> Design system: dark-first, glassmorphism (`backdrop-filter: blur`, translucent cards, 1px gradient borders),
> accent `#22d3ee` (cyan) + profit/loss `#22c55e`/`#ef4444`, font Inter. Motion: 200–300ms ease transitions, skeleton loaders.
> Implementation: `frontend/src/`. Charts: TradingView *Lightweight Charts* (price, zoom/pan/crosshair) + Apache ECharts (forecast intervals & gauge).

## 1. Global Layout (desktop ≥1024px)
```
┌──────────────────────────────────────────────────────────────────────┐
│ ▦ StockSense AI        🔍 Search ticker / company / sector…    🌙 ☰  │  ← sticky glass topbar (64px)
├──────────┬───────────────────────────────────────────────────────────┤
│ DASHBOARD│                                                           │
│ STOCKS   │               <page content — animated route fade>        │
│ PREDICT  │                                                           │
│ WATCHLIST│                                                           │
│ INSIGHTS │                                                           │
└──────────┴───────────────────────────────────────────────────────────┘
```
Mobile: sidebar collapses to bottom tab bar; cards stack single column.

## 2. Home Dashboard
```
┌─────────────── Market Overview ───────────────────────────────────────┐
│ [NIFTY 50 24,812 ▲0.6%] [SENSEX 81,224 ▲0.5%] [BANKNIFTY ▼0.2%]       │  ← 3 glass index cards + sparkline
│ Sentiment ●●●●○ Bullish-ish   Advance/Decline 84 / 46                 │
├───────────────┬───────────────────────┬───────────────────────────────┤
│ TOP GAINERS   │ TOP LOSERS            │ MOST ACTIVE                   │  ← 3 compact tables
│ TATAMOTORS +4 │ ADANIENT −3.2%        │ RELIANCE 12.4M                │
├───────────────┴───────────────────────┴───────────────────────────────┤
│ LATEST PREDICTIONS (from your watchlist / recents)                    │
│ RELIANCE → ₹2,841 ▸ +1.8% high │ TCS → …                            │
└────────────────────────────────────────────────────────────────────────┘
```

## 3. Stock Detail
```
┌──────────────────────────────────────────────────────────────────────┐
│ RELIANCE · Reliance Industries Ltd            [☆ Watch] [⇩ Export ▾] │
│ ₹2,823.10  ▲ +1.2% today        Energy · Oil & Gas Refining          │
│ [Open][High][Low][PrevClose][Volume][MktCap][P/E][EPS][DivYld][52wkH/L]│ ← stat chips grid
├──────────────────────────────────────────────────────────────────────┤
│ Range: [1M][3M][6M][1Y][2Y][5Y][Max]   Overlays: ☑SMA20 ☑SMA50 ☐BB   │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │   price line/area + MA overlays, crosshair, OHLC tooltip         │ │  ← Lightweight Charts
│ │   ███ volume histogram (color by day direction)                  │ │
│ └──────────────────────────────────────────────────────────────────┘ │
├─────────────────────────┬────────────────────────────────────────────┤
│ TECHNICAL PANEL         │  AI INSIGHTS                               │
│ RSI 62 neutral ▸ gauge  │  Trend: Uptrend (SMA20>SMA50)              │
│ MACD hist +, BB %B 0.7  │  Support ₹2,740 · Resistance ₹2,905        │
│ ATR 41 (1.4%) risk: mod │  Outlook 🟢 Bullish 68/100 — why: …        │
├─────────────────────────┴────────────────────────────────────────────┤
│ ▶ TRAIN & FORECAST  Range [2Y ▾]  Models [auto ▾]   [Train]          │
│ ┌────────────────────────────── forecast chart + band ─────────────┐ │
│ │ history fades → 7 projected steps + P05–P95 gradient band        │ │  ← ECharts
│ └──────────────────────────────────────────────────────────────────┘ │
│  7-DAY FORECAST                              model: rf · RMSE 21.4   │
│ ┌────────┬───────────┬──────────────┬────────┬─────────┬───────────┐│
│ │Date    │Predicted  │Interval      │Change  │%        │Confidence ││
│ │Mon20Jul│₹2,841     │2,798–2,890   │+₹18    │+1.8%    │🟢 High    ││
│ │…×7                                                                 ││
│ └────────┴───────────┴──────────────┴────────┴─────────┴───────────┘│
│ MODEL LEADERBOARD: rf 21.4 RMSE · linear 24.9 · arima 31.2 [bar]     │
└──────────────────────────────────────────────────────────────────────┘
```

## 4. Search Behavior
- Debounced 250ms, `minChars=1`; dropdown shows **symbol chip + name + sector badge**, keyboard ↑↓/Enter nav.
- Grouping: exact ticker > prefix ticker > name substring > sector/industry match.

## 5. States
- **Loading:** shimmer skeletons shaped like final cards/charts.
- **Empty:** "Train a model to see forecasts" CTA.
- **Offline/seed mode:** amber banner "Showing cached/seed data (provider offline)" driven by `source` field.
- **Error:** toast + inline retry; 429 shows cooldown countdown.

## 6. Accessibility
WCAG AA contrast on dark palette; focus-visible rings; chart tooltips mirrored in a screen-reader table; `prefers-reduced-motion` disables transitions/particles.
