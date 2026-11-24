# Decisões do Projeto — Desenhe e a IA Adivinha (Museu Ciência Viva)

> **Versão Final Consolidada (Fase 5)** — Execução 100% local em CPU, dados fictícios, sem APIs externas.

---

## 1. Como entendemos o problema e o que decidimos não resolver

O Museu Ciência Viva precisa de uma atração interativa em que visitantes desenham em uma tela digital e uma IA própria tenta adivinhar o desenho exibindo seu nível de confiança. Do ponto de vista de experiência do público, **chutar com alta confiança diante de um rabisco ou desenho ambíguo é pior do que errar ocasionalmente**. Por isso, o tratamento explícito de incerteza (**"Não sei"**) e o registro de feedback para auditoria da equipe são requisitos centrais do produto.

**O que decidimos NÃO resolver (escopo fechado):**
- **Reconhecimento aberto de centenas de classes:** Limitamos o domínio a **18 classes** (`0–9` e 8 símbolos simples: `Estrela`, `Casa`, `Círculo`, `Triângulo`, `Quadrado`, `Coração`, `Nuvem`, `Árvore`) para garantir alta precisão, boa explicabilidade ao vivo e baixa latência.
- **Inferência em nuvem ou GPU dedicada:** Nenhuma imagem sai da máquina local; toda a inferência roda em CPU convencional.
- **Aprendizado online em tempo real:** Feedbacks dos visitantes não alteram os pesos da rede em produção, evitando degradação ou envenenamento do modelo por rabiscos maliciosos; eles alimentam métricas reais e uma futura fila de retreino supervisionado offline.

---

## 2. Caminhos considerados, o que escolhemos e por quê

### Estratégia de IA
- **RAG / VLMs (Descartado):** Exigem modelos multimodais pesados inviáveis em CPU simples ou APIs externas (proibidas), além de não constituírem treinamento de classificador próprio.
- **Aprendizado por Reforço (Descartado):** Paradigma inadequado para classificação estática de traços; exigiria milhares de erros ao vivo e dificultaria a calibração determinística do `"Não sei"`.
- **Modelos Pré-Treinados Prontos (Descartado):** Viola a regra de treinar a própria IA. Usamos apenas dados públicos brutos (MNIST e Quick, Draw!) como matéria-prima de treino local.
- **CNN Própria em PyTorch (Escolhido):** A arquitetura `DrawGuessCNN` (3 blocos convolucionais `32 → 64 → 128` com `BatchNorm2d`, `ReLU`, `MaxPool2d`/`AdaptiveAvgPool2d` e classificador linear com `Dropout`) oferece controle total sobre tensores, Softmax e calibração de incerteza, mantendo leveza em CPU.

### Arquitetura e Stack
- **Pré-processamento único compartilhado (`ml/preprocessing.py`):** Importado diretamente pelo FastAPI (`app.state.predictor` carregado uma vez no `lifespan`), eliminando *train-serve skew* entre treino e inferência ao vivo.
- **FastAPI + PostgreSQL 16 (Docker Compose):** Mesmo ecossistema Python do PyTorch, contratos validados com Pydantic v2 e persistência relacional em duas tabelas (`predictions` e `feedbacks` com FK única `prediction_id`), evitando duplicidade de votos (`409 Conflict`) e armazenando zero dados pessoais.
- **Next.js (Canvas + Dashboard + Simulador de Chat Offline):** Interface única com alternância entre **Visitante** (`Canvas 360x360` via `PointerEvent`) e **Equipe do Museu** (Dashboard com agregações SQL em tempo real e chat determinístico offline por intenção sobre `GET /stats`, sem depender de LLMs ou tokens pagos).

### Chat de Estatísticas: Motor Determinístico + SQL vs. RAG
Para as consultas da equipe do museu (`POST /chat` em `backend/app/services/chat_service.py`), optamos por **roteamento determinístico por intenção sobre agregações SQL** (`get_aggregated_stats`) em vez de um pipeline **RAG**:
- **Simplicidade de código e manutenção:** Dispensa *chunking*, modelos de *embeddings*, banco vetorial e orquestração de prompts; toda a lógica cabe em um módulo enxuto e legível.
- **Menor consumo de recursos (100% CPU):** Evita carregar LLMs ou modelos de *embeddings* em memória (que competiriam com a CNN em CPU) e mantém a latência na casa de milissegundos.
- **Precisão numérica e zero alucinação:** RAG é voltado a texto não estruturado, enquanto métricas do museu (`COUNT`, taxa de acerto, ranking de confusões) exigem cálculo SQL exato em tempo real no PostgreSQL.
- **Determinismo e testabilidade:** A mesma pergunta sempre mapeia para a mesma intenção (`summary`, `confusions`, `accuracy`, `volume`, `help`) e retorna dados estruturados previsíveis, facilitando testes automatizados.
- **Critério de evolução:** RAG só passaria a fazer sentido se o chat precisasse responder perguntas abertas sobre documentos longos da exposição (ex.: manuais curatoriais), e não métricas tabulares.

---

## 3. Como medimos se a solução funciona

A validação foi dividida em avaliação offline imparcial, bateria de rejeição de rabiscos, suíte automatizada e auditoria contínua via PostgreSQL:

- **Conjunto de teste separado (`test`, 5.400 amostras, `seed=42`, divisão 70%/15%/15%):** Acurácia global de **`97,81%`**. Quando o modelo responde de forma confiante (cobertura de **`93,98%`**), a acurácia sobe para **`99,43%`**.
- **Rejeição de rabiscos (`noise_eval`, 300 amostras sintéticas):** Taxa de rejeição (**"Não sei"**) de **`89,00%`** aplicando os limiares calibrados na validação: confiança mínima $\tau_1 = 0{,}75$ e margem top-1/top-2 $\tau_2 = 0{,}10$ (além da detecção determinística de canvas vazio antes da rede).
- **Latência em CPU:** **`39,94 ms`** em média por predição (abaixo da meta de `50 ms`).
- **Principais pares confundidos no teste:** `digit_0 → circle` (`12`), `square → cloud` (`10`) e `tree → star` (`9`).
- **Ações tomadas para reduzir erros e *data drift*:** Centralização por centro de massa em `28x28` com *bounding box* e suavização gaussiana leve (`radius=0.45`), *data augmentation* apenas no treino (`RandomAffine` $\pm 12^\circ$, translação $\pm 10\%$, escala `0.88–1.12` e variação de espessura) e gerador paramétrico local para `heart` (ausente no repositório do Quick, Draw!).
- **Comparação com desenhos ao vivo (`PostgreSQL`):** O script `scripts/generate_evidence_report.py` compara automaticamente o `evaluation_report.json` com as tabelas reais do PostgreSQL; toda a suíte `pytest` (`11/11` testes) e o build/lint do Next.js foram validados integralmente.

---

## 4. Limites do sistema e o que faríamos com mais tempo

- **Limites conhecidos:** O modelo opera em conjunto fechado de 18 classes; desenhos compostos (múltiplos objetos na mesma tela) ou traços muito fora do padrão de treino tendem a cair em `"Não sei"`. Formas geometricamente próximas (`0` vs. `Círculo`, `Quadrado` vs. `Nuvem`) ainda concentram os raros erros.
- **Com mais tempo:** Coletaríamos uma base maior de desenhos reais feitos no próprio Canvas do museu para criar um ciclo periódico de **retreino supervisionado offline** (com curadoria dos feedbacks negativos), além de adicionar testes de interface automatizados (Playwright) para o fluxo completo do Canvas.
