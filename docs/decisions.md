# Architecture Decision Records (ADR Log)

> Each entry: context → decision → consequence. Append new ADRs at the top; never edit history. Status: ✅ accepted.

## ADR-0012 — Synchronous SQLAlchemy over async · 2026-07-19 ✅
ML workloads are CPU-bound and synchronous; repos called from FastAPI threadpool. Async adds complexity without throughput gain at this scale. Revisit when moving to Celery + pg queues.

## ADR-0011 — Header-identity users (MVP), JWT deferred · 2026-07-19 ✅
`X-User-Id` header watches/personalisations without an auth stack. Enables end-to-end user features now; JWT + password hashing scheduled R3.4. Consequence: not multi-tenant-safe for public deployment — must ship R3.4 before any public launch.

## ADR-0010 — Conformal (residual-quantile) intervals · 2026-07-19 ✅
Raw residual quantiles (P05/P95 by default) from validation predictions are added to point forecasts. Model-agnostic, assumptions-light, works for ML *and* ARIMA/Prophet paths (natives CIs used where available, conformal fallback elsewhere). Consequence: intervals are symmetric-ish and can be wide on volatile tickers — acceptable and *honest*.

## ADR-0009 — Direct multi-horizon supervised strategy · 2026-07-19 ✅
One model per forecast day (h=1..7) on engineered features beats recursive loops for tree/linear models (no error compounding, per-horizon calibration). ARIMA-family keeps native recursive forecasting. 7 small models remain fast (<2 s total on 5y daily data for RF/Linear).

## ADR-0008 — Graceful-dependency ML registry · 2026-07-19 ✅
`ModelRegistry` registers each forecaster only if its optional import succeeds (`xgboost`, `lightgbm`, `prophet`, `torch`...). Guarantees `pip install` + full test pass on a bare interpreter, while richer environments unlock more candidates automatically. Model comparison then only ever runs over available models.

## ADR-0007 — Deterministic seed provider as final fallback · 2026-07-19 ✅
A seeded, regime-aware random-walk generator anchored to plausible NSE price levels produces stable OHLCV for the curated universe. It makes CI, demos, and offline development fully deterministic; real providers override whenever reachable. Clearly labeled `source: seed` in API responses.

## ADR-0006 — Provider chain (NSE → yfinance → seed) · 2026-07-19 ✅
NSE-first honours "official data where permitted"; yfinance is the resilient fallback; seed guarantees availability. Chain switches per-call with timeouts and caches aggressively. New providers implement `MarketDataProvider` and are inserted into the ordered list.

## ADR-0005 — Monorepo with `backend/` + `frontend/` · 2026-07-19 ✅
Single PR flow, shared CI, docs co-evolve with code. Deployment stays decoupled: SPA builds to static (Netlify), API containerizes (Railway/Render/Fly).

## ADR-0004 — `pip`-based packaging via root `pyproject.toml` (+ optional extras) · 2026-07-19 ✅
One source of dependency truth; extras: `ml-full` (prophet/torch), `postgres`, `redis`, `dev`. Avoids poetry lock churn for multi-agent sessions.

## ADR-0003 — Mermaid for diagrams · 2026-07-19 ✅
Renders on GitHub; text-diffable; survives refactors better than PNGs.

## ADR-0002 — Docs-as-protocol for multi-agent collaboration · 2026-07-19 ✅
`implementation_status.md`, `changelog.md`, `agent_handoff.md` are updated in the *same* commit as code changes. Handoff doc always lists last-run commands + next task so a cold-start agent can continue safely.

## ADR-0001 — Clean Architecture with DI composition root · 2026-07-19 ✅
Dependency direction API→Services→Repos/Providers/ML. Composition in `api/deps.py`. Consequence: more files, but every layer is independently testable — verified by the test suite layout.
