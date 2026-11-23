# Skill — Frontend Next.js e Canvas (`skill-nextjs-canvas`)

## Quando usar
Ao implementar a interface do visitante (Canvas de desenho), o fluxo de feedback e o Dashboard de métricas no `/frontend`.

## Responsabilidades
- Implementar um Canvas HTML5 responsivo com suporte a `PointerEvent` (mouse, trackpad e touch) e espessura de traço adequada ao modelo.
- Exibir claramente os três estados possíveis de resposta:
  1. Palpite confiante (classe + percentual de confiança + top-3 opcional).
  2. Estado **"Não sei"** (explicação amigável de que o desenho parece confuso ou fora das 18 classes).
  3. Estado de erro/carregamento.
- Disponibilizar o fluxo de feedback ("Acertou" / "Errou" com seleção da classe real) após a predição.
- Exibir o Dashboard de métricas consumindo `GET /api/stats`.

## Padrões Técnicos e Boas Práticas
- Usar Next.js App Router com TypeScript estrito, tipando todos os contratos da API FastAPI.
- Centralizar chamadas HTTP em um cliente de API (`src/lib/api.ts`) usando `NEXT_PUBLIC_API_URL`.
- Manter interface limpa, acessível e intuitiva para uso em totem/tela de museu.

## O que NÃO fazer
- **NÃO** rodar inferência de IA ou lógica de modelo dentro do navegador (toda inferência ocorre no backend FastAPI local).
- **NÃO** inventar métricas ou exibir dados estáticos simulados no lugar das respostas reais do backend.
- **NÃO** adicionar dependências pesadas desnecessárias que compliquem o setup local.
