"""UptimeRobot / keep-alive ping endpoint."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

router = APIRouter(tags=["uptime"])


@router.get("/ping")
def ping() -> dict:
    """Lightweight endpoint for UptimeRobot to prevent HF Space sleep."""
    return {"status": "ok", "service": "stocksense-ai", "time": datetime.now(UTC).isoformat()}
