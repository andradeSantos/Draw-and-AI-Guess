"""Pipeline único e determinístico de pré-processamento de imagens (SPEC 02).

Compartilhado entre o treinamento em `/ml` e a inferência no `/backend` para
garantir zero Train-Serve Skew. Não possui dependências de FastAPI ou banco.
"""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from typing import Union

import numpy as np
import torch
from PIL import Image, ImageFilter

ImageInput = Union[str, bytes, Image.Image, np.ndarray]

TARGET_SIZE = 28
INNER_BOX_SIZE = 20
DEFAULT_INK_THRESHOLD = 20
DEFAULT_MIN_ACTIVE_PIXELS = 8


@dataclass(frozen=True)
class PreprocessResult:
    is_empty: bool
    tensor: torch.Tensor | None
    array_28x28: np.ndarray | None
    reason: str | None = None


def _decode_to_pil(image_input: ImageInput) -> Image.Image:
    """Converte entrada heterogênea (Base64, bytes, PIL ou ndarray) para PIL.Image."""
    if isinstance(image_input, Image.Image):
        return image_input

    if isinstance(image_input, str):
        payload = image_input.split(",", 1)[1] if "," in image_input else image_input
        raw_bytes = base64.b64decode(payload)
        return Image.open(io.BytesIO(raw_bytes))

    if isinstance(image_input, (bytes, bytearray)):
        return Image.open(io.BytesIO(raw_bytes := bytes(image_input)))

    if isinstance(image_input, np.ndarray):
        arr = image_input
        if arr.ndim == 3 and arr.shape[2] == 1:
            arr = arr[:, :, 0]
        if arr.dtype != np.uint8:
            max_val = float(arr.max()) if arr.size > 0 else 0.0
            scale = 255.0 if max_val <= 1.0 else 1.0
            arr = np.clip(arr * scale, 0, 255).astype(np.uint8)
        return Image.fromarray(arr)

    raise TypeError(f"Tipo de imagem não suportado: {type(image_input)!r}")


def _to_grayscale_dark_bg(img: Image.Image) -> np.ndarray:
    """Converte para escala de cinza uint8 com fundo escuro (0) e traço claro (>0)."""
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        white_bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        gray = Image.alpha_composite(white_bg, rgba).convert("L")
    else:
        gray = img.convert("L")

    arr = np.asarray(gray, dtype=np.uint8).copy()

    # Inspeciona as bordas (e mediana como fallback) para detectar fundo claro (ex.: Canvas branco)
    if arr.shape[0] >= 2 and arr.shape[1] >= 2:
        border = np.concatenate([arr[0, :], arr[-1, :], arr[:, 0], arr[:, -1]])
        is_light_bg = float(np.median(border)) > 127.0
    else:
        is_light_bg = float(np.median(arr)) > 127.0

    if is_light_bg:
        arr = 255 - arr

    return arr


def _center_by_mass(cropped: np.ndarray) -> Image.Image:
    """Redimensiona preservando proporção para 20x20 e centraliza pelo centro de massa em 28x28."""
    h, w = cropped.shape
    scale = INNER_BOX_SIZE / max(h, w)
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))

    pil_crop = Image.fromarray(cropped, mode="L").resize(
        (new_w, new_h), resample=Image.Resampling.BILINEAR
    )
    resized = np.asarray(pil_crop, dtype=np.float32)

    total_mass = float(resized.sum())
    if total_mass > 0.0:
        ys, xs = np.indices(resized.shape, dtype=np.float32)
        cy = float((ys * resized).sum() / total_mass)
        cx = float((xs * resized).sum() / total_mass)
    else:
        cy = new_h / 2.0
        cx = new_w / 2.0

    # Alinha o centro de massa ao centro (14, 14) do quadro 28x28
    offset_y = int(round(TARGET_SIZE / 2.0 - cy))
    offset_x = int(round(TARGET_SIZE / 2.0 - cx))

    offset_y = max(0, min(TARGET_SIZE - new_h, offset_y))
    offset_x = max(0, min(TARGET_SIZE - new_w, offset_x))

    canvas = np.zeros((TARGET_SIZE, TARGET_SIZE), dtype=np.uint8)
    canvas[offset_y : offset_y + new_h, offset_x : offset_x + new_w] = np.clip(
        resized, 0, 255
    ).astype(np.uint8)

    return Image.fromarray(canvas, mode="L")


def preprocess_image(
    image_input: ImageInput,
    *,
    ink_threshold: int = DEFAULT_INK_THRESHOLD,
    min_active_pixels: int = DEFAULT_MIN_ACTIVE_PIXELS,
) -> PreprocessResult:
    """Executa o pipeline completo de pré-processamento para inferência e treino."""
    pil_img = _decode_to_pil(image_input)
    arr = _to_grayscale_dark_bg(pil_img)

    # Remove ruído fraco de fundo
    arr[arr < ink_threshold] = 0

    active_ys, active_xs = np.nonzero(arr)
    if len(active_ys) < min_active_pixels:
        return PreprocessResult(
            is_empty=True,
            tensor=None,
            array_28x28=None,
            reason="blank_canvas",
        )

    # Recorte pela bounding box do desenho
    y_min, y_max = int(active_ys.min()), int(active_ys.max()) + 1
    x_min, x_max = int(active_xs.min()), int(active_xs.max()) + 1
    cropped = arr[y_min:y_max, x_min:x_max]

    # Centraliza pelo centro de massa em 28x28 e aplica suavização leve
    centered_img = _center_by_mass(cropped)
    smoothed_img = centered_img.filter(ImageFilter.GaussianBlur(radius=0.45))

    norm = np.asarray(smoothed_img, dtype=np.float32) / 255.0
    max_val = float(norm.max())
    if max_val > 0.0:
        norm = norm / max_val

    tensor = torch.from_numpy(norm).unsqueeze(0).contiguous()  # (1, 28, 28)
    return PreprocessResult(
        is_empty=False,
        tensor=tensor,
        array_28x28=norm,
        reason=None,
    )
