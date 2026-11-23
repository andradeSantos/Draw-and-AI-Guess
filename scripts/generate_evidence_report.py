"""Gera relatório comparativo entre métricas offline (teste separado) e métricas ao vivo (PostgreSQL)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.core.database import SessionLocal, init_db
from backend.app.repositories.drawing_repo import get_aggregated_stats
from ml.classes import LABEL_TO_DISPLAY_PT

EVAL_REPORT_PATH = ROOT_DIR / "ml" / "artifacts" / "evaluation_report.json"
OUTPUT_PATH = ROOT_DIR / "docs" / "evidencias.md"


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "N/A (sem feedbacks registrados)"
    return f"{value * 100:.2f}%"


def _display(label: str) -> str:
    return LABEL_TO_DISPLAY_PT.get(label, label)


def build_report() -> str:
    if not EVAL_REPORT_PATH.exists():
        raise FileNotFoundError(f"Arquivo de avaliação não encontrado: {EVAL_REPORT_PATH}")

    eval_data = json.loads(EVAL_REPORT_PATH.read_text(encoding="utf-8"))
    metrics = eval_data["metrics"]
    top_offline_confusions = eval_data.get("top_confused_pairs", [])

    init_db()
    with SessionLocal() as db:
        live_stats = get_aggregated_stats(db)

    now_iso = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    total_live = live_stats["total_predictions"]
    fb_count = live_stats["feedback_count"]

    lines = [
        "# Evidências de Medição — Projeto 04 (Desenhe e a IA Adivinha)",
        "",
        f"> **Gerado em:** {now_iso}  ",
        f"> **Versão do modelo:** `{eval_data['model_version']}` (`τ₁={eval_data['confidence_threshold']}`, `τ₂={eval_data['margin_threshold']}`)",
        "",
        "## 1. Comparativo: Conjunto de Teste Separado vs. Sessão Ao Vivo (PostgreSQL)",
        "",
        "| Indicador | Teste Separado (`evaluation_report.json`) | Ao Vivo (`PostgreSQL`) |",
        "| :--- | :--- | :--- |",
        f"| **Amostras avaliadas** | 5.400 (`test`) + 300 (`noise_eval`) | {total_live} predições ({fb_count} com feedback) |",
        f"| **Acurácia global / relatada** | {_fmt_pct(metrics['test_accuracy'])} | {_fmt_pct(live_stats['accuracy_rate'])} |",
        f"| **Acurácia quando confiante** | {_fmt_pct(metrics['test_accuracy_when_confident'])} (cobertura {_fmt_pct(metrics['test_confident_coverage'])}) | — |",
        f"| **Taxa de \"Não sei\"** | {_fmt_pct(metrics['noise_rejection_rate'])} (em rabiscos `noise_eval`) | {_fmt_pct(live_stats['unknown_rate'])} ({live_stats['unknown_count']}/{total_live}) |",
        f"| **Latência média em CPU** | {metrics['cpu_inference_latency_ms']:.2f} ms | Medida por requisição na API |",
        "",
        "## 2. Top Pares Mais Confundidos",
        "",
        "### No Conjunto de Teste Separado (`test`)",
    ]

    for pair in top_offline_confusions[:5]:
        t_lbl = _display(pair["true_class"])
        p_lbl = _display(pair["predicted_class"])
        lines.append(f"- `{pair['true_class']}` ({t_lbl}) → `{pair['predicted_class']}` ({p_lbl}): **{pair['count']}** ocorrências")

    lines.extend(["", "### Ao Vivo no PostgreSQL (`feedbacks` com erro informado)"])
    if live_stats["top_confusions"]:
        for pair in live_stats["top_confusions"]:
            p_lbl = _display(pair["predicted_class"])
            a_lbl = _display(pair["actual_class"])
            lines.append(f"- Previsto `{pair['predicted_class']}` ({p_lbl}) / Real `{pair['actual_class']}` ({a_lbl}): **{pair['count']}** ocorrências")
    else:
        lines.append("- Nenhum par confundido registrado até o momento.")

    lines.extend(["", "## 3. Status da Amostra Ao Vivo"])
    if fb_count < 15:
        lines.append(
            f"> **Aviso de transparência:** Até o momento há apenas **{total_live} predições** e **{fb_count} feedbacks** "
            "gravados no PostgreSQL. Ainda não há uma bateria humana suficiente para reportar a taxa de acerto ao vivo como métrica consolidada. "
            "Após realizar sua sessão manual de desenhos no Canvas (`http://localhost:3000`), execute novamente:"
        )
        lines.append("> ```bash")
        lines.append("> ./.venv/bin/python scripts/generate_evidence_report.py")
        lines.append("> ```")
    else:
        lines.append(
            f"Amostra ao vivo válida registrada com **{total_live} predições** e **{fb_count} feedbacks** humanos no PostgreSQL."
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    report = build_report()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(report, encoding="utf-8")
    print(report)
    print(f"Relatório salvo em: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
