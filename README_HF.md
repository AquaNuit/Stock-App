# Deploy Backend on Hugging Face Spaces (Free Tier)

## Prerequisites

- Hugging Face account: https://huggingface.co
- UptimeRobot account (optional, for 24/7 keep-alive): https://uptimerobot.com/

## Step 1 — Create the Space

1. Go to https://huggingface.co/spaces → **New Space**
2. **Space name**: `stocksense-ai` (or your choice)
3. **License**: MIT (optional)
4. **SDK**: Select `Docker`
5. **Space Hardware**: Leave on `CPU basic` (free, 2 vCPU, 16 GB RAM, 50 GB disk) — the app runs fine within the 1 GB practical limit due to the slim Dockerfile.
6. Click **Create Space**

## Step 2 — Push Code to the Space

The Space creates a git repo. From your local machine:

```bash
# Clone the space repo (replace YOUR_USERNAME and YOUR_SPACE)
git clone https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE

# Copy optimized files from this repo
cp Stock-App/Dockerfile YOUR_SPACE/
cp Stock-App/requirements-hf.txt YOUR_SPACE/
cp Stock-App/backend YOUR_SPACE/backend -r
cp Stock-App/README_SPACE.md YOUR_SPACE/README.md
cp Stock-App/.env.huggingface YOUR_SPACE/.env

# Also copy the root .env.huggingface as .env
cp Stock-App/.env.huggingface YOUR_SPACE/.env

# Push
cd YOUR_SPACE
git add .
git commit -m "Deploy StockSense AI backend"
git push
```

Or, if you want to deploy directly from the `Stock-App` repo root (recommended):

```bash
# Inside Stock-App directory
cp Dockerfile .env.huggingface .
git add Dockerfile requirements-hf.txt README_SPACE.md .env.huggingface
# Note: README.md is replaced by README_SPACE.md for HF, but you can also rename it
```

## Step 3 — Configure Space Settings

In your Space dashboard (`https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE`):

- **Settings → Variables & secrets** → Add:
  - `ENV` = `prod`
  - `CORS_ORIGINS` = `https://YOUR-NETLIFY-SITE.netlify.app` (your actual Netlify URL)
  - `DATABASE_URL` = `sqlite:///./stocksense.db`
  - `SCHEDULER_ENABLED` = `true`
  - `SEED_FALLBACK` = `true`
  - `MAX_CONCURRENT_TRAINS` = `1`
  - `ML_MAX_TRAINING_ROWS` = `750`
  - `ML_DEFAULT_MODELS` = `linear,random_forest`

- **Settings → Hardware** → Keep on `CPU basic` (free). Do not upgrade unless needed.

- The Docker build will start automatically when files are pushed.

## Step 4 — Verify Deployment

Once the container builds (watch the **Logs** tab), the app should be available at:

```
https://YOUR_USERNAME-YOUR_SPACE.hf.space/ping
```

Test with curl:

```bash
curl https://YOUR_USERNAME-YOUR_SPACE.hf.space/ping
# Expected: {"status":"ok","service":"stocksense-ai","time":"..."}
```

Also verify docs:
```
https://YOUR_USERNAME-YOUR_SPACE.hf.space/docs
```

## Step 5 — UptimeRobot Setup (Keep 24/7 Awake)

Free HF Spaces sleep after ~48 hours of inactivity. UptimeRobot pings every 5 minutes prevent this.

1. Sign up at https://uptimerobot.com/
2. Click **Add New Monitor**
3. **Monitor Type**: `HTTP(s)`
4. **Friendly Name**: `StockSense AI HF`
5. **URL/IP**: `https://YOUR_USERNAME-YOUR_SPACE.hf.space/ping`
6. **Monitoring Interval**: `Every 5 minutes`
7. Click **Create Monitor**

The `/ping` endpoint is designed to respond in < 10 ms with almost zero CPU/memory usage.

## Step 6 — Link Netlify Frontend

In your Netlify site settings (`Site settings → Build & deploy → Environment variables`):

- `VITE_API_BASE` = `https://YOUR_USERNAME-YOUR_SPACE.hf.space/api/v1`

Also update your backend `.env` (or Space Variables) so `CORS_ORIGINS` includes your Netlify domain:

```
CORS_ORIGINS=https://stocksense-app.netlify.app
```

Then redeploy Netlify (`Deploys → Trigger deploy → Deploy site`).

## Troubleshooting

| Issue | Fix |
|---|---|
| Container crashes with OOM | Ensure `MAX_CONCURRENT_TRAINS=1` and `ML_MAX_TRAINING_ROWS=750`. Avoid selecting `prophet`, `lstm`, `xgboost`, or `lightgbm` in Forecast Studio. |
| `/ping` returns 404 | Make sure `README_SPACE.md` is copied as `README.md` in the Space repo and `Dockerfile` exposes `7860`. |
| CORS errors on Netlify | Add the exact Netlify domain (including `https://`) to `CORS_ORIGINS`. |
| SQLite DB resets on restart | Free HF Spaces have ephemeral storage except `/data` (requires paid upgrade). For persistence, consider uploading the DB to HF Hub or switching to a persistent volume. |

## Memory Footprint (Free Tier)

- Base image (`python:3.11-slim`): ~50 MB
- Installed slim packages (`scikit-learn`, `pandas`, etc.): ~250 MB
- SQLite DB (after seed): ~5 MB
- Running memory (single uvicorn + 1 train): ~300-500 MB
- This leaves comfortable headroom within the 1 GB practical limit.
