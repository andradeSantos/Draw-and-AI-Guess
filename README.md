# Desenhe e a IA Adivinha — Museu Ciência Viva

Atração interativa 100% local para o **Museu Ciência Viva** (fictício): o visitante desenha em um Canvas web, uma **CNN própria em PyTorch** (rodando em CPU) classifica o desenho entre **18 classes** (`0–9` e 8 símbolos: Estrela, Casa, Círculo, Triângulo, Quadrado, Coração, Nuvem, Árvore) ou responde explicitamente **"Não sei"** diante de rabiscos e ambiguidades. Os palpites e feedbacks (*Acertou* / *Errou*) são salvos no **PostgreSQL 16** e consultados pela equipe do museu via **Dashboard Web** e **Simulador de Chat offline**.

---

## Arquitetura Resumida

- **`/ml`:** Pipeline único de pré-processamento (`preprocessing.py`), dataset estratificado (`dataset.py`), arquitetura `DrawGuessCNN` (`model.py`), treino reproduzível em CPU (`train.py`) e inferência com filtro `"Não sei"` (`inference.py`).
- **`/backend`:** API REST em **FastAPI** + **SQLAlchemy** + **PostgreSQL 16**, carregando o modelo PyTorch uma única vez no `lifespan` e expondo `/health`, `/classes`, `/predict`, `/feedback`, `/stats` e `/chat`.
- **`/frontend`:** Aplicação **Next.js (App Router + TypeScript)** com Canvas HTML5 (`360x360`), exibição de confiança/Top-3, coleta de feedback e aba **Dashboard & Chat** para a equipe do museu.

---

## Como Instalar e Rodar (em até 5 comandos)

> **Pré-requisitos:** Docker + Docker Compose, Python 3.11+ e Node.js 20+.

```bash
# 1. Configurar variáveis locais e subir o PostgreSQL 16
cp .env.example .env && docker compose up -d

# 2. Criar ambiente virtual Python e instalar dependências de Backend e ML
python3 -m venv .venv && .venv/bin/pip install -r backend/requirements.txt torch torchvision numpy pillow pytest

# 3. (Opcional se ml/artifacts/draw_cnn.pt já existir) Treinar o modelo CNN localmente
.venv/bin/python -m ml.train

# 4. Iniciar a API FastAPI (porta 8000)
.venv/bin/uvicorn backend.app.main:app --reload

# 5. Em outro terminal, instalar dependências e iniciar o Frontend Next.js (porta 3000)
cd frontend && npm install && npm run dev
```

Acesse **`http://localhost:3000`** no navegador.

---

## Testes e Relatório de Evidências

- **Suíte automatizada (`ml` + `backend`):**
  ```bash
  ./.venv/bin/pytest -v
  ```
- **Lint e Build do Frontend:**
  ```bash
  cd frontend && npm run lint && npm run build
  ```
- **Comparativo de Evidências (Teste Separado vs. Desenhos Ao Vivo no PostgreSQL):**
  ```bash
  ./.venv/bin/python scripts/generate_evidence_report.py
  ```

---

## Como Usar a Aplicação

1. **Modo Visitante (`Desenhar`):** Desenhe no quadro branco, clique em **Adivinhar** para ver o palpite, a barra de confiança e o Top-3 (ou o aviso educativo **"Não sei"** em rabiscos) e envie seu feedback (**Acertou** / **Errou**).
2. **Modo Equipe do Museu (`Dashboard & Chat`):** Alterne na barra superior para acompanhar métricas em tempo real (total de desenhos, taxa de `"Não sei"`, taxa de acerto e pares mais confundidos) e fazer perguntas no **Simulador de Chat** local.
