# StockSense AI — Development Roadmap

> Status: v1.0 · Last updated: 2026-07-19
> Legend: ✅ done · 🚧 in progress · ⬜ planned — progress truth lives in [implementation_status.md](implementation_status.md).

## Milestone R0 — Foundations & Documentation ✅
- ✅ R0.1 Repository scaffold, tooling, `pyproject.toml`, CI
- ✅ R0.2 Full documentation set (this folder) with multi-agent handoff protocol

## Milestone R1 — Backend Core ✅
- ✅ R1.1 Core: settings, logging, constants
- ✅ R1.2 Database: 8 ORM models + session factories (SQLite/Postgres)
- ✅ R1.3 Repositories (stocks, prices, predictions, models, watchlist, searches, training runs, users)
- ✅ R1.4 Cache layer (TTL memory + optional Redis)
- ✅ R1.5 Provider chain: NSE → yfinance → deterministic seed fallback; NSE universe search
- ✅ R1.6 Seed script (`python -m backend.scripts.seed_db`)

## Milestone R2 — ML Engine ✅
- ✅ R2.1 Data preprocessing (cleaning, alignment, business-day reindex)
- ✅ R2.2 Technical indicators (SMA, EMA, RSI, MACD, ATR, BB, VWAP, OBV, ROC, momentum, volatility)
- ✅ R2.3 Feature engineering (lags, rolling, calendar)
- ✅ R2.4 Model zoo: Linear, RandomForest, ARIMA + guarded XGBoost/LightGBM/Prophet/LSTM
- ✅ R2.5 Training pipeline: time-split validation, metrics (RMSE/MAE/MAPE/R²), auto model selection, versioning
- ✅ R2.6 7-day forecaster with conformal intervals + confidence labels
- ⬜ R2.7 Celery worker queue for async training (APScheduler in-process shipped instead)
- ⬜ R2.8 Optuna hyper-parameter search
- ⬜ R2.9 Walk-forward revalidation & drift monitoring

## Milestone R3 — API ✅
- ✅ R3.1 FastAPI app factory, middleware (request-id, timing, rate limit, CORS)
- ✅ R3.2 Routers: health, market, stocks, indicators, predictions, insights, watchlist, export
- ✅ R3.3 CSV/Excel export
- ⬜ R3.4 JWT auth + per-user watchlists (header-identity MVP shipped)
- ⬜ R3.5 Redis-backed distributed rate limiter

## Milestone R4 — Frontend ✅
- ✅ R4.1 Vite + React + TS scaffold, dark mode, glass design system
- ✅ R4.2 Dashboard (overview, gainers/losers/active, breadth, sentiment)
- ✅ R4.3 Search with autocomplete (ticker/name/sector/industry)
- ✅ R4.4 Stock detail: stats, fundamentals, interactive chart (ranges 1M–Max, MA overlays, volume)
- ✅ R4.5 Training + 7-day prediction panel + history + comparison table
- ⬜ R4.6 PDF export from UI
- ⬜ R4.7 Comparison mode (multi-symbol overlay)

## Milestone R5 — Productionization 🚧
- ✅ R5.1 Dockerfiles + docker-compose (api + worker + postgres + redis + frontend)
- ✅ R5.2 CI: lint+typecheck+tests, frontend build
- ⬜ R5.3 Deploy: Railway/Render (API), Netlify (SPA), Upstash (Redis), R2 (artifacts) — guide in [deployment.md](deployment.md)
- ⬜ R5.4 Observability: Prometheus metrics, Sentry
- ⬜ R5.5 Alembic migrations (currently `create_all` for dev)

## Suggested Next-Increment Order
1. R5.5 Alembic → 2. R3.4 JWT auth → 3. R2.8 Optuna → 4. R4.7 comparison mode → 5. R2.7 Celery
