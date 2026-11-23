# Skill — QA, Métricas e Documentação (`skill-qa-and-docs`)

## Quando usar
Ao escrever testes automatizados, coletar métricas offline vs. ao vivo, validar o setup do projeto ou atualizar a documentação.

## Responsabilidades
- Criar e manter suíte `pytest` cobrindo pré-processamento, inferência válida, rejeição de rabiscos ("Não sei") e fluxo ponta a ponta (`predict -> feedback -> stats -> chat`).
- Garantir isolamento dos testes (transações revertidas ou banco de teste separado, sem poluir o banco principal).
- Manter `/agent/decisoes.md` conciso (1 a 2 páginas) e sincronizado com as decisões reais.
- Garantir que o `README.md` suba todo o projeto localmente em **no máximo 5 comandos**.

## Padrões Técnicos e Boas Práticas
- Registrar métricas comparativas reais (offline vs. ao vivo) antes de concluir qualquer entrega de ML.
- Testar comandos de setup em ambiente limpo sempre que alterar dependências ou `docker-compose.yml`.

## O que NÃO fazer
- **NÃO** considerar uma funcionalidade pronta sem validar os critérios de aceite da SPEC correspondente.
- **NÃO** inflar `decisoes.md` com logs extensos ou código-fonte colado.
- **NÃO** relaxar asserções de testes para mascarar falhas de "Não sei" ou de integração com o PostgreSQL.
