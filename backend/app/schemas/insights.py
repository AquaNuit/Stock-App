"""Indicator + insights DTOs."""

from __future__ import annotations

from pydantic import BaseModel


class IndicatorSnapshot(BaseModel):
    symbol: str
    range: str
    latest_close: float
    sma: dict[str, float | None]
    ema_cross_12_26: float | None
    rsi_14: float | None
    rsi_state: str  # overbought|neutral|oversold
    macd: float | None
    macd_signal: float | None
    macd_hist: float | None
    atr_14: float | None
    atr_pct: float | None
    bb_width: float | None
    bb_pct_b: float | None
    vol_21: float | None
    series: dict[str, list]  # trimmed overlays for charts (dates + sma20/sma50/bb bands)


class SupportResistance(BaseModel):
    support: float
    resistance: float
    method: str


class InsightsResponse(BaseModel):
    symbol: str
    trend: str  # uptrend|downtrend|sideways
    trend_strength: str
    momentum_summary: str
    volatility_summary: str
    support_resistance: SupportResistance
    outlook_label: str  # bullish|bearish|neutral
    outlook_score: float  # 0–100
    risk_level: str  # low|moderate|high
    confidence_explanation: str
    bullets: list[str]
