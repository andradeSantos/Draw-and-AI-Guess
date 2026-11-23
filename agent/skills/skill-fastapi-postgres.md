# Skill — Backend FastAPI e PostgreSQL (`skill-fastapi-postgres`)

## Quando usar
Ao estruturar a API REST, configurar a conexão com o PostgreSQL, modelar tabelas/schemas ou integrar o serviço de inferência.

## Responsabilidades
- Carregar o modelo PyTorch e os metadados **uma única vez** no ciclo de vida (*lifespan*) da aplicação FastAPI.
- Validar rigorosamente entradas e saídas com Pydantic v2.
- Persistir predições e feedbacks no PostgreSQL local usando SQLAlchemy/SQLModel com sessões gerenciadas.
- Separar responsabilidades em camadas claras: `routers/`, `services/`, `ml_service/`, `repositories/` e `core/`.
- Configurar CORS para permitir requisições do frontend Next.js local.

## Padrões Técnicos e Boas Práticas
- Ler `DATABASE_URL` e limiares de configuração via variáveis de ambiente (`.env`), nunca *hardcoded*.
- Retornar erros HTTP semânticos (`400` para imagem inválida/canvas vazio, `404` para `prediction_id` inexistente, `503` se modelo/banco estiverem indisponíveis).
- Usar agregações SQL limpas para gerar estatísticas em `GET /api/stats`.

## O que NÃO fazer
- **NÃO** recarregar o arquivo `.pt` do disco a cada requisição `/api/predict`.
- **NÃO** versionar senhas, tokens ou strings de conexão reais no código.
- **NÃO** armazenar dados pessoais de visitantes ou imagens sensíveis.
