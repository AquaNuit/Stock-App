"""Forecast persistence: batch save + latest/history queries."""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import func, select

from backend.app.database.models import Prediction
from backend.app.repositories.base import Repository


class PredictionRepository(Repository[Prediction]):
    model = Prediction

    def save_batch(self, rows: Iterable[Prediction]) -> list[Prediction]:
        rows = list(rows)
        self.session.add_all(rows)
        self.session.flush()
        return rows

    def latest_batch(self, stock_id: int) -> list[Prediction]:
        """Most recent 7-day batch (all horizons sharing latest prediction_date + run)."""
        latest = self.session.scalar(
            select(func.max(Prediction.prediction_date)).where(Prediction.stock_id == stock_id)
        )
        if latest is None:
            return []
        stmt = (
            select(Prediction)
            .where(Prediction.stock_id == stock_id, Prediction.prediction_date == latest)
            .order_by(Prediction.horizon.asc())
        )
        return list(self.session.scalars(stmt))

    def history(self, stock_id: int, *, limit: int = 10) -> list[Prediction]:
        stmt = (
            select(Prediction)
            .where(Prediction.stock_id == stock_id)
            .order_by(Prediction.prediction_date.desc(), Prediction.horizon.asc())
            .limit(limit * 7)
        )
        return list(self.session.scalars(stmt))
