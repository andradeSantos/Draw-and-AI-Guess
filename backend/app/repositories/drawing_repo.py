"""Repositório de acesso ao PostgreSQL para predições, feedbacks e estatísticas."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import case, desc, func, select
from sqlalchemy.orm import Session

from backend.app.models.entities import Feedback, Prediction


def create_prediction(
    db: Session,
    *,
    predicted_class: str,
    is_unknown: bool,
    confidence: float,
    margin: float,
    top_k: list[dict[str, Any]],
    latency_ms: float,
    source: str,
) -> Prediction:
    record = Prediction(
        predicted_class=predicted_class,
        is_unknown=is_unknown,
        confidence=confidence,
        margin=margin,
        top_k=top_k,
        latency_ms=latency_ms,
        source=source,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_prediction(db: Session, prediction_id: uuid.UUID) -> Prediction | None:
    return db.get(Prediction, prediction_id)


def get_feedback_by_prediction(db: Session, prediction_id: uuid.UUID) -> Feedback | None:
    stmt = select(Feedback).where(Feedback.prediction_id == prediction_id)
    return db.scalar(stmt)


def create_feedback(
    db: Session,
    *,
    prediction_id: uuid.UUID,
    is_correct: bool,
    actual_class: str | None,
) -> Feedback:
    record = Feedback(
        prediction_id=prediction_id,
        is_correct=is_correct,
        actual_class=actual_class,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_aggregated_stats(db: Session) -> dict[str, Any]:
    """Calcula métricas agregadas reais diretamente via SQL no PostgreSQL."""
    pred_row = db.execute(
        select(
            func.count(Prediction.id).label("total"),
            func.coalesce(func.sum(case((Prediction.is_unknown.is_(True), 1), else_=0)), 0).label("unknown_count"),
        )
    ).one()

    total_predictions = int(pred_row.total or 0)
    unknown_count = int(pred_row.unknown_count or 0)
    unknown_rate = round(unknown_count / total_predictions, 4) if total_predictions > 0 else 0.0

    fb_row = db.execute(
        select(
            func.count(Feedback.id).label("total"),
            func.coalesce(func.sum(case((Feedback.is_correct.is_(True), 1), else_=0)), 0).label("correct_count"),
        )
    ).one()

    feedback_count = int(fb_row.total or 0)
    correct_count = int(fb_row.correct_count or 0)
    accuracy_rate = round(correct_count / feedback_count, 4) if feedback_count > 0 else None

    confusion_stmt = (
        select(
            Prediction.predicted_class,
            Feedback.actual_class,
            func.count(Feedback.id).label("cnt"),
        )
        .join(Feedback, Feedback.prediction_id == Prediction.id)
        .where(Feedback.is_correct.is_(False), Feedback.actual_class.is_not(None))
        .group_by(Prediction.predicted_class, Feedback.actual_class)
        .order_by(desc("cnt"))
        .limit(5)
    )
    top_confusions = [
        {
            "predicted_class": row.predicted_class,
            "actual_class": row.actual_class,
            "count": int(row.cnt),
        }
        for row in db.execute(confusion_stmt).all()
    ]

    dist_stmt = (
        select(Prediction.predicted_class, func.count(Prediction.id).label("cnt"))
        .group_by(Prediction.predicted_class)
        .order_by(desc("cnt"))
    )
    class_distribution = [
        {"predicted_class": row.predicted_class, "count": int(row.cnt)}
        for row in db.execute(dist_stmt).all()
    ]

    return {
        "total_predictions": total_predictions,
        "unknown_count": unknown_count,
        "unknown_rate": unknown_rate,
        "feedback_count": feedback_count,
        "accuracy_rate": accuracy_rate,
        "top_confusions": top_confusions,
        "class_distribution": class_distribution,
    }
