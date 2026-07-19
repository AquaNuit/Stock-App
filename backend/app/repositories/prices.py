"""OHLCV persistence: bulk upsert + range queries + DataFrame export."""

from __future__ import annotations

from datetime import date

import pandas as pd
from sqlalchemy import delete, func, select

from backend.app.database.models import HistoricalPrice
from backend.app.repositories.base import Repository

COLUMNS = ["date", "open", "high", "low", "close", "adj_close", "volume"]


class PriceRepository(Repository[HistoricalPrice]):
    model = HistoricalPrice

    def latest_date(self, stock_id: int) -> date | None:
        return self.session.scalar(
            select(func.max(HistoricalPrice.date)).where(HistoricalPrice.stock_id == stock_id)
        )

    def count_for(self, stock_id: int) -> int:
        return int(
            self.session.scalar(
                select(func.count()).select_from(HistoricalPrice).where(HistoricalPrice.stock_id == stock_id)
            )
            or 0
        )

    def bulk_upsert(self, stock_id: int, frame: pd.DataFrame, *, source: str) -> int:
        """Insert/replace rows from a cleaned OHLCV DataFrame (indexed or 'date' column)."""
        if frame.empty:
            return 0
        df = frame.copy()
        if "date" not in df.columns:
            df = df.reset_index().rename(columns={df.index.name or "index": "date"})
            if "date" not in df.columns:  # datetime index named otherwise
                df = df.rename(columns={df.columns[0]: "date"})
        df["date"] = pd.to_datetime(df["date"]).dt.date

        incoming = [d for d in df["date"]]
        self.session.execute(
            delete(HistoricalPrice).where(
                HistoricalPrice.stock_id == stock_id, HistoricalPrice.date.in_(incoming)
            )
        )
        rows = [
            HistoricalPrice(
                stock_id=stock_id,
                date=d,
                open=float(r.open),
                high=float(r.high),
                low=float(r.low),
                close=float(r.close),
                adj_close=float(getattr(r, "adj_close", r.close)),
                volume=int(getattr(r, "volume", 0)),
                source=source,
            )
            for d, r in zip(df["date"], df.itertuples(index=False), strict=True)
        ]
        self.session.add_all(rows)
        self.session.flush()
        return len(rows)

    def get_range(self, stock_id: int, start: date | None = None, end: date | None = None) -> list[HistoricalPrice]:
        stmt = (
            select(HistoricalPrice)
            .where(HistoricalPrice.stock_id == stock_id)
            .order_by(HistoricalPrice.date.asc())
        )
        if start:
            stmt = stmt.where(HistoricalPrice.date >= start)
        if end:
            stmt = stmt.where(HistoricalPrice.date <= end)
        return list(self.session.scalars(stmt))

    def to_frame(self, stock_id: int, start: date | None = None, end: date | None = None) -> pd.DataFrame:
        rows = self.get_range(stock_id, start, end)
        if not rows:
            return pd.DataFrame(columns=COLUMNS)
        return pd.DataFrame([{c: getattr(r, c) for c in COLUMNS} for r in rows])
