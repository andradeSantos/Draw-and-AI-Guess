"""Motor determinístico e 100% offline do chat de estatísticas do museu."""

from __future__ import annotations

import unicodedata
from typing import Any

from ml.classes import LABEL_TO_DISPLAY_PT


def _normalize_text(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text.lower().strip())
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def _display_label(label: str) -> str:
    if label == "Não sei":
        return "Não sei"
    return LABEL_TO_DISPLAY_PT.get(label, label)


def process_chat_message(message: str, stats: dict[str, Any]) -> dict[str, Any]:
    """Interpreta perguntas da equipe do museu por regras determinísticas locais."""
    norm = _normalize_text(message)
    total = stats["total_predictions"]
    unknown_count = stats["unknown_count"]
    unknown_rate_pct = round(stats["unknown_rate"] * 100, 1)
    feedback_count = stats["feedback_count"]
    accuracy_rate = stats["accuracy_rate"]
    confusions = stats["top_confusions"]

    if any(kw in norm for kw in ("/stats", "resumo", "estatistica", "geral", "status")):
        acc_text = (
            f"{round(accuracy_rate * 100, 1)}% ({feedback_count} feedbacks)"
            if accuracy_rate is not None
            else "sem feedbacks registrados ainda"
        )
        reply = (
            f"Resumo do Museu Ciência Viva: {total} desenhos recebidos, "
            f"{unknown_count} respostas 'Não sei' ({unknown_rate_pct}%) e "
            f"taxa de acerto relatada de {acc_text}."
        )
        return {"intent": "summary", "reply": reply, "data": stats}

    if any(kw in norm for kw in ("confund", "erro", "matriz", "parec", "troc")):
        if not confusions:
            reply = (
                "Ainda não há erros com classe real informada para montar o ranking de confusões."
            )
        else:
            formatted = ", ".join(
                f"'{_display_label(c['predicted_class'])}' -> '{_display_label(c['actual_class'])}' ({c['count']}x)"
                for c in confusions[:3]
            )
            reply = f"Pares de classes mais confundidos pelos visitantes: {formatted}."
        return {"intent": "confusions", "reply": reply, "data": {"top_confusions": confusions}}

    if any(kw in norm for kw in ("acerto", "acuracia", "acertou", "precisao")):
        if accuracy_rate is None:
            reply = "Ainda não há feedbacks suficientes para calcular a taxa de acerto."
        else:
            pct = round(accuracy_rate * 100, 1)
            reply = f"A taxa de acerto relatada pelos visitantes é de {pct}% sobre {feedback_count} feedback(s)."
        return {
            "intent": "accuracy",
            "reply": reply,
            "data": {"accuracy_rate": accuracy_rate, "feedback_count": feedback_count},
        }

    if any(kw in norm for kw in ("quanto", "total", "volume", "desenho", "nao sei")):
        reply = (
            f"Foram registrados {total} desenho(s) até agora, sendo {unknown_count} "
            f"classificados como 'Não sei' ({unknown_rate_pct}%)."
        )
        return {
            "intent": "volume",
            "reply": reply,
            "data": {"total_predictions": total, "unknown_count": unknown_count},
        }

    reply = (
        "Comandos disponíveis para a equipe do museu: "
        "'resumo' (/stats), 'quantos desenhos', 'taxa de acerto' ou 'classes confundidas'."
    )
    return {"intent": "help", "reply": reply, "data": {}}
