"""Definição fechada das 18 classes do Projeto 04 (SPEC 01)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClassSpec:
    index: int
    label: str
    display_pt: str
    category: str
    quickdraw_name: str | None = None


CLASSES: tuple[ClassSpec, ...] = (
    *(
        ClassSpec(
            index=i,
            label=f"digit_{i}",
            display_pt=str(i),
            category="digit",
            quickdraw_name=None,
        )
        for i in range(10)
    ),
    ClassSpec(10, "star", "Estrela", "symbol", "star"),
    ClassSpec(11, "house", "Casa", "symbol", "house"),
    ClassSpec(12, "circle", "Círculo", "symbol", "circle"),
    ClassSpec(13, "triangle", "Triângulo", "symbol", "triangle"),
    ClassSpec(14, "square", "Quadrado", "symbol", "square"),
    ClassSpec(15, "heart", "Coração", "symbol", "heart"),
    ClassSpec(16, "cloud", "Nuvem", "symbol", "cloud"),
    ClassSpec(17, "tree", "Árvore", "symbol", "tree"),
)

NUM_CLASSES: int = len(CLASSES)
INDEX_TO_LABEL: dict[int, str] = {c.index: c.label for c in CLASSES}
LABEL_TO_INDEX: dict[str, int] = {c.label: c.index for c in CLASSES}
LABEL_TO_DISPLAY_PT: dict[str, str] = {c.label: c.display_pt for c in CLASSES}
SYMBOL_CLASSES: tuple[ClassSpec, ...] = tuple(c for c in CLASSES if c.quickdraw_name is not None)
