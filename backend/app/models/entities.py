"""Modelos ORM SQLAlchemy para `predictions` e `feedbacks` (SPEC 04)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True, nullable=False)
    predicted_class: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    is_unknown: Mapped[bool] = mapped_column(Boolean, index=True, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    margin: Mapped[float] = mapped_column(Float, nullable=False)
    top_k: Mapped[list[dict[str, object]]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
    )
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(32), default="live_canvas", nullable=False)

    feedback: Mapped[Feedback | None] = relationship(
        back_populates="prediction",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("predictions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, index=True, nullable=False)
    actual_class: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)

    prediction: Mapped[Prediction] = relationship(back_populates="feedback")
