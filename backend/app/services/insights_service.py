"""AI insights: deterministic, explainable narrative from indicators + forecasts.

Not an LLM — a rule-based analyst (docs/architecture.md §AI INSIGHTS). Every
statement carries its evidence so the UI can render "why".
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from backend.app.core.constants import TimeRange
from backend.app.ml.features.technical_indicators import add_technical_indicators
from backend.app.ml.prediction.forecaster import DayForecast
from backend.app.repositories import PredictionRepository, StockRepository
from backend.app.schemas.insights import InsightsResponse, SupportResistance
from backend.app.services.stock_service import StockService


class InsightsService:
    def __init__(self, stock_service: StockService):
        self.stock_service = stock_service
        self.session = stock_service.session
        self.predictions = PredictionRepository(self.session)
        self.stocks = StockRepository(self.session)

    def generate(self, symbol: str) -> InsightsResponse:
        frame, _ = self.stock_service.get_history_frame(symbol, TimeRange.ONE_YEAR)
        e = add_technical_indicators(frame)
        close = e["close"].astype(float)
        last_close = float(close.iloc[-1])

        trend, strength = self._trend(e, close)
        momentum = self._momentum(e)
        vol_summary, risk = self._volatility(e)
        sr = self._support_resistance(close, last_close)
        outlook_label, outlook_score, fc_bullets = self._outlook(symbol, e, last_close)

        bullets = [
            f"Close ₹{last_close:,.2f}; 20d mean ₹{close.tail(20).mean():,.2f}, "
            f"50d mean ₹{close.tail(50).mean():,.2f}.",
            momentum,
            vol_summary,
            f"Support ≈ ₹{sr.support:,.0f} (recent swing low) · Resistance ≈ ₹{sr.resistance:,.0f} (recent swing high).",
            *fc_bullets,
        ]
        explanation = (
            "Outlook blends trend structure (40%), momentum (25%), forecast drift (20%) and "
            "volatility regime (15%). Model confidence labels derive from conformal interval "
            "widths (docs/ml_pipeline.md §6): narrow bands → high confidence."
        )
        return InsightsResponse(
            symbol=symbol.upper(), trend=trend, trend_strength=strength,
            momentum_summary=momentum, volatility_summary=vol_summary,
            support_resistance=sr, outlook_label=outlook_label, outlook_score=outlook_score,
            risk_level=risk, confidence_explanation=explanation, bullets=bullets,
        )

    # ---------------------------------------------------------------- internals
    def _trend(self, e: pd.DataFrame, close: pd.Series) -> tuple[str, str]:
        sma20, sma50 = close.tail(20).mean(), close.tail(50).mean()
        sma200 = close.tail(200).mean() if len(close) >= 200 else close.mean()
        above20, above50, above200 = close.iloc[-1] > sma20, close.iloc[-1] > sma50, close.iloc[-1] > sma200
        score = int(above20) + int(above50) + int(above200)
        slope = (sma20 - close.tail(40).head(20).mean()) / max(close.iloc[-1], 1e-9)
        if score >= 2 and slope > 0.01:
            label, strength = "uptrend", "strong" if score == 3 and slope > 0.05 else "moderate"
        elif score <= 1 and slope < -0.01:
            label, strength = "downtrend", "strong" if score == 0 and slope < -0.05 else "moderate"
        else:
            label, strength = "sideways", "weak"
        return label, strength

    def _momentum(self, e: pd.DataFrame) -> str:
        rsi = float(e["rsi_14"].iloc[-1])
        macd_hist = float(e["macd_hist"].iloc[-1]) if pd.notna(e["macd_hist"].iloc[-1]) else 0.0
        roc10 = float(e["roc_10"].iloc[-1]) if pd.notna(e["roc_10"].iloc[-1]) else 0.0
        state = "overbought" if rsi >= 70 else "oversold" if rsi <= 30 else "neutral"
        macd_state = "positive" if macd_hist > 0 else "negative"
        return (
            f"RSI(14) {rsi:.0f} ({state}); MACD histogram {macd_state}; "
            f"10-session ROC {roc10 * 100:+.1f}%."
        )

    def _volatility(self, e: pd.DataFrame) -> tuple[str, str]:
        atr_pct = float(e["atr_pct"].iloc[-1]) if pd.notna(e["atr_pct"].iloc[-1]) else 0.0
        vol21 = float(e["vol_21"].iloc[-1]) if pd.notna(e["vol_21"].iloc[-1]) else 0.0
        if vol21 < 0.2:
            risk = "low"
        elif vol21 < 0.35:
            risk = "moderate"
        else:
            risk = "high"
        return (
            f"21d annualized volatility {vol21 * 100:.0f}% (ATR {atr_pct * 100:.1f}% of price); "
            f"risk regime: {risk}."
        ), risk

    def _support_resistance(self, close: pd.Series, last_close: float) -> SupportResistance:
        window = close.tail(60)
        # Rolling extrema confluence: nearest swing levels around current price.
        low_q, high_q = float(window.quantile(0.10)), float(window.quantile(0.90))
        support = min(float(window.min()), low_q)
        resistance = max(float(window.max()), high_q)
        support = min(support, last_close * 0.985)
        resistance = max(resistance, last_close * 1.015)
        return SupportResistance(
            support=round(support, 2), resistance=round(resistance, 2),
            method="60-session quantile confluence (Q10/Q90)",
        )

    def _outlook(self, symbol: str, e: pd.DataFrame, last_close: float) -> tuple[str, float, list[str]]:
        close = e["close"].astype(float)
        trend_pts = 0.0
        trend_pts += 20 if close.iloc[-1] > close.tail(20).mean() else -10
        trend_pts += 20 if close.iloc[-1] > close.tail(50).mean() else -10

        rsi = float(e["rsi_14"].iloc[-1])
        momentum_pts = 25 - abs(rsi - 55) * 0.9  # healthy mid-high RSI scores best
        macd_hist = float(e["macd_hist"].iloc[-1]) if pd.notna(e["macd_hist"].iloc[-1]) else 0.0
        momentum_pts += 10 if macd_hist > 0 else -5

        forecast_pts = 0.0
        bullets: list[str] = []
        stock = self.stocks.by_symbol(symbol.upper())
        if stock is not None:
            batch = self.predictions.latest_batch(stock.id)
            if batch:
                avg_change = sum(p.expected_change_pct for p in batch) / len(batch)
                forecast_pts = float(np.clip(avg_change * 4, -20, 20))
                confs = [p.confidence for p in batch]
                hi = confs.count("high")
                bullets.append(
                    f"Latest 7-day model forecast: mean {avg_change:+.1f}% "
                    f"({hi}/7 days at high confidence)."
                )

        vol21 = float(e["vol_21"].iloc[-1]) if pd.notna(e["vol_21"].iloc[-1]) else 0.25
        vol_pts = 15 - max(0.0, (vol21 - 0.2)) * 100  # penalize elevated vol

        raw = 50 + trend_pts + momentum_pts - 15 + forecast_pts + vol_pts - 15
        score = float(np.clip(raw, 0, 100))
        label = "bullish" if score >= 60 else "bearish" if score <= 40 else "neutral"
        bullets.append(
            f"Composite outlook score {score:.0f}/100 → {label} "
            f"(trend {trend_pts:+.0f}, momentum {momentum_pts - 25:+.0f}, "
            f"forecast {forecast_pts:+.0f}, vol {vol_pts - 15:+.0f})."
        )
        return label, round(score, 1), bullets


def summarize_forecasts(days: list[DayForecast]) -> str:
    up = sum(1 for d in days if d.expected_change_pct > 0.3)
    down = sum(1 for d in days if d.expected_change_pct < -0.3)
    return f"{up} of 7 projected days up, {down} down, rest flat (±0.3%)."
