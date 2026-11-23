"""Testes de integração da API FastAPI + PostgreSQL + PyTorch (/ml)."""

from __future__ import annotations

import base64
import io
import uuid

import numpy as np
from PIL import Image, ImageDraw


def _pil_to_base64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _make_circle_image() -> str:
    img = Image.new("RGB", (200, 200), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse((45, 45, 155, 155), outline=(0, 0, 0), width=10)
    return _pil_to_base64(img)


def _make_blank_image() -> str:
    img = Image.new("RGB", (200, 200), (255, 255, 255))
    return _pil_to_base64(img)


def _make_scribble_image() -> str:
    rng = np.random.default_rng(123)
    img = Image.new("RGB", (160, 160), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    pts = [(int(rng.integers(5, 155)), int(rng.integers(5, 155))) for _ in range(24)]
    draw.line(pts, fill=(0, 0, 0), width=4)
    return _pil_to_base64(img)


def test_health_and_classes(client) -> None:
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    health = health_resp.json()
    assert health["status"] == "ok"
    assert health["database"] == "connected"
    assert health["model_loaded"] is True

    classes_resp = client.get("/classes")
    assert classes_resp.status_code == 200
    data = classes_resp.json()
    assert data["num_classes"] == 18
    assert len(data["classes"]) == 18


def test_predict_valid_blank_and_scribble(client) -> None:
    # 1. Desenho válido (círculo)
    res_valid = client.post("/predict", json={"image_base64": _make_circle_image()})
    assert res_valid.status_code == 200
    body_valid = res_valid.json()
    assert "prediction_id" in body_valid
    assert body_valid["is_unknown"] is False
    assert body_valid["predicted_class"] in {"circle", "digit_0"}
    assert len(body_valid["top_k"]) == 3

    # 2. Canvas vazio -> retorna 200 graciosamente com "Não sei"
    res_blank = client.post("/predict", json={"image_base64": _make_blank_image()})
    assert res_blank.status_code == 200
    body_blank = res_blank.json()
    assert body_blank["is_unknown"] is True
    assert body_blank["predicted_class"] == "Não sei"
    assert body_blank["reason"] == "blank_canvas"

    # 3. Rabisco aleatório -> retorna "Não sei"
    res_scribble = client.post("/predict", json={"image_base64": _make_scribble_image()})
    assert res_scribble.status_code == 200
    body_scribble = res_scribble.json()
    assert body_scribble["is_unknown"] is True
    assert body_scribble["predicted_class"] == "Não sei"


def test_feedback_stats_and_chat_flow(client) -> None:
    # Predição 1: acerto
    p1 = client.post("/predict", json={"image_base64": _make_circle_image()}).json()
    fb1 = client.post(
        "/feedback",
        json={"prediction_id": p1["prediction_id"], "is_correct": True},
    )
    assert fb1.status_code == 201

    # Duplicidade de feedback para mesma predição -> 409
    fb1_dup = client.post(
        "/feedback",
        json={"prediction_id": p1["prediction_id"], "is_correct": False},
    )
    assert fb1_dup.status_code == 409

    # Predição 2: erro com actual_class informado
    p2 = client.post("/predict", json={"image_base64": _make_circle_image()}).json()
    fb2 = client.post(
        "/feedback",
        json={
            "prediction_id": p2["prediction_id"],
            "is_correct": False,
            "actual_class": "square",
        },
    )
    assert fb2.status_code == 201

    # Predição 3: rabisco ("Não sei")
    _ = client.post("/predict", json={"image_base64": _make_scribble_image()}).json()

    # Feedback para prediction_id inexistente -> 404
    fb_missing = client.post(
        "/feedback",
        json={"prediction_id": str(uuid.uuid4()), "is_correct": True},
    )
    assert fb_missing.status_code == 404

    # Validação de /stats
    stats_resp = client.get("/stats")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total_predictions"] == 3
    assert stats["unknown_count"] == 1
    assert stats["feedback_count"] == 2
    assert stats["accuracy_rate"] == 0.5
    assert len(stats["top_confusions"]) == 1
    assert stats["top_confusions"][0]["actual_class"] == "square"
    assert stats["top_confusions"][0]["count"] == 1

    # Validação de /chat
    chat_vol = client.post("/chat", json={"message": "Quantos desenhos foram feitos?"})
    assert chat_vol.status_code == 200
    assert chat_vol.json()["intent"] == "volume"
    assert "3 desenho" in chat_vol.json()["reply"]

    chat_acc = client.post("/chat", json={"message": "Qual a taxa de acerto?"})
    assert chat_acc.status_code == 200
    assert chat_acc.json()["intent"] == "accuracy"
    assert "50.0%" in chat_acc.json()["reply"]

    chat_conf = client.post("/chat", json={"message": "Quais classes a IA mais confunde?"})
    assert chat_conf.status_code == 200
    assert chat_conf.json()["intent"] == "confusions"
    assert "Quadrado" in chat_conf.json()["reply"]

    chat_help = client.post("/chat", json={"message": "/help"})
    assert chat_help.status_code == 200
    assert chat_help.json()["intent"] == "help"
