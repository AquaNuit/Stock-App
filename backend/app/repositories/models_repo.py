"""Model versioning + training-run persistence."""

from __future__ import annotations

from sqlalchemy import select

from backend.app.database.models import Model, TrainingRun
from backend.app.repositories.base import Repository


class ModelRepository(Repository[Model]):
    model = Model

    def by_version(self, version: str) -> Model | None:
        return self.session.scalar(select(Model).where(Model.version == version))

    def for_symbol(self, stock_id: int, *, limit: int = 25) -> list[Model]:
        stmt = (
            select(Model)
            .where(Model.stock_id == stock_id)
            .order_by(Model.trained_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(stmt))

    def latest_selected(self, stock_id: int) -> Model | None:
        stmt = (
            select(Model)
            .where(Model.stock_id == stock_id, Model.status == "selected")
            .order_by(Model.trained_at.desc())
            .limit(1)
        )
        return self.session.scalar(stmt)


class TrainingRunRepository(Repository[TrainingRun]):
    model = TrainingRun

    def create_run(self, *, stock_id: int, trigger_type: str, data_range: str) -> TrainingRun:
        return self.add(
            TrainingRun(stock_id=stock_id, trigger_type=trigger_type, data_range=data_range, status="running")
        )

    def recent_runs(self, stock_id: int | None = None, *, limit: int = 10) -> list[TrainingRun]:
        stmt = select(TrainingRun).order_by(TrainingRun.started_at.desc()).limit(limit)
        if stock_id is not None:
            stmt = stmt.where(TrainingRun.stock_id == stock_id)
        return list(self.session.scalars(stmt))

    def prune_runs(self, stock_id: int, *, keep_last: int = 3) -> int:
        """Incremental-learning hygiene: keep only the newest N successful runs per symbol."""
        runs = self.recent_runs(stock_id, limit=100)
        stale = [r for r in runs if r.status == "success"][keep_last:]
        for r in stale:
            self.session.delete(r)
        self.session.flush()
        return len(stale)
