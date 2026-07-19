"""Technical-indicator snapshot + chart overlay payload."""

from __future__ import annotations

import numpy as np
import pandas as pd

from backend.app.core.constants import TimeRange
from backend.app.ml.features.technical_indicators import add_technical_indicators
from backend.app.schemas.insights import IndicatorSnapshot
from backend.app.services.stock_service import StockService

_TAIL = 260  # overlay rows shipped to the chart


class IndicatorService:
    def __init__(self, stock_service: StockService):
        self.stock_service = stock_service

    def snapshot(self, symbol: str, range_value: str = "6m") -> IndicatorSnapshot:
        frame, _source = self.stock_service.get_history_frame(symbol, TimeRange(range_value))
        enriched = add_technical_indicators(frame)
        last = enriched.iloc[-1]
        close = float(last["close"])

        def f(col: str) -> float | None:
            v = last.get(col)
            return round(float(v), 4) if v is not None and pd.notna(v) and np.isfinite(v) else None

        rsi = f("rsi_14")
        rsi_state = (
            "overbought" if (rsi or 50) >= 70 else "oversold" if (rsi or 50) <= 30 else "neutral"
        )

        tail = enriched.tail(_TAIL)
        sma20 = tail["close"].rolling(20).mean()
        sma50 = tail["close"].rolling(50).mean()
        sd20 = tail["close"].rolling(20).std(ddof=0)
        series = {
            "dates": [str(d) for d in tail["date"]],
            "close": [round(float(c), 2) for c in tail["close"]],
            "volume": [int(v) for v in tail["volume"]],
            "sma_20": _round_series(sma20),
            "sma_50": _round_series(sma50),
            "bb_upper": _round_series(sma20 + 2 * sd20),
            "bb_lower": _round_series(sma20 - 2 * sd20),
        }
        return IndicatorSnapshot(
            symbol=symbol.upper(),
            range=range_value,
            latest_close=round(close, 2),
            sma={str(w): f(f"sma_{w}") for w in (5, 10, 20, 50, 100, 200)},
            ema_cross_12_26=f("ema_cross_12_26"),
            rsi_14=rsi,
            rsi_state=rsi_state,
            macd=f("macd"),
            macd_signal=f("macd_signal"),
            macd_hist=f("macd_hist"),
            atr_14=f("atr_14"),
            atr_pct=f("atr_pct"),
            bb_width=f("bb_width"),
            bb_pct_b=f("bb_pct_b"),
            vol_21=f("vol_21"),
            series=series,
        )


def _round_series(s: pd.Series) -> list[float | None]:
    return [round(float(v), 2) if pd.notna(v) and np.isfinite(v) else None for v in s]
