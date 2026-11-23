# SPEC 05 — Frontend Web (Canvas do Visitante + Dashboard)

> **Status:** Placeholder estruturado (a detalhar antes da Fase 4)  
> **Módulos afetados:** `/frontend`

## 1. Objetivo
Especificar a interface web em Next.js (App Router + TypeScript) para a atração do Museu Ciência Viva e o painel de métricas.

## 2. Escopo Resumido
- **Tela do Visitante (Canvas):** Área de desenho responsiva (`PointerEvent` para mouse e toque), botões "Limpar" e "Adivinhar", exibição clara do palpite, barra/percentual de confiança, estado educativo **"Não sei"** para rabiscos e botões de feedback ("Acertou" / "Errou" + seleção da classe correta).
- **Dashboard de Métricas:** Visão em tempo real consumindo `GET /api/stats` (total de interações, taxa de acerto, taxa de "Não sei" e classes mais confundidas).
- **Integração com Simulador de Chat:** Acesso direto ao componente/aba de chat da equipe do museu definido na SPEC 06.
