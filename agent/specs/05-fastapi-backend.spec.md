# SPEC 05 — Contrato da API Backend (FastAPI)

> **Status:** Aprovada (Fase 3)  
> **Skill vinculada:** `/agent/skills/skill-fastapi-postgres.md`, `/agent/skills/skill-museum-analytics-chat.md`  
> **Módulos afetados:** `/backend/app/`

---

## 1. Objetivo
Especificar os endpoints REST da API FastAPI, schemas Pydantic v2, carregamento único do modelo `DrawGuessPredictor` (`/ml/inference.py`) no *lifespan* da aplicação e tratamento de erros.

---

## 2. Regras Arquiteturais
- **Singleton no Startup:** `DrawGuessPredictor` é instanciado **uma única vez** no `lifespan` do FastAPI e armazenado em `app.state.predictor`.
- **Zero Duplicação:** Toda lógica de pré-processamento e inferência vem diretamente de `ml/inference.py` e `ml/classes.py`.
- **CORS:** Liberado para `CORS_ORIGINS` (padrão `http://localhost:3000`).

---

## 3. Endpoints e Contratos

### `GET /health`
Verifica saúde da API, modelo carregado e conexão com PostgreSQL (`SELECT 1`).
- **200 OK:** `{ "status": "ok", "database": "connected", "model_loaded": true, "model_version": "cnn-v1.0.0" }`
- **503 Service Unavailable:** se modelo ou banco estiverem indisponíveis.

### `GET /classes`
Retorna as 18 classes suportadas e limiares configurados.
- **200 OK:** `{ "num_classes": 18, "classes": [{ "index": 0, "label": "digit_0", "display_pt": "0", "category": "digit" }, ...], "confidence_threshold": 0.75, "margin_threshold": 0.10 }`

### `POST /predict`
Recebe imagem do Canvas via JSON (`{ "image_base64": "...", "source": "live_canvas" }`) ou `multipart/form-data` (`file`), executa `predictor.predict()`, persiste em `predictions` e retorna:
- **200 OK:**
  `{ "prediction_id": "<uuid>", "predicted_class": "star" | "Não sei", "display_name": "Estrela" | "Não sei", "is_unknown": false, "confidence": 0.96, "margin": 0.91, "reason": null | "blank_canvas" | "low_confidence" | "low_margin", "top_k": [...], "latency_ms": 12.4 }`
- **400 Bad Request:** imagem corrompida ou payload ausente (nunca retorna erro 500 para canvas vazio; canvas vazio retorna `200` com `is_unknown: true`, `predicted_class: "Não sei"`, `reason: "blank_canvas"`).

### `POST /feedback`
- **Request:** `{ "prediction_id": "<uuid>", "is_correct": true | false, "actual_class": "star" | null }`
- **Validações:**
  - `404 Not Found` se `prediction_id` não existir.
  - `409 Conflict` se já houver feedback registrado para esse `prediction_id`.
  - `422 Unprocessable Entity` se `actual_class` não pertencer às 18 classes válidas.
- **201 Created:** `{ "feedback_id": "<uuid>", "prediction_id": "<uuid>", "is_correct": false, "actual_class": "star" }`

### `GET /stats`
Retorna métricas agregadas reais do PostgreSQL:
- **200 OK:**
  `{ "total_predictions": 42, "unknown_count": 5, "unknown_rate": 0.119, "feedback_count": 30, "accuracy_rate": 0.8667, "top_confusions": [{ "predicted_class": "digit_0", "actual_class": "circle", "count": 3 }], "class_distribution": [{ "predicted_class": "star", "count": 8 }] }`

### `POST /chat`
Simulador de chat determinístico e 100% offline para a equipe do museu:
- **Request:** `{ "message": "Qual a taxa de acerto?" }`
- **200 OK:** `{ "intent": "accuracy" | "summary" | "volume" | "confusions" | "help", "reply": "...", "data": { ... } }`
