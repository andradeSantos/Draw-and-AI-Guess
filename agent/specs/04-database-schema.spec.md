# SPEC 04 — Schema do Banco de Dados (PostgreSQL 16)

> **Status:** Aprovada (Fase 3)  
> **Skill vinculada:** `/agent/skills/skill-fastapi-postgres.md`  
> **Módulos afetados:** `/backend/app/models/`, `/backend/app/core/database.py`

---

## 1. Objetivo
Modelar a persistência local no **PostgreSQL 16** (orquestrado via `docker-compose.yml`) para registrar todas as predições da CNN e os feedbacks enviados pelos visitantes do Museu Ciência Viva, sem armazenar dados pessoais (PII).

---

## 2. Tabelas e Colunas

### 2.1 Tabela `predictions`
Registra cada desenho submetido ao modelo PyTorch.

| Coluna | Tipo PostgreSQL | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY`, default `uuid4` | Identificador único da predição |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, default `now()` | Momento da inferência |
| `predicted_class` | `VARCHAR(64)` | `NOT NULL` | Classe prevista (`digit_0`..`tree`) ou `"Não sei"` |
| `is_unknown` | `BOOLEAN` | `NOT NULL`, indexado | `true` quando acionado o filtro "Não sei" |
| `confidence` | `DOUBLE PRECISION` | `NOT NULL` | Maior probabilidade Softmax ($P_1$) |
| `margin` | `DOUBLE PRECISION` | `NOT NULL` | Diferença entre top-1 e top-2 ($P_1 - P_2$) |
| `top_k` | `JSONB` | `NOT NULL` | Lista com top-3 palpites (`label`, `display_name`, `confidence`) |
| `latency_ms` | `DOUBLE PRECISION` | `NOT NULL` | Tempo de inferência + pré-processamento em CPU (ms) |
| `source` | `VARCHAR(32)` | `NOT NULL`, default `'live_canvas'` | Origem da imagem (ex.: `live_canvas`, `api_upload`) |

**Índices:** `ix_predictions_created_at`, `ix_predictions_predicted_class`, `ix_predictions_is_unknown`.

### 2.2 Tabela `feedbacks`
Registra o retorno explícito do visitante sobre a predição.

| Coluna | Tipo PostgreSQL | Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | `UUID` | `PRIMARY KEY`, default `uuid4` | Identificador único do feedback |
| `prediction_id` | `UUID` | `NOT NULL`, `UNIQUE`, `FK -> predictions.id (ON DELETE CASCADE)` | Garante no máximo 1 feedback por predição |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, default `now()` | Momento do envio |
| `is_correct` | `BOOLEAN` | `NOT NULL` | `true` ("Acertou") ou `false` ("Errou") |
| `actual_class` | `VARCHAR(64)` | `NULLABLE` | Classe real informada pelo visitante quando a IA errou ou disse "Não sei" |

**Índices:** `ix_feedbacks_is_correct`, `ix_feedbacks_actual_class`.

---

## 3. Inicialização e Privacidade
- A criação das tabelas ocorre automaticamente no *lifespan* do FastAPI (`Base.metadata.create_all`) para manter o setup em até 5 comandos.
- **Zero PII:** Nenhum IP, nome, e-mail ou imagem bruta é salvo no banco.
