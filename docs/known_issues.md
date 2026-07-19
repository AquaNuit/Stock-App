# Known Issues — StockSense AI

> Status: v1.0 · Last updated: 2026-07-19
> Format: `KI-NNN [severity open|closed] — description / workaround / link to roadmap item`.

| ID | Sev | State | Issue |
|---|---|---|---|
| KI-001 | medium | open | Seed-provider OHLCV is synthetic; UI/API label it via `source=seed`, but a **banner in prod** requires `SEED_FALLBACK=false`. |
| KI-002 | low | open | ARIMA order fixed (2,1,2) for latency; seasonal sweep deferred (R2.8). |
| KI-003 | low | open | Conformal intervals are marginal per horizon, not joint across the 7 days. Acceptable for display; document before trading use. |
| KI-004 | medium | open | Auth is header-identity MVP (ADR-0011) — not safe for public exposure until R3.4 JWT ships. |
| KI-005 | low | open | Excel export requires `openpyxl`; endpoint returns 501 if missing (graceful). |
| KI-006 | low | open | Rate limiter is per-process; multiple API replicas need Redis limiter (R3.5). |
