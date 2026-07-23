# Deploy Backend on Render (Free Tier)

Render is a great free alternative to Hugging Face Spaces for deploying your Python FastAPI backend. The free tier provides 512 MB of RAM, which is enough to run this app if we restrict the ML models.

## Step 1 — Push Code to GitHub
Ensure your repository (including the new `render.yaml` file) is pushed to your GitHub account.

## Step 2 — Deploy to Render
We have included a `render.yaml` file (Infrastructure as Code) that automatically configures your app for Render's free tier.

1. Go to [Render](https://render.com/) and create a free account.
2. Click **New +** and select **Blueprint**.
3. Connect your GitHub account and select your `Stock-App` repository.
4. Render will automatically detect the `render.yaml` file.
5. Click **Apply**. 

Render will now build your environment using the lightweight `requirements-hf.txt` (to stay within the 512 MB memory limit) and deploy your app.

## Step 3 — Configure CORS (Netlify Link)
By default, the `render.yaml` file sets a placeholder for `CORS_ORIGINS`. Once your frontend is deployed to Netlify:

1. Go to your Render Dashboard → **stocksense-ai** service.
2. Click on **Environment** in the left sidebar.
3. Edit the `CORS_ORIGINS` variable to match your Netlify URL (e.g., `https://my-app.netlify.app`).
4. **Save Changes** (Render will automatically redeploy).

## Step 4 — Update Netlify Frontend
In your Netlify Dashboard for the frontend:
1. Go to **Site settings → Build & deploy → Environment variables**.
2. Add or update `VITE_API_BASE` to your new Render URL: `https://stocksense-ai-xxxx.onrender.com/api/v1`.
3. Redeploy your Netlify site.

## Step 5 — Keep Awake 24/7 (UptimeRobot)
Render's free tier spins down your server after 15 minutes of inactivity, causing a ~30-second delay on the next request.

1. Go to [UptimeRobot](https://uptimerobot.com/).
2. Create a new **HTTP(s)** monitor.
3. Set the URL to your Render ping endpoint: `https://stocksense-ai-xxxx.onrender.com/ping`.
4. Set the interval to **every 10 minutes**.
5. Save the monitor. This will keep your Render service awake 24/7.
