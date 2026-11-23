# AGENTS.md — Contexto Global do Projeto 04: Desenhe e a IA Adivinha

Este documento é a **constituição técnica** do repositório. Todo agente de código deve lê-lo integralmente antes de criar ou modificar qualquer arquivo.

---

## 1. Objetivo do Produto
Atração interativa para o **Museu Ciência Viva** (fictício): o visitante desenha em um Canvas web, um modelo próprio em **PyTorch** tenta adivinhar o desenho entre **18 classes** (dígitos `0–9` + 8 símbolos simples: estrela, casa, círculo, triângulo, quadrado, coração, nuvem, árvore) exibindo o nível de confiança, ou responde explicitamente **"Não sei"** quando detecta rabiscos ou ambiguidade. O visitante envia feedback ("Acertou" / "Errou"), as interações são gravadas no **PostgreSQL** local e a equipe do museu consulta as estatísticas via **Dashboard Web** e **Simulador de Chat integrado**.

---

## 2. Arquitetura e Fluxo de Dados

```text
[ Canvas de Desenho (Next.js) ]
             │
             ▼ HTTP (POST /api/predict)
[ API Backend (FastAPI) ] ──► [ Pré-processamento Compartilhado ] ──► [ CNN Local (PyTorch / CPU) ]
             ▲                                                                   │
             │                                                                   ▼
[ Painel de Feedback ] ◄──────────────────────────────────────── [ Filtro "Não sei" (Confiança/Margem) ]
             │
             ▼ HTTP (POST /api/feedback) / SQL
[ PostgreSQL 16 (Local via Docker Compose) ] ──► [ Dashboard Web ] & [ Simulador de Chat Integrado ]
```

### Stack Oficial
- **IA / ML (`/ml`):** Python 3.11+, PyTorch (execução 100% CPU), NumPy, Pillow.
- **Backend (`/backend`):** FastAPI, Pydantic v2, SQLAlchemy/SQLModel, driver PostgreSQL (`psycopg`).
- **Frontend (`/frontend`):** Next.js (App Router + TypeScript).
- **Banco de Dados:** PostgreSQL 16 local via `docker-compose.yml`.

---

## 3. As 5 Regras Inegociáveis (Guardrails)

1. **Execução 100% Local (CPU):** Nenhuma imagem ou requisição pode sair da máquina local. Proibido depender de GPU dedicada em produção/inferência ou de serviços em nuvem.
2. **Modelo Próprio em PyTorch:** Proibido usar APIs externas de visão/IA ou modelos pré-treinados prontos de terceiros. A CNN deve ser treinada localmente com pipeline de pré-processamento compartilhado entre `/ml` e `/backend`.
3. **Tratamento Explícito de "Não sei":** O sistema nunca deve chutar com alta confiança diante de rabiscos, traços vazios ou desenhos ambíguos. A regra de incerteza (limiar de probabilidade máxima $\tau_1$, margem top-1/top-2 $\tau_2$ e/ou amostras de ruído) é requisito central.
4. **Dados Fictícios e Segredos via `.env`:** Proibido usar dados reais de visitantes. Credenciais de banco e configurações sensíveis ficam exclusivamente em `.env` (nunca versionadas; usar `.env.example` como modelo).
5. **Setup em até 5 Comandos (`README.md`):** Qualquer alteração de infraestrutura ou dependência deve preservar a capacidade de subir todo o ecossistema localmente em no máximo 5 comandos simples.

---

## 4. Fluxo de Trabalho IA-First (Obrigatório)

Antes de implementar qualquer módulo ou funcionalidade, o agente **DEVE**:
1. Ler a especificação correspondente em `/agent/specs/` (`01` a `07`) para entender contratos, entradas/saídas e critérios de aceite.
2. Ler a skill correspondente em `/agent/skills/` (`skill-*.md`) para seguir os padrões técnicos e respeitar o que **NÃO** deve ser feito.
3. Consultar `/agent/decisoes.md` caso haja dúvida sobre escopo ou justificativas arquiteturais.
4. Manter o código simples, modular e didático (explicável ao vivo, sem *over-engineering*).
5. **Atualização Incremental por Checkpoint (`skill-qa-and-docs`):** Ao final de cada fase ou alteração relevante de arquitetura, validar contra os critérios de aceite da SPEC correspondente e atualizar `/agent/decisoes.md` de forma incremental e objetiva, mantendo o documento dentro do limite final de **1 a 2 páginas**.

---

## 5. Comandos Previstos de Execução Local

> *(Os scripts e aplicações serão implementados nas Fases 2 a 5; abaixo está o contrato alvo de execução em até 5 comandos.)*

1. Subir banco PostgreSQL local: `docker compose up -d`
2. Preparar/treinar modelo local (quando necessário): `python -m ml.train`
3. Iniciar API FastAPI: `uvicorn backend.app.main:app --reload`
4. Iniciar Frontend Next.js: `cd frontend && npm run dev`
