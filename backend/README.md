# Módulo `/backend`
API REST em FastAPI integrada ao PostgreSQL local e ao serviço de inferência PyTorch.

Estrutura planejada:
- `app/core/` — Configurações (`.env`) e conexão com PostgreSQL
- `app/ml_service/` — Carregamento do modelo `.pt` e regra "Não sei"
- `app/repositories/` — Acesso a dados (predições e feedbacks)
- `app/services/` — Regras de negócio, estatísticas e interpretador do chat
- `app/routers/` — Endpoints (`/api/health`, `/api/predict`, `/api/feedback`, `/api/stats`, `/api/chat`)

*(Implementação prevista para a Fase 3, conforme `/agent/specs/03-database-schema.spec.md` e `04-backend-api.spec.md`.)*
