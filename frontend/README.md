# StockSense AI — Frontend

A production-grade **React + TypeScript + Vite** SPA for **StockSense AI**, the AI-powered
NSE (Indian equities) analysis & 7-day forecasting platform. It talks to the FastAPI backend
in `../backend` (see `docs/api_reference.md`).

## Features

- **Dashboard** — live market overview, indices with sparklines, sentiment gauge, breadth,
  top gainers / losers / most-active, watchlist preview.
- **Search & Discover** — autocomplete over ticker / company / sector / industry + universe browse by sector.
- **Stock Detail** — quote + fundamentals, interactive candlestick + volume chart with
  SMA / Bollinger overlays and a 7-day forecast overlay, technical indicators, AI insights.
- **AI Forecast Studio** — pick a symbol + training window + optional model subset, run a
  model-comparison leaderboard (RMSE / MAE / MAPE / R²), and generate a 7-day forecast with
  confidence intervals.
- **Watchlist & Recents** — starred stocks (header identity `X-User-Id`), recent searches.
- **Compare** — overlay normalised performance of up to 3 symbols.
- **Export** — history & forecasts to CSV / XLSX via backend export routes.
- **Design** — dark-first glassmorphism, light theme toggle, animated page transitions,
  fully responsive (off-canvas sidebar on mobile).

## Stack

React 18 · TypeScript · Vite 5 · React Router 6 · TanStack Query 5 · ECharts 5 ·
Framer Motion · Zustand · lucide-react.

## Quick start (local)

```bash
# 1) Start the backend (separate terminal) — works fully offline via the seed provider.
cd ../backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn backend.app.main:app --reload --port 8000

# 2) Start the frontend
cd frontend
npm install
npm run dev          # http://localhost:5173  (proxies /api -> :8000)
```

`VITE_API_BASE` is intentionally unset in dev: the Vite dev server proxies `/api/*`
to `http://localhost:8000` (see `vite.config.ts`), so there are no CORS issues locally.

## Scripts

| Command | Description |
|---|---|
| `npm run dev` | Vite dev server with API proxy |
| `npm run build` | Type-check (`tsc --noEmit`) + production build to `dist/` |
| `npm run preview` | Preview the production build locally |
| `npm run typecheck` | Type-check only |

## Project structure

```
frontend/
├── index.html
├── vite.config.ts
├── tsconfig.json
├── netlify.toml
├── public/            # favicon, _redirects (SPA fallback)
└── src/
    ├── main.tsx       # entry — QueryClient + Toast providers
    ├── App.tsx        # router + AppShell
    ├── config/env.ts  # API base, user-id/theme persistence
    ├── types/api.ts   # TS mirrors of backend Pydantic schemas
    ├── lib/           # api client, queryClient, formatters, ECharts builders
    ├── hooks/         # useDebounce + React Query data hooks
    ├── store/         # zustand (theme)
    ├── context/       # Toast provider
    ├── components/
    │   ├── layout/    # AppShell, Sidebar, Topbar
    │   ├── ui/        # GlassCard, Button, Badge, SearchBar, RangeSelector, …
    │   ├── charts/    # EChart wrapper + Price/Prediction/Technical/Gauge/Compare
    │   └── stock|dashboard/  # ForecastPanel, Indicators, Insights, Movers, …
    ├── pages/         # Dashboard, Search, StockDetail, Predict, Watchlist, Compare, 404
    └── styles/        # tokens, base, components, layout, pages
```

## Deployment (Netlify)

1. Build command: `npm run build` · Publish directory: `dist` (already in `netlify.toml`).
2. Set the build environment variable **`VITE_API_BASE`** to your deployed API, e.g.
   `https://api.stocksense.app/api/v1`. Ensure the backend’s `CORS_ORIGINS` includes your
   Netlify domain.
3. SPA routing is handled by `public/_redirects` (and the `[[redirects]]` in `netlify.toml`).

Alternatively, proxy `/api/*` to your backend at Netlify’s edge (uncomment the block in
`netlify.toml`) to avoid CORS entirely.

> Demo data is synthetic and labelled **“Demo”** in the UI — not investment advice.
