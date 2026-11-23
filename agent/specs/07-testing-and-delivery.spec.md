# SPEC 07 — Testes, Métricas, Segurança e Entrega Final

> **Status:** Aprovada (Fase 5)  
> **Skill vinculada:** `/agent/skills/skill-qa-and-docs.md`  
> **Módulos afetados:** `/ml`, `/backend`, `/frontend`, `/scripts`, raiz do repositório

---

## 1. Objetivo
Definir a matriz de testes automatizados, o protocolo de validação ao vivo no Canvas, a comparação entre métricas offline e métricas reais no PostgreSQL e o checklist final de segurança e entrega do Projeto 04 (*Desenhe e a IA adivinha* — Museu Ciência Viva).

---

## 2. Matriz de Testes Automatizados

| Camada | Comando | Escopo Coberto | Critério de Aceite |
| :--- | :--- | :--- | :--- |
| **ML — Pré-processamento** | `./.venv/bin/pytest ml/tests/test_preprocessing.py -v` | Canvas vazio, RGBA transparente, traço fora do centro, Base64 `data:image/png;base64,...` | 100% dos testes aprovados; saída determinística `(1, 28, 28)` em `[0.0, 1.0]` |
| **ML — Inferência & "Não sei"** | `./.venv/bin/pytest ml/tests/test_inference.py -v` | Contrato de predição, amostras do conjunto `test`, canvas em branco, bateria `noise_eval` e rabisco inédito | 100% dos testes aprovados; rejeição explícita (`is_unknown=True`) em rabiscos e canvas vazio |
| **Backend — API + PostgreSQL** | `./.venv/bin/pytest backend/tests/test_api.py -v` | `GET /health`, `GET /classes`, `POST /predict` (válido, vazio, rabisco), `POST /feedback` (`201` e duplicado `409`), `GET /stats`, `POST /chat` | 100% dos testes aprovados sem poluir dados de produção |
| **Frontend — Lint & Build** | `cd frontend && npm run lint && npm run build` | ESLint (`eslint .`), checagem de tipos TypeScript e build de produção Next.js App Router | Zero erros de lint, tipagem ou build |

---

## 3. Protocolo de Teste Ao Vivo (Canvas + Dashboard + Chat)

Para validar *data drift* e experiência real antes da apresentação ao vivo:
1. Subir PostgreSQL (`docker compose up -d`), API FastAPI (`uvicorn backend.app.main:app --reload`) e Frontend (`cd frontend && npm run dev`).
2. Na aba **Desenhar (Visitante)**, executar uma bateria manual de **~20 interações**:
   - **15 desenhos válidos** variados entre dígitos (`0–9`) e símbolos (`Estrela`, `Casa`, `Círculo`, `Triângulo`, `Quadrado`, `Coração`, `Nuvem`, `Árvore`), enviando feedback **"Acertou"** ou **"Errou"** (informando a classe real no seletor).
   - **5 rabiscos aleatórios / traços desconexos** para confirmar o acionamento educativo de **"Não sei"**.
3. Na aba **Dashboard & Chat (Equipe do Museu)**:
   - Conferir se os contadores de `GET /stats` (total de desenhos, taxa de `"Não sei"`, taxa de acerto e top confusões) refletem os novos registros no PostgreSQL.
   - Testar consultas no Simulador de Chat (`POST /chat`), como *"Resumo geral"*, *"Qual a taxa de acerto?"* e *"Quais classes mais confundem?"*.
4. Executar `./.venv/bin/python scripts/generate_evidence_report.py` para atualizar `docs/evidencias.md` com os números reais comparativos (teste separado vs. sessão ao vivo).

---

## 4. Checklist de Critérios de Aceite e Segurança (Pré-Entrega)
- [ ] Execução 100% local em CPU, sem chamadas a APIs externas ou modelos pré-treinados de terceiros.
- [ ] `.env` listado no `.gitignore` e ausente de versionamento; `.env.example` presente apenas com valores locais de exemplo.
- [ ] Nenhuma senha, token ou credencial sensível hardcoded no código-fonte (`/ml`, `/backend`, `/frontend`, `/scripts`).
- [ ] `./.venv/bin/pytest -v` com 100% de aprovação.
- [ ] `npm run lint` e `npm run build` em `/frontend` sem erros.
- [ ] `README.md` na raiz permitindo instalação e execução local em **no máximo 5 comandos**.
- [ ] `decisoes.md` consolidado na raiz em **1 a 2 páginas** (sincronizado com `/agent/decisoes.md`).
- [ ] `relato-ia.md` na raiz em **~0,5 página**, objetivo e honesto.
