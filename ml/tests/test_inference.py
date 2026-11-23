"""Testes do modelo CNN salvo, contrato de inferência e política 'Não sei' (SPEC 03)."""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

from ml.classes import INDEX_TO_LABEL
from ml.dataset import NOISE_PATH, SPLITS_PATH
from ml.inference import DrawGuessPredictor


def test_predictor_contract_and_known_test_samples() -> None:
    predictor = DrawGuessPredictor()
    data = np.load(SPLITS_PATH)
    x_test = data["x_test"]
    y_test = data["y_test"]

    # Warmup de 1 chamada para evitar jitter de inicialização da threadpool CPU
    _ = predictor.predict(x_test[0], top_k=3)

    # Avalia uma amostra representativa de 100 imagens do teste
    hits = 0
    evaluated = 0
    latencies = []
    for img_arr, true_idx in zip(x_test[:100], y_test[:100]):
        result = predictor.predict(img_arr, top_k=3)
        assert "is_unknown" in result
        assert "predicted_class" in result
        assert "display_name" in result
        assert "confidence" in result
        assert "top_k" in result
        assert len(result["top_k"]) == 3
        latencies.append(result["latency_ms"])

        if not result["is_unknown"]:
            evaluated += 1
            if result["predicted_class"] == INDEX_TO_LABEL[int(true_idx)]:
                hits += 1

    assert (sum(latencies) / len(latencies)) < 50.0
    assert evaluated >= 60
    assert (hits / evaluated) >= 0.80


def test_predictor_returns_unknown_for_blank_canvas() -> None:
    predictor = DrawGuessPredictor()
    blank = Image.new("RGB", (200, 200), (255, 255, 255))
    result = predictor.predict(blank)
    assert result["is_unknown"] is True
    assert result["predicted_class"] is None
    assert result["display_name"] == "Não sei"
    assert result["reason"] == "blank_canvas"


def test_predictor_rejects_scribbles_as_unknown() -> None:
    predictor = DrawGuessPredictor()
    noise_samples = np.load(NOISE_PATH)
    rejected = sum(1 for sample in noise_samples[:50] if predictor.predict(sample)["is_unknown"])
    rejection_rate = rejected / 50.0
    assert rejection_rate >= 0.70


def test_predictor_rejects_fresh_random_scribble_image() -> None:
    predictor = DrawGuessPredictor()
    rng = np.random.default_rng(123)
    img = Image.new("L", (160, 160), 255)
    draw = ImageDraw.Draw(img)
    pts = [(int(rng.integers(5, 155)), int(rng.integers(5, 155))) for _ in range(24)]
    draw.line(pts, fill=0, width=4)

    result = predictor.predict(img)
    assert result["is_unknown"] is True
    assert result["display_name"] == "Não sei"
