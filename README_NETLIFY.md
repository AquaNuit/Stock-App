# Deploy Frontend on Netlify

## Prerequisites

- Netlify account: https://app.netlify.com/
- GitHub access (optional, for Git-based deploys)

## Step 1 — Connect the Repository

Option A — Git-based deploy (recommended):

1. Go to https://app.netlify.com/ → **Add new site** → **Import an existing project**
2. Select your Git provider (GitHub) and choose the `Stock-App` repo
3. Set **Branch to deploy**: `arena/019f8f25-stock-app` (or `main`)
4. Set **Base directory**: `frontend`

Option B — Manual deploy (drag & drop):

```bash
cd Stock-App/frontend
npm ci
npm run build
# Upload the `dist/` folder to Netlify manually
```

## Step 2 — Configure Build Settings

In the Netlify site settings (`Site settings → Build & deploy → Build settings`):

- **Build command**: `npm run build`
- **Publish directory**: `dist`
- **Base directory**: `frontend` (if deploying the whole repo, set this to `frontend`)

These values are already defined in `frontend/netlify.toml`.

## Step 3 — Set Environment Variables

In Netlify (`Site settings → Build & deploy → Environment variables`), add:

| Variable | Value | Notes |
|---|---|---|
| `VITE_API_BASE` | `https://YOUR_USERNAME-YOUR_SPACE.hf.space/api/v1` | Your HF backend URL |
| `NODE_VERSION` | `22` | Already in `netlify.toml` |

**Important**: The variable must start with `VITE_` for Vite to expose it to the browser.

## Step 4 — Configure Proxy (Optional)

If you prefer to avoid CORS entirely, uncomment the proxy block in `frontend/netlify.toml`:

```toml
[[redirects]]
  from = "/api/*"
  to = "https://YOUR_USERNAME-YOUR_SPACE.hf.space/api/:splat"
  status = 200
  force = true
```

Then redeploy. With this proxy, you can leave `VITE_API_BASE` empty (defaults to `/api/v1` in dev, but in production it will hit the proxy).

## Step 5 — SPA Routing

`frontend/netlify.toml` and `frontend/public/_redirects` already contain:

```toml
[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

This ensures React Router works correctly on refresh or direct links (`/watchlist`, `/predict`, etc.).

## Step 6 — Deploy

1. Click **Deploy site** (or push to the branch if using Git integration)
2. Wait for the build to complete (watch the **Deploy log**)
3. Once live, visit your Netlify URL (`https://random-name.netlify.app`)

## Step 7 — Link to HF Backend

After deploying both:

1. Copy your HF Space URL: `https://YOUR_USERNAME-YOUR_SPACE.hf.space`
2. In Netlify, add/update `VITE_API_BASE` to: `https://YOUR_USERNAME-YOUR_SPACE.hf.space/api/v1`
3. In your HF Space settings (`Variables & secrets`), add/update `CORS_ORIGINS` to include your Netlify domain: `https://random-name.netlify.app`
4. Redeploy Netlify (`Deploys → Trigger deploy`) and restart/rebuild your HF Space if needed.

## Step 8 — Verify Connection

In the browser console (Netlify site) or with curl:

```bash
# Check health via Netlify -> HF
curl -H "Origin: https://random-name.netlify.app" \
  https://YOUR_USERNAME-YOUR_SPACE.hf.space/api/v1/health
```

Expected response:
```json
{"status":"ok","version":"0.1.0","time":"2026-07-23T..."}
```

## Step 9 — Custom Domain (Optional)

In Netlify (`Site settings → Domain management`):

1. Click **Add custom domain**
2. Enter your domain (`stocksense.app` or subdomain)
3. Follow the DNS instructions (CNAME to `your-site.netlify.app` or A records)
4. Once propagated, update `CORS_ORIGINS` on HF to include the custom domain

## Build Size Optimization

The Vite config (`frontend/vite.config.ts`) already splits chunks:

- `vendor`: react, react-router-dom
- `query`: tanstack/react-query
- `motion`: framer-motion
- `echarts`: echarts, echarts-for-react

This keeps the initial bundle under ~400 KB gzipped.

## Troubleshooting

| Issue | Fix |
|---|---|
| `VITE_API_BASE` is undefined in production | Ensure the env variable in Netlify starts with `VITE_` and redeploy. |
| CORS error when fetching from HF | Add the exact Netlify domain (with `https://`) to `CORS_ORIGINS` in HF Variables. |
| 404 on page refresh | Ensure `netlify.toml` has the `/*` redirect to `/index.html`. |
| Build fails with TypeScript errors | Run `npm run typecheck` locally in `frontend/` before deploying. |
