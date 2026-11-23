# SPEC 07 — Estratégia de Testes, Métricas e QA

> **Status:** Placeholder estruturado (a detalhar antes da Fase 5)  
> **Módulos afetados:** `/ml`, `/backend`, `/frontend`

## 1. Objetivo
Definir os cenários obrigatórios de validação técnica e de qualidade do modelo para comprovar o funcionamento ponta a ponta na apresentação ao vivo.

## 2. Escopo Resumido
- **Testes Automatizados (`pytest`):**
  - Unidade do pré-processamento compartilhado (imagem válida, imagem vazia, traço deslocado).
  - Inferência do modelo (classe esperada vs. rabisco retornando "Não sei").
  - Fluxo de integração API + PostgreSQL (`predict -> feedback -> stats -> chat`) em banco de testes isolado.
- **Avaliação de ML:** Comparação documentada entre acurácia offline (`test`), acurácia ao vivo (`live_canvas`) e taxa de rejeição de rabiscos (`noise_eval`).
- **Evidências:** Registro de métricas e aprendizados em `decis_es_arquiteturais_do_projeto.md` e validação final do setup em até 5 comandos no `README.md`.
