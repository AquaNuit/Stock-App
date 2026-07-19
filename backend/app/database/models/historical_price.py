"""EOD OHLCV bars, upserted from providers (unique per stock+date)."""

from __future__ import annotations

from datetime import date

from sqlalchemy import BigInteger, Date, Float, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base


class HistoricalPrice(Base):
    __tablename__ = "historical_prices"

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), index=True)
    date: Mapped[date] = mapped_column(Date)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    adj_close: Mapped[float] = mapped_column(Float, default=0.0)
    volume: Mapped[int] = mapped_column(BigInteger, default=0)
    source: Mapped[str] = mapped_column(String(16), default="unknown")

    stock = relationship("Stock", back_populates="prices")

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_prices_stock_date"),
        Index("ix_prices_stock_date_desc", "stock_id", "date"),
    )
