"""Carregamento único do DrawGuessPredictor (/ml) para uso no lifespan da API."""

from __future__ import annotations

from backend.app.core.config import Settings
from ml.inference import DrawGuessPredictor


def load_predictor(settings: Settings) -> DrawGuessPredictor:
    """Instancia o modelo PyTorch em CPU uma única vez no startup."""
    return DrawGuessPredictor(
        artifacts_dir=settings.model_artifacts_dir,
        confidence_threshold=settings.unknown_confidence_threshold,
        margin_threshold=settings.unknown_margin_threshold,
    )
