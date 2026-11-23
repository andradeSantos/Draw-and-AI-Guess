# SPEC 04 — Contrato da API Backend (FastAPI)

> **Status:** Placeholder estruturado (a detalhar antes da Fase 3)  
> **Módulos afetados:** `/backend`

## 1. Objetivo
Definir todos os endpoints REST do backend FastAPI, schemas Pydantic v2, códigos de status HTTP e tratamento de erros.

## 2. Escopo Resumido
- `GET /api/health` — Verifica saúde da API, conexão com PostgreSQL e carregamento do modelo PyTorch.
- `POST /api/predict` — Recebe imagem do Canvas (Base64 PNG ou `multipart/form-data`), executa pré-processamento + inferência em CPU, aplica regra "Não sei", persiste em `predictions` e retorna `prediction_id`, `predicted_class`, `confidence`, `is_unknown` e `top_k`.
- `POST /api/feedback` — Recebe `prediction_id`, `is_correct` e `actual_class` opcional; persiste em `feedbacks`.
- `GET /api/stats` — Retorna métricas agregadas (total de desenhos, taxa de "Não sei", taxa de acerto relatada, distribuição por classe e top confusões) consumidas pelo Dashboard e pelo Simulador de Chat.
- `POST /api/chat` — Processa perguntas/comandos em linguagem simples da equipe do museu no simulador de chat local, consultando os dados reais de estatísticas do PostgreSQL.
