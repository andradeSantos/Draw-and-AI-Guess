# Arquitetura IA-First — Contexto, SPECS e SKILLS

Este documento define a estrutura de engenharia **IA-First** (baseada em *Spec-Driven Development* e *Agent Skills*) para o **Projeto 04: Desenhe e a IA adivinha**. O objetivo é dar aos agentes de código contexto cristalino, contratos imutáveis e procedimentos padronizados para construir o ecossistema (**PyTorch + FastAPI + Next.js + PostgreSQL**) com alta qualidade e baixo retrabalho.

---

## 1. Estrutura Recomendada do Repositório

```text
projeto-desenha-ia/
├── AGENTS.md                       # Contexto Geral e Regras Globais (lido primeiro por qualquer agente)
├── README.md                       # Instalação e execução em até 5 comandos
├── decisoes.md                     # Registro vivo das decisões arquiteturais
├── relato-ia.md                    # Registro de acertos e erros da IA durante o desenvolvimento
├── docker-compose.yml              # Orquestração local (PostgreSQL + Backend + Frontend)
├── .env.example                    # Variáveis de ambiente (DB, token de chat, thresholds)
│
├── specs/                          # O QUE construir (contratos e critérios de aceite)
│   ├── 01-domain-and-dataset.spec.md
│   ├── 02-ml-model-and-uncertainty.spec.md
│   ├── 03-database-schema.spec.md
│   ├── 04-backend-api.spec.md
│   ├── 05-frontend-canvas-dashboard.spec.md
│   ├── 06-chat-stats-interface.spec.md
│   └── 07-testing-and-qa.spec.md
│
├── .agent/skills/                  # COMO construir (procedimentos e padrões técnicos)
│   ├── pytorch-cnn-local/SKILL.md
│   ├── image-preprocessing-parity/SKILL.md
│   ├── fastapi-postgres-backend/SKILL.md
│   ├── nextjs-canvas-ui/SKILL.md
│   ├── qa-and-ml-metrics/SKILL.md
│   └── docs-and-compliance-sync/SKILL.md
│
├── ml/                             # Scripts de dados, pré-processamento, treino e avaliação (PyTorch)
├── backend/                        # API FastAPI, acesso ao PostgreSQL, serviço de inferência e chat
└── frontend/                       # Aplicação Next.js (Canvas do visitante + Dashboard)
```

---

## 2. Contexto Geral do Projeto (`AGENTS.md`)

O arquivo `AGENTS.md` (ou equivalente como `.cursorrules` / `CLAUDE.md`) funciona como a **constituição do projeto**. Todo agente deve carregá-lo automaticamente antes de alterar qualquer linha de código.

### O que deve constar no Contexto Geral:
1. **Resumo do Produto:** Atração interativa do Museu Ciência Viva onde visitantes desenham, a IA adivinha com grau de confiança ou diz "Não sei", coleta feedback e expõe estatísticas via chat/dashboard.
2. **Restrições Inegociáveis (Guardrails):**
   * **Zero serviços externos na inferência:** Nunca chamar APIs de visão externas ou modelos prontos de terceiros. O modelo deve ser treinado localmente em PyTorch.
   * **Execução 100% local em CPU:** Todo o código de inferência deve rodar sem GPU dedicada.
   * **Segurança e Dados Fictícios:** Proibido usar dados reais de pessoas; credenciais (PostgreSQL, token do Telegram) devem ficar exclusivamente em `.env` (nunca versionadas).
   * **Regra dos 5 comandos:** Qualquer alteração de infraestrutura deve preservar a capacidade de subir o projeto em até 5 comandos documentados no `README.md`.
   * **Código explicável:** Evitar abstrações mágicas ou *over-engineering*; o desenvolvedor precisa conseguir explicar cada bloco na apresentação ao vivo.
