# SPEC 03 — Schema do Banco de Dados (PostgreSQL)

> **Status:** Placeholder estruturado (a detalhar antes da Fase 3)  
> **Módulos afetados:** `/backend`, `docker-compose.yml`

## 1. Objetivo
Modelar a persistência local no PostgreSQL 16 para registrar predições da IA, feedbacks dos visitantes do museu e suportar consultas analíticas em tempo real.

## 2. Escopo Resumido
- **Tabela `predictions`:** `id` (UUID/serial), `created_at`, `predicted_class` (nullable se "Não sei"), `confidence` (float), `is_unknown` (boolean), `top_k_json` (JSONB com top-3 palpites e probabilidades), `model_version` (string).
- **Tabela `feedbacks`:** `id`, `prediction_id` (FK para `predictions`), `is_correct` (boolean), `actual_class` (string opcional quando o visitante corrige), `created_at`.
- **Consultas Analíticas:** Total de desenhos, total de "Não sei", taxa de acerto relatada pelos visitantes e pares de classes mais confundidas (matriz de confusão real).
- **Privacidade:** Nenhum dado pessoal identificável (PII) é armazenado.
