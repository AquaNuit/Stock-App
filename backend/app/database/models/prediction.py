"""Stored 7-day forecast rows + model registry + training runs."""

from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), index=True)
    training_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("training_runs.id", ondelete="SET NULL"), nullable=True
    )

    prediction_date: Mapped[date] = mapped_column(Date)  # when the forecast was generated
    target_date: Mapped[date] = mapped_column(Date)  # day being predicted
    horizon: Mapped[int] = mapped_column(Integer)

    predicted_price: Mapped[float] = mapped_column(Float)
    lower_bound: Mapped[float] = mapped_column(Float)
    upper_bound: Mapped[float] = mapped_column(Float)
    expected_change_pct: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[str] = mapped_column(String(8), default="low")

    model_name: Mapped[str] = mapped_column(String(32))
    model_version: Mapped[str] = mapped_column(String(128), default="")
    model_rmse: Mapped[float | None] = mapped_column(Float, nullable=True)
    range_used: Mapped[str] = mapped_column(String(8), default="2y")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    stock = relationship("Stock", back_populates="predictions")

    __table_args__ = (
        Index("ix_predictions_stock_created", "stock_id", "prediction_date"),
        Index("ix_predictions_lookup", "stock_id", "target_date", "horizon"),
    )


class Model(Base):
    """A trained, versioned model instance with validation metrics."""

    __tablename__ = "models"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32), index=True)
    version: Mapped[str] = mapped_column(String(128), unique=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(16), default="trained")  # trained|selected|retired

    hyperparams: Mapped[dict] = mapped_column(JSON, default=dict)
    feature_list: Mapped[list] = mapped_column(JSON, default=list)

    rmse: Mapped[float | None] = mapped_column(Float, nullable=True)
    mae: Mapped[float | None] = mapped_column(Float, nullable=True)
    mape: Mapped[float | None] = mapped_column(Float, nullable=True)
    r2: Mapped[float | None] = mapped_column(Float, nullable=True)

    data_range: Mapped[str] = mapped_column(String(8), default="2y")
    train_rows: Mapped[int] = mapped_column(Integer, default=0)
    val_rows: Mapped[int] = mapped_column(Integer, default=0)

    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    runs = relationship("TrainingRun", back_populates="model")


class TrainingRun(Base):
    """One comparison/training execution; links to the winning model."""

    __tablename__ = "training_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), index=True)
    model_id: Mapped[int | None] = mapped_column(ForeignKey("models.id", ondelete="SET NULL"), nullable=True)

    status: Mapped[str] = mapped_column(String(16), default="running", index=True)  # running|success|failed
    trigger_type: Mapped[str] = mapped_column(String(16), default="manual")  # manual|scheduled|auto

    leaderboard: Mapped[list] = mapped_column(JSON, default=list)  # [{name, rmse, mae, mape, r2, ...}]
    best_model: Mapped[str] = mapped_column(String(32), default="")
    best_rmse: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_range: Mapped[str] = mapped_column(String(8), default="2y")

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str] = mapped_column(Text, default="")

    model = relationship("Model", back_populates="runs")
