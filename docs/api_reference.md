# API Reference — StockSense AI

> Status: v1.1 · Last updated: 2026-07-19
> Base URL: `/api/v1` · Responses: JSON · Errors: `{"detail": str, "code": str}` with HTTP status.
> Auth: MVP header identity `X-User-Id: <string>` (optional, enables watchlist/recents). JWT in R3.4.
> Rate limit: `RATE_LIMIT_PER_MINUTE` per-IP (default 120). `429` on breach. CORS allowlist via env.
> Interactive docs: `/docs` (Swagger), `/redoc`.

## Conventions

- `symbol` path param: NSE ticker, case-insensitive, validated `^[A-Z0-9&-]{1,20}$` → 422 otherwise.
- `range` query enum: `1m,3m,6m,1y,2y,5y,max` (chart) — history endpoint also accepts it.
- All money INR; dates ISO-8601 UTC; floats rounded to 2 decimals (prices) / 4 (pct).
- Response envelope: resources return objects directly; lists return `{items: [...], count: n}`.
- `source` fields expose provenance: `nse | yfinance | seed | cache`.

## Endpoints

### Health
| Method | Path | Description |
|---|---|---|
| GET | `/health` | liveness: `{status, version, time}` |
| GET | `/ready` | readiness: db + provider chain + cache checks |

### Market
| Method | Path | Query | Description |
|---|---|---|---|
| GET | `/market/overview` | — | index snapshot (NIFTY50/SENSEX/BANKNIFTY), advancers/decliners, sentiment label |
| GET | `/market/movers` | `kind=gainers\|losers\|active` `limit=10` | top movers table (symbol, name, price, change%, volume) |

### Stocks
| Method | Path | Query | Description |
|---|---|---|---|
| GET | `/stocks/search` | `q` `limit=10` | autocomplete over ticker/name/sector/industry (ranked) |
| GET | `/stocks` | `sector?` `limit/offset` | list universe (paginated) |
| GET | `/stocks/{symbol}` | — | quote + fundamentals (price, O/H/L/C, volume, mcap, P/E, EPS, div yield, 52wk, sector, industry) |
| GET | `/stocks/{symbol}/history` | `range=1y` | OHLCV array + range metadata |
| GET | `/stocks/{symbol}/indicators` | `range=1y` | latest indicator snapshot + full series for overlays |

### Indicators (stateless)
| Method | Path | Query | Description |
|---|---|---|---|
| GET | `/indicators/{symbol}` | `range=6m` | computed RSI/MACD/BB/ATR/… latest values + classification (overbought etc.) |

### Predictions
| Method | Path | Body/Query | Description |
|---|---|---|---|
| POST | `/predictions/train` | `{symbol, range="2y", models?=[...]}` | trains candidates, returns leaderboard + best model + run id (429-safe, ~seconds) |
| POST | `/predictions/{symbol}` | `{range="2y"}` | trains-if-needed then returns **7-day forecast** table |
| GET | `/predictions/{symbol}` | `run_id?` | latest stored predictions for a symbol |
| GET | `/predictions/{symbol}/history` | `limit=10` | past prediction batches + realized accuracy where matured |
| GET | `/predictions/models/{symbol}` | — | versioned model registry for symbol with metrics |

**7-day forecast item**
```json
{
  "date": "2026-07-20", "day": "Mon 20 Jul",
  "predicted_price": 2841.35, "lower_bound": 2798.10, "upper_bound": 2890.55,
  "expected_change": 18.25, "expected_change_pct": 1.8,
  "confidence": "high", "horizon": 1, "model": "random_forest", "model_rmse": 21.4
}
```

### Insights
| Method | Path | Description |
|---|---|---|
| GET | `/insights/{symbol}` | AI narrative: trend, support/resistance, momentum, volatility risk, bullish/bearish score 0–100, model-confidence explanation |

### Watchlist & Users
| Method | Path | Body | Description |
|---|---|---|---|
| GET | `/watchlist` | — (`X-User-Id`) | enriched watchlist rows w/ live price |
| POST | `/watchlist` | `{symbol}` | add |
| DELETE | `/watchlist/{symbol}` | — | remove |
| GET | `/users/me/searches` | — | recent searches (`limit=10`) |

### Export
| Method | Path | Query | Description |
|---|---|---|---|
| GET | `/export/history/{symbol}` | `range=1y&format=csv\|xlsx` | OHLCV download |
| GET | `/export/predictions/{symbol}` | `format=csv\|xlsx` | latest 7-day forecast download |

## Error Codes
`VALIDATION_ERROR 422` · `SYMBOL_NOT_FOUND 404` · `PROVIDER_UNAVAILABLE 503` · `RATE_LIMITED 429` · `INSUFFICIENT_HISTORY 409` · `TRAINING_FAILED 500`

## cURL
```bash
curl -s localhost:8000/api/v1/stocks/search?q=reliance
curl -s -X POST localhost:8000/api/v1/predictions/RELIANCE -H 'content-type: application/json' -d '{"range":"2y"}'
```
