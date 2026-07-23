#!/usr/bin/env python3
"""
Standalone lightweight uptime server for UptimeRobot.
Runs a minimal FastAPI app on a dedicated port (default 8000 or 7860)
so that UptimeRobot can ping it independently of the main backend.

Usage (optional — the main backend already exposes /ping):
    python uptime_server.py

Then configure UptimeRobot to ping:
    http://localhost:8000/ping   (local test)
    https://your-space.hf.space/ping  (production)
"""

import uvicorn
from fastapi import FastAPI
from datetime import UTC, datetime

app = FastAPI(title="StockSense AI Uptime Server", version="1.0.0")

@app.get("/ping")
async def ping() -> dict:
    """Instant response for UptimeRobot. Keeps HF Space awake."""
    return {
        "status": "ok",
        "service": "stocksense-ai-uptime",
        "time": datetime.now(UTC).isoformat(),
    }

@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "stocksense-ai-uptime"}

if __name__ == "__main__":
    port = 8000
    uvicorn.run(app, host="0.0.0.0", port=port, access_log=False)
    print(f"Uptime server running on http://0.0.0.0:{port}/ping")