3. **Mapa de Stack e Versões:** Python 3.11+, PyTorch (CPU), FastAPI, Pydantic v2, PostgreSQL 16, Next.js (App Router + TypeScript).
4. **Regra de Trabalho IA-First:** *"Nunca implemente uma funcionalidade sem ler a SPEC correspondente em `/specs/`. Ao finalizar uma tarefa, valide contra os critérios de aceite da SPEC e atualize `decisoes.md` se houver mudança de rumo."*

---

## 3. SPECS (Especificações do Ecossistema)

As **SPECS** definem *o que* precisa existir, seus contratos de entrada/saída e *como saber que está pronto*. Abaixo estão os 7 módulos necessários:

| Arquivo SPEC | Responsabilidade e Conteúdo Essencial |
| :--- | :--- |
| **`01-domain-and-dataset.spec.md`** | Define a lista fechada de classes, origem das imagens de exemplo, separação estratificada (treino/validação/teste) e estratégia de inclusão de desenhos próprios e amostras de rabisco. |
| **`02-ml-model-and-uncertainty.spec.md`** | Especifica o pipeline de pré-processamento (binarização, *bounding box*, centralização, redimensionamento para tamanho fixo e normalização), arquitetura da CNN em PyTorch, formato de exportação dos pesos e a regra matemática do **"Não sei"** (ex.: $\max(P) < \tau_1$ ou $P_1 - P_2 < \tau_2$). |
| **`03-database-schema.spec.md`** | Modela as tabelas no PostgreSQL: registro de predições (timestamp, classe prevista, vetor/top-k de confiança, flag `is_unknown`), feedback do visitante (acertou/errou, classe real informada) e consultas SQL agregadas para estatísticas e matriz de confusão. |
| **`04-backend-api.spec.md`** | Contrato completo do FastAPI: `POST /api/predict` (recebe imagem do Canvas e retorna palpite, confiança, flag "Não sei" e `prediction_id`), `POST /api/feedback`, `GET /api/stats` (totais, taxa de acerto, confusões) e `GET /api/health`. Define schemas Pydantic e tratamento de erros. |
| **`05-frontend-canvas-dashboard.spec.md`** | Especifica a tela do visitante (Canvas responsivo para mouse/toque, controles de limpar e enviar, exibição clara da confiança e do estado "Não sei", botões de feedback) e a tela de Dashboard para acompanhar as métricas em tempo real. |
| **`06-chat-stats-interface.spec.md`** | Define o canal de chat obrigatório para a equipe do museu (Telegram com token em `.env` ou simulador local) e os comandos/intenções suportados: total de desenhos, taxa de acerto relatada pelos visitantes e classes mais confundidas. |
| **`07-testing-and-qa.spec.md`** | Define os cenários obrigatórios de teste: validação offline vs. ao vivo, bateria de rabiscos aleatórios (garantindo retorno "Não sei"), testes automatizados de API/banco e formato das evidências a entregar. |

---

## 4. SKILLS (Habilidades Especializadas dos Agentes)

Enquanto as **SPECS** dizem *o que* fazer, as **SKILLS** ensinam *como* o agente deve agir em cada domínio técnico, evitando erros clássicos de agentes genéricos.

### Skill 1: `pytorch-cnn-local`
* **Quando ativar:** Ao criar ou ajustar o modelo, loop de treinamento ou avaliação.
* **Diretrizes principais:**
  * Fixar *random seeds* para reprodutibilidade.
  * Construir CNN enxuta (2 a 3 blocos convolucionais) otimizada para inferência rápida em CPU (`torch.inference_mode()`).
  * Salvar artefatos versionados (pesos `.pt` + metadados JSON com mapeamento de classes e parâmetros de normalização).
  * Sempre gerar relatório de métricas (acurácia e matriz de confusão) ao final do treino.

