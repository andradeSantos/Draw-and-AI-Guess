# Skill — Chat de Estatísticas do Museu (`skill-museum-analytics-chat`)

## Quando usar
Ao implementar o simulador de chat integrado na aplicação web e o endpoint `POST /api/chat` para a equipe do museu.

## Responsabilidades
- Permitir que a equipe do museu faça perguntas simples em linguagem natural (ou via botões rápidos de sugestão) sobre:
  - Total de desenhos e quantidade de "Não sei".
  - Taxa de acerto relatada pelos visitantes.
  - Classes mais confundidas / erros frequentes.
- Responder exclusivamente com base nos dados reais agregados do PostgreSQL local.

## Padrões Técnicos e Boas Práticas
- Implementar mapeamento determinístico e transparente de intenções no backend (sem depender de LLMs externos).
- Fornecer resposta textual clara + dados estruturados para exibição amigável no componente de chat do Next.js.
- Incluir exemplos de perguntas sugeridas na interface para facilitar a demonstração ao vivo.

## O que NÃO fazer
- **NÃO** chamar APIs externas de LLM (OpenAI, Gemini, etc.) para interpretar perguntas ou gerar respostas.
- **NÃO** fabricar números quando o banco ainda não tiver registros (informar claramente que ainda há 0 interações).
