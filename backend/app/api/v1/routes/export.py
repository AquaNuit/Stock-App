"""CSV / XLSX exports."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query
from fastapi.responses import Response

from backend.app.api.deps import PredictionServiceDep, StockServiceDep
from backend.app.core.constants import TimeRange
from backend.app.services.export_service import export_frame, predictions_frame

router = APIRouter(prefix="/export", tags=["export"])


def _respond(payload: bytes, media: str, filename: str) -> Response:
    return Response(
        content=payload,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/history/{symbol}")
def export_history(
    symbol: str,
    svc: StockServiceDep,
    range: str = Query(default="1y", pattern="^(1m|3m|6m|1y|2y|5y|max)$"),
    format: str = Query(default="csv", pattern="^(csv|xlsx)$"),
) -> Response:
    frame, _ = svc.get_history_frame(symbol, TimeRange(range))
    payload, media, ext = export_frame(frame, format, sheet=f"{symbol} {range}")
    return _respond(payload, media, f"stocksense_{symbol.upper()}_{range}_{date.today()}.{ext}")


@router.get("/predictions/{symbol}")
def export_predictions(
    symbol: str,
    svc: PredictionServiceDep,
    format: str = Query(default="csv", pattern="^(csv|xlsx)$"),
) -> Response:
    fc = svc.forecast7(symbol, force_retrain=False)
    rows = [d.model_dump() for d in fc.forecasts]
    frame = predictions_frame(rows)
    payload, media, ext = export_frame(frame, format, sheet=f"{symbol} forecast")
    return _respond(payload, media, f"stocksense_forecast_{symbol.upper()}_{date.today()}.{ext}")