### Skill 2: `image-preprocessing-parity`
* **Quando ativar:** Ao tocar na transformação de imagem no treino (`/ml`) ou na API (`/backend`).
* **Diretrizes principais:**
  * **Zero *Train-Serve Skew*:** O módulo de pré-processamento deve ser compartilhado (mesma função Python usada no treino e na inferência do FastAPI).
  * Garantir tratamento de fundo transparente/branco vindo do Canvas HTML5, inversão de cores consistente, recorte por *bounding box* com margem (*padding*) e preservação de proporção antes do *resize*.
  * Rejeitar automaticamente imagens vazias (canvas em branco) antes mesmo de chamar o modelo.

### Skill 3: `fastapi-postgres-backend`
* **Quando ativar:** Ao criar endpoints, modelos ORM, migrações ou serviços no backend.
* **Diretrizes principais:**
  * Carregar o modelo PyTorch uma única vez no ciclo de vida (*lifespan*) da aplicação FastAPI, nunca a cada requisição.
  * Usar Pydantic v2 para validação estrita e SQLAlchemy/SQLModel com sessões gerenciadas para o PostgreSQL.
  * Separar claramente rotas (`routers/`), regras de negócio (`services/`), inferência (`ml_service/`) e persistência (`repositories/`).
  * Configurar CORS adequadamente para o Next.js local.

### Skill 4: `nextjs-canvas-ui`
* **Quando ativar:** Ao construir o Canvas, o fluxo de feedback ou o Dashboard no frontend.
* **Diretrizes principais:**
  * Implementar Canvas com suporte a eventos de ponteiro (`PointerEvent`) para funcionar bem com mouse e touch, com espessura de traço calibrada.
  * Tipar rigorosamente todas as respostas da API FastAPI em TypeScript.
  * Tratar estados visuais de carregamento, erro de conexão, resposta confiante e estado **"Não sei"** de forma amigável e educativa para o visitante do museu.

### Skill 5: `qa-and-ml-metrics`
* **Quando ativar:** Ao escrever testes automatizados ou coletar provas de qualidade.
* **Diretrizes principais:**
  * Criar suíte `pytest` cobrindo pré-processamento, inferência com imagem válida, inferência com ruído/rabisco (validando "Não sei") e fluxo completo `predict -> feedback -> stats`.
  * Utilizar banco de testes isolado ou transações revertidas para não sujar o PostgreSQL principal.
  * Exportar resultados de testes e medições de forma legível para compor as evidências do projeto.

### Skill 6: `docs-and-compliance-sync`
* **Quando ativar:** Ao concluir um marco relevante ou alterar uma decisão técnica.
* **Diretrizes principais:**
  * Atualizar `decisoes.md` mantendo concisão (1 a 2 páginas ao final).
  * Registrar no `relato-ia.md` exemplos concretos de onde os agentes ajudaram e onde cometeram erros que precisaram de correção humana.
  * Verificar se o `README.md` continua rodando o sistema completo em até 5 comandos.

---

## 5. Ordem Sugerida de Execução (MVP Ponta a Ponta)

Seguindo a regra de ouro do projeto (*"um sistema pequeno que funciona vale mais do que um grande que não roda"*), os agentes devem construir o sistema nesta sequência:

1. **Fase 1 — Fundação e Contratos:** Criar `AGENTS.md`, `docker-compose.yml` (PostgreSQL) e fechar as `specs/01` a `04`.
2. **Fase 2 — Núcleo de IA (`/ml`):** Implementar o pré-processamento compartilhado, treinar a primeira versão da CNN em PyTorch, calibrar o "Não sei" e gerar a primeira matriz de confusão.
3. **Fase 3 — Backend + Banco (`/backend`):** Subir o FastAPI integrado ao PostgreSQL e ao modelo `.pt` treinado, expondo `/predict`, `/feedback` e `/stats`.
4. **Fase 4 — Frontend (`/frontend`):** Construir o Canvas em Next.js integrado à API + fluxo de feedback + Dashboard de métricas.
5. **Fase 5 — Chat da Equipe e QA:** Integrar o bot/simulador de chat consumindo `/stats`, rodar testes ao vivo, comparar métricas (offline vs. ao vivo) e finalizar `decisoes.md`, `relato-ia.md` e `README.md`.