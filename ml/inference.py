"""Serviço de inferência em CPU com política explícita de 'Não sei' (SPEC 03)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import torch

from ml.classes import INDEX_TO_LABEL, LABEL_TO_DISPLAY_PT, NUM_CLASSES
from ml.model import DrawGuessCNN
from ml.preprocessing import ImageInput, preprocess_image

DEFAULT_ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"


class DrawGuessPredictor:
    """Carrega pesos e metadados calibrados e executa inferência 100% em CPU."""

    def __init__(
        self,
        artifacts_dir: str | Path = DEFAULT_ARTIFACTS_DIR,
        confidence_threshold: float | None = None,
        margin_threshold: float | None = None,
    ) -> None:
        self.artifacts_dir = Path(artifacts_dir)
        weights_path = self.artifacts_dir / "draw_cnn.pt"
        metadata_path = self.artifacts_dir / "metadata.json"

        if not weights_path.exists():
            raise FileNotFoundError(f"Pesos do modelo não encontrados em {weights_path}")
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadados não encontrados em {metadata_path}")

        with metadata_path.open("r", encoding="utf-8") as f:
            self.metadata: dict[str, Any] = json.load(f)

        self.confidence_threshold = (
            confidence_threshold
            if confidence_threshold is not None
            else float(self.metadata.get("confidence_threshold", 0.55))
        )
        self.margin_threshold = (
            margin_threshold
            if margin_threshold is not None
            else float(self.metadata.get("margin_threshold", 0.15))
        )

        self.model = DrawGuessCNN(num_classes=int(self.metadata.get("num_classes", NUM_CLASSES)))
        state_dict = torch.load(weights_path, map_location="cpu", weights_only=True)
        self.model.load_state_dict(state_dict)
        self.model.eval()
        # Evita overhead de sincronização OpenMP em inferência CPU com batch=1
        if torch.get_num_threads() > 1:
            torch.set_num_threads(1)

    def predict(self, image_input: ImageInput, top_k: int = 3) -> dict[str, Any]:
        """Classifica a imagem ou retorna 'Não sei' quando há incerteza ou canvas vazio."""
        t0 = time.perf_counter()
        prep = preprocess_image(image_input)

        if prep.is_empty or prep.tensor is None:
            latency_ms = (time.perf_counter() - t0) * 1000.0
            return {
                "is_unknown": True,
                "predicted_class": None,
                "display_name": "Não sei",
                "confidence": 0.0,
                "margin": 0.0,
                "reason": prep.reason or "blank_canvas",
                "top_k": [],
                "model_version": self.metadata.get("model_version", "unknown"),
                "latency_ms": round(latency_ms, 2),
            }

        batch = prep.tensor.unsqueeze(0)  # (1, 1, 28, 28)
        with torch.inference_mode():
            logits = self.model(batch)
            probs = torch.softmax(logits, dim=1)[0]

        k = min(top_k, probs.numel())
        top_vals, top_idxs = torch.topk(probs, k=k)

        p1 = float(top_vals[0].item())
        p2 = float(top_vals[1].item()) if k > 1 else 0.0
        margin = p1 - p2
        best_idx = int(top_idxs[0].item())
        best_label = INDEX_TO_LABEL[best_idx]

        top_predictions = [
            {
                "label": INDEX_TO_LABEL[int(idx.item())],
                "display_name": LABEL_TO_DISPLAY_PT[INDEX_TO_LABEL[int(idx.item())]],
                "confidence": round(float(val.item()), 4),
            }
            for val, idx in zip(top_vals, top_idxs)
        ]

        if p1 < self.confidence_threshold:
            is_unknown = True
            reason = "low_confidence"
        elif margin < self.margin_threshold:
            is_unknown = True
            reason = "low_margin"
        else:
            is_unknown = False
            reason = None

        latency_ms = (time.perf_counter() - t0) * 1000.0
        return {
            "is_unknown": is_unknown,
            "predicted_class": None if is_unknown else best_label,
            "display_name": "Não sei" if is_unknown else LABEL_TO_DISPLAY_PT[best_label],
            "confidence": round(p1, 4),
            "margin": round(margin, 4),
            "reason": reason,
            "top_k": top_predictions,
            "model_version": self.metadata.get("model_version", "unknown"),
            "latency_ms": round(latency_ms, 2),
        }
