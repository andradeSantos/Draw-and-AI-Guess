# SPEC 06 — Frontend Web Next.js (Canvas, Dashboard e Chat da Equipe)

> **Status:** Aprovada (Fase 4)  
> **Skills vinculadas:** `/agent/skills/skill-nextjs-canvas.md`, `/agent/skills/skill-museum-analytics-chat.md`  
> **Módulos afetados:** `/frontend`

---

## 1. Objetivo
Especificar a aplicação web em **Next.js (App Router + TypeScript)** para a atração do **Museu Ciência Viva**, atendendo dois perfis na mesma interface:
1. **Visitante:** desenha no Canvas HTML5, visualiza o palpite da IA (ou o estado `"Não sei"`) e envia feedback.
2. **Equipe do Museu:** acompanha métricas em tempo real no Dashboard e interage com o Simulador de Chat local.

---

## 2. Estrutura de Navegação e Modos
- **Cabeçalho Fixo:** Identidade do Museu Ciência Viva, indicador de conexão com a API (`GET /health`) e alternador de abas claro para apresentação ao vivo:
  - **Modo Visitante (`Desenhar`)**
  - **Modo Equipe do Museu (`Dashboard & Chat`)**

---

## 3. Especificação do Canvas HTML5 (`DrawingCanvas`)
- **Resolução interna:** `360x360` px (responsivo via CSS `aspect-square`, compatível com mouse e toque).
- **Eventos:** `PointerEvent` (`onPointerDown`, `onPointerMove`, `onPointerUp`, `onPointerCancel`) com `touch-action: none` para evitar rolagem acidental em telas sensíveis ao toque.
- **Estilo de traço:** Fundo sólido branco (`#FFFFFF`) e traço preto (`#000000`) com `lineCap = "round"`, `lineJoin = "round"` e espessura ajustável (padrão `12px`), garantindo total compatibilidade com `/ml/preprocessing.py`.
- **Controles:** **"Adivinhar"** (exporta `canvas.toDataURL("image/png")` para `POST /predict`), **"Desfazer"** (pilha de histórico `ImageData`), **"Limpar"** e seletor simples de espessura.
- **Guia Visual:** Lista discreta das **18 classes reconhecidas** carregadas dinamicamente de `GET /classes`.

---

## 4. Estados de UI e Fluxo de Feedback
- **Estados da Predição:** `idle` (aguardando desenho), `loading` (enviando para `/predict`), `confident` (`is_unknown === false` com destaque do nome em PT-BR, barra de confiança %, latência ms e Top-3), `unknown` (`is_unknown === true` com card educativo explicando `"Não sei"`, transparência de confiança/margem e motivo) e `error` (erro de conexão com a API).
- **Feedback (`POST /feedback`):**
  - Botões **"Acertou"** e **"Errou"** (no estado `"Não sei"`, permite informar diretamente qual classe o visitante tentou desenhar).
  - Ao clicar em **"Errou"**, exibe seletor rápido com as 18 classes (`actual_class`) para alimentar o ranking de pares confundidos no PostgreSQL.
  - Bloqueia envio duplicado na UI após confirmação (alinhado ao HTTP `409`).

---

## 5. Integração com Backend
- Variável de ambiente `NEXT_PUBLIC_API_URL` (padrão `http://localhost:8000`) centralizada em `src/lib/api.ts`.
- Nenhuma lógica de pré-processamento ou inferência de IA roda no navegador.
