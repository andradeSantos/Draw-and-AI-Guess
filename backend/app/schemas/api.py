"""Schemas Pydantic v2 para contratos da API FastAPI (SPEC 05)."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    database: str
    model_loaded: bool
    model_version: str


class ClassInfo(BaseModel):
    index: int
    label: str
    display_pt: str
    category: str


class ClassesResponse(BaseModel):
    num_classes: int
    classes: list[ClassInfo]
    confidence_threshold: float
    margin_threshold: float


class TopKItem(BaseModel):
    label: str
    display_name: str
    confidence: float


class PredictBase64Request(BaseModel):
    image_base64: str = Field(..., min_length=1)
    source: str = Field(default="live_canvas", max_length=32)


class PredictResponse(BaseModel):
    prediction_id: uuid.UUID
    predicted_class: str
    display_name: str
    is_unknown: bool
    confidence: float
    margin: float
    reason: str | None = None
    top_k: list[TopKItem]
    latency_ms: float
    model_version: str


class FeedbackRequest(BaseModel):
    prediction_id: uuid.UUID
    is_correct: bool
    actual_class: str | None = None


class FeedbackResponse(BaseModel):
    feedback_id: uuid.UUID
    prediction_id: uuid.UUID
    is_correct: bool
    actual_class: str | None = None


class ConfusionPair(BaseModel):
    predicted_class: str
    actual_class: str
    count: int


class ClassDistributionItem(BaseModel):
    predicted_class: str
    count: int


class StatsResponse(BaseModel):
    total_predictions: int
    unknown_count: int
    unknown_rate: float
    feedback_count: int
    accuracy_rate: float | None
    top_confusions: list[ConfusionPair]
    class_distribution: list[ClassDistributionItem]


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)


class ChatResponse(BaseModel):
    intent: str
    reply: str
    data: dict[str, Any] = Field(default_factory=dict)
