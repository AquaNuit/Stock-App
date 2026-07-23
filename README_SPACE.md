---
title: StockSense AI
emoji: 📊
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
---

# StockSense AI — Backend (FastAPI)

AI-powered NSE stock analysis and 7-day forecasting API. Deployed on Hugging Face Spaces (free tier, 1 GB RAM).

## Endpoints

- `GET /ping` — UptimeRobot keep-alive (prevents HF sleep)
- `GET /api/v1/health` — Health check
- `GET /api/v1/ready` — Readiness probe
- `GET /docs` — Interactive Swagger UI

## UptimeRobot Setup

1. Go to [UptimeRobot](https://uptimerobot.com/)
2. Add new monitor: **Monitor Type** = HTTP(s)
3. **Friendly Name**: `StockSense AI HF`
4. **URL/IP**: `https://your-username-your-space.hf.space/ping`
5. **Monitoring Interval**: Every 5 minutes (free tier minimum is 5 min)
6. Save. The ping endpoint responds instantly (`{"status":"ok"}`) and uses minimal memory.

## Environment Variables (HF Space Settings)

Set these in your Space **Settings → Variables & secrets**:

| Variable | Value |
|---|---|
| `ENV` | `prod` |
| `DATABASE_URL` | `sqlite:///./stocksense.db` |
| `CORS_ORIGINS` | `https://your-netlify-site.netlify.app` |
| `SCHEDULER_ENABLED` | `true` |
| `SEED_FALLBACK` | `true` |
| `MAX_CONCURRENT_TRAINS` | `1` |
| `ML_MAX_TRAINING_ROWS` | `750` |
| `ML_DEFAULT_MODELS` | `linear,random_forest` |

## Memory Optimization (Free Tier)

- Only `scikit-learn` (linear, random_forest) is loaded by default.
- Heavy libraries (`torch`, `prophet`, `xgboost`, `lightgbm`) are excluded from `requirements-hf.txt`.
- SQLite database is used (no external PostgreSQL needed).
- Single uvicorn worker (`--workers 1`).

## Netlify Frontend Link

The frontend (Netlify) connects via `VITE_API_BASE=https://your-username-your-space.hf.space/api/v1`.

## Keep-Alive Note

Free HF Spaces sleep after ~48 hours of inactivity. The `/ping` endpoint + UptimeRobot ping every 5 minutes keeps it awake 24/7.
