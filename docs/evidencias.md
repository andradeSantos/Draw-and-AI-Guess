# Evidências de Medição — Projeto 04 (Desenhe e a IA Adivinha)

> **Gerado em:** 2026-11-23 11:46:33 -03  
> **Versão do modelo:** `cnn-v1.0.0` (`τ₁=0.75`, `τ₂=0.1`)

## 1. Comparativo: Conjunto de Teste Separado vs. Sessão Ao Vivo (PostgreSQL)

| Indicador | Teste Separado (`evaluation_report.json`) | Ao Vivo (`PostgreSQL`) |
| :--- | :--- | :--- |
| **Amostras avaliadas** | 5.400 (`test`) + 300 (`noise_eval`) | 7 predições (0 com feedback) |
| **Acurácia global / relatada** | 97.81% | N/A (sem feedbacks registrados) |
| **Acurácia quando confiante** | 99.43% (cobertura 93.98%) | — |
| **Taxa de "Não sei"** | 89.00% (em rabiscos `noise_eval`) | 42.86% (3/7) |
| **Latência média em CPU** | 39.94 ms | Medida por requisição na API |

## 2. Top Pares Mais Confundidos

### No Conjunto de Teste Separado (`test`)
- `digit_0` (0) → `circle` (Círculo): **12** ocorrências
- `square` (Quadrado) → `cloud` (Nuvem): **10** ocorrências
- `tree` (Árvore) → `star` (Estrela): **9** ocorrências
- `circle` (Círculo) → `cloud` (Nuvem): **7** ocorrências
- `digit_8` (8) → `digit_5` (5): **4** ocorrências

### Ao Vivo no PostgreSQL (`feedbacks` com erro informado)
- Nenhum par confundido registrado até o momento.

## 3. Status da Amostra Ao Vivo
> **Aviso de transparência:** Até o momento há apenas **7 predições** e **0 feedbacks** gravados no PostgreSQL. Ainda não há uma bateria humana suficiente para reportar a taxa de acerto ao vivo como métrica consolidada. Após realizar sua sessão manual de desenhos no Canvas (`http://localhost:3000`), execute novamente:
> ```bash
> ./.venv/bin/python scripts/generate_evidence_report.py
> ```
