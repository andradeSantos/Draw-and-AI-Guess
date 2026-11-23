"""Rotas REST do FastAPI integrando PyTorch (/ml), PostgreSQL e Chat."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.repositories import drawing_repo
from backend.app.schemas.api import (
    ChatRequest,
    ChatResponse,
    ClassesResponse,
    ClassInfo,
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    PredictBase64Request,
    PredictResponse,
    StatsResponse,
)
from backend.app.services.chat_service import process_chat_message
from ml.classes import CLASSES, LABEL_TO_INDEX

router = APIRouter()


def _get_predictor(request: Request):
    predictor = getattr(request.app.state, "predictor", None)
    if predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modelo PyTorch não carregado.",
        )
    return predictor


@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check(request: Request, db: Session = Depends(get_db)) -> HealthResponse:
    predictor = getattr(request.app.state, "predictor", None)
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"PostgreSQL indisponível: {exc}",
        ) from exc

    if predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modelo PyTorch não carregado.",
        )

    return HealthResponse(
        status="ok",
        database=db_status,
        model_loaded=True,
        model_version=str(predictor.metadata.get("model_version", "unknown")),
    )


@router.get("/classes", response_model=ClassesResponse, tags=["Model"])
def list_classes(request: Request) -> ClassesResponse:
    predictor = _get_predictor(request)
    return ClassesResponse(
        num_classes=len(CLASSES),
        classes=[
            ClassInfo(
                index=c.index,
                label=c.label,
                display_pt=c.display_pt,
                category=c.category,
            )
            for c in CLASSES
        ],
        confidence_threshold=predictor.confidence_threshold,
        margin_threshold=predictor.margin_threshold,
    )


@router.post("/predict", response_model=PredictResponse, tags=["Inference"])
async def predict_drawing(
    request: Request,
    file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
) -> PredictResponse:
    predictor = _get_predictor(request)

    if file is not None:
        raw_bytes = await file.read()
        if not raw_bytes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Arquivo de imagem vazio.")
        image_input: str | bytes = raw_bytes
        source = "api_upload"
    else:
        try:
            body = await request.json()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Envie um JSON com 'image_base64' ou um arquivo via multipart/form-data.",
            ) from exc
        parsed = PredictBase64Request.model_validate(body)
        image_input = parsed.image_base64
        source = parsed.source

    try:
        result = predictor.predict(image_input, top_k=3)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Imagem inválida para pré-processamento: {exc}",
        ) from exc

    predicted_label = "Não sei" if result["is_unknown"] else str(result["predicted_class"])
    saved = drawing_repo.create_prediction(
        db,
        predicted_class=predicted_label,
        is_unknown=bool(result["is_unknown"]),
        confidence=float(result["confidence"]),
        margin=float(result["margin"]),
        top_k=list(result["top_k"]),
        latency_ms=float(result["latency_ms"]),
        source=source,
    )

    return PredictResponse(
        prediction_id=saved.id,
        predicted_class=predicted_label,
        display_name=str(result["display_name"]),
        is_unknown=bool(result["is_unknown"]),
        confidence=float(result["confidence"]),
        margin=float(result["margin"]),
        reason=result["reason"],
        top_k=result["top_k"],
        latency_ms=float(result["latency_ms"]),
        model_version=str(result["model_version"]),
    )


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Feedback"],
)
def submit_feedback(payload: FeedbackRequest, db: Session = Depends(get_db)) -> FeedbackResponse:
    prediction = drawing_repo.get_prediction(db, payload.prediction_id)
    if prediction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Predição não encontrada.")

    existing = drawing_repo.get_feedback_by_prediction(db, payload.prediction_id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Feedback já registrado para esta predição.",
        )

    if payload.actual_class is not None and payload.actual_class not in LABEL_TO_INDEX:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Classe inválida '{payload.actual_class}'. Use um dos 18 IDs válidos.",
        )

    saved = drawing_repo.create_feedback(
        db,
        prediction_id=payload.prediction_id,
        is_correct=payload.is_correct,
        actual_class=payload.actual_class,
    )
    return FeedbackResponse(
        feedback_id=saved.id,
        prediction_id=saved.prediction_id,
        is_correct=saved.is_correct,
        actual_class=saved.actual_class,
    )


@router.get("/stats", response_model=StatsResponse, tags=["Analytics"])
def get_stats(db: Session = Depends(get_db)) -> StatsResponse:
    stats = drawing_repo.get_aggregated_stats(db)
    return StatsResponse(**stats)


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
def museum_chat(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    stats = drawing_repo.get_aggregated_stats(db)
    response = process_chat_message(payload.message, stats)
    return ChatResponse(**response)
