"""Testes unitários do pipeline de pré-processamento compartilhado (SPEC 02)."""

from __future__ import annotations

import base64
import io

import numpy as np
import torch
from PIL import Image, ImageDraw

from ml.preprocessing import preprocess_image


def test_blank_canvas_returns_empty() -> None:
    blank = Image.new("RGB", (200, 200), (255, 255, 255))
    res = preprocess_image(blank)
    assert res.is_empty is True
    assert res.tensor is None
    assert res.reason == "blank_canvas"


def test_transparent_rgba_blank_canvas_returns_empty() -> None:
    blank_rgba = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    res = preprocess_image(blank_rgba)
    assert res.is_empty is True
    assert res.tensor is None


def test_offcenter_stroke_is_centered_and_formatted() -> None:
    # Desenha um círculo no canto superior esquerdo de um canvas 200x200
    img = Image.new("RGB", (200, 200), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse((10, 10, 50, 50), outline=(0, 0, 0), width=5)

    res = preprocess_image(img)
    assert res.is_empty is False
    assert res.tensor is not None
    assert res.array_28x28 is not None
    assert res.tensor.shape == (1, 28, 28)
    assert res.tensor.dtype == torch.float32
    assert 0.0 <= float(res.tensor.min()) <= float(res.tensor.max()) <= 1.0

    # Verifica que o centro de massa foi trazido para perto do centro (14, 14)
    arr = res.array_28x28
    ys, xs = np.indices(arr.shape)
    cy = float((ys * arr).sum() / arr.sum())
    cx = float((xs * arr).sum() / arr.sum())
    assert 10.0 <= cy <= 18.0
    assert 10.0 <= cx <= 18.0


def test_base64_data_url_input_works() -> None:
    img = Image.new("RGBA", (120, 120), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.line([(20, 20), (100, 100)], fill=(0, 0, 0, 255), width=6)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")

    res = preprocess_image(b64)
    assert res.is_empty is False
    assert res.tensor is not None
    assert res.tensor.shape == (1, 28, 28)
