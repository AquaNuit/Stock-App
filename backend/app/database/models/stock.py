"""Stock universe + fundamentals (docs/database_schema.md)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    company_name: Mapped[str] = mapped_column(String(255))
    sector: Mapped[str] = mapped_column(String(120), default="", index=True)
    industry: Mapped[str] = mapped_column(String(120), default="", index=True)
    exchange: Mapped[str] = mapped_column(String(10), default="NSE")
    isin: Mapped[str] = mapped_column(String(20), default="")

    # Fundamentals (best-effort; provider-dependent)
    market_cap: Mapped[float | None] = mapped_column(Float, nullable=True)
    pe_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    eps: Mapped[float | None] = mapped_column(Float, nullable=True)
    dividend_yield: Mapped[float | None] = mapped_column(Float, nullable=True)
    week52_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    week52_low: Mapped[float | None] = mapped_column(Float, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    prices = relationship("HistoricalPrice", back_populates="stock", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="stock", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_stocks_active_lookup", "symbol", "exchange"),)

    @property
    def yf_symbol(self) -> str:
        return f"{self.symbol}.NS" if self.exchange.upper() == "NSE" else self.symbol

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Stock {self.symbol}>"
