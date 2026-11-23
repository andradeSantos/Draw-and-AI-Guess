# SPEC 06 — Interface de Chat de Estatísticas (Simulador Web Integrado)

> **Status:** Placeholder estruturado (a detalhar antes da Fase 5)  
> **Módulos afetados:** `/frontend`, `/backend`

## 1. Objetivo
Especificar o **Simulador de Chat integrado na aplicação web** para a equipe do Museu Ciência Viva consultar estatísticas do sistema de forma conversacional e 100% local.

## 2. Escopo Resumido
- **Canal escolhido:** Simulador de chat integrado no frontend Next.js (sem dependência de tokens externos ou APIs de terceiros).
- **Intenções / Comandos suportados:**
  - Total de desenhos recebidos e quantidade de respostas "Não sei".
  - Taxa de acerto relatada pelos visitantes (com base nos feedbacks).
  - Classes mais confundidas / ranking de erros.
  - Resumo geral do dia / estado do sistema.
- **Comportamento:** Interpretação determinística/baseada em intenções simples no backend (`POST /api/chat`), respondendo com números reais consultados diretamente no PostgreSQL (nunca números inventados).
