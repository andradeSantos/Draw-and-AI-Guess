# Relato de Uso de IA no Desenvolvimento (`relato-ia.md`)

O projeto foi conduzido no fluxo **IA-First**: antes de escrever código, definimos as especificações técnicas (`/agent/specs/`) e regras operacionais (`/agent/skills/`) para orientar os agentes de código com contratos claros.

### Onde a IA ajudou de forma decisiva
- **Estruturação e contratos:** A IA acelerou a criação das especificações modulares, garantindo alinhamento entre o esquema do PostgreSQL (`predictions` e `feedbacks`), os endpoints do FastAPI e os estados de UI do Next.js.
- **Boilerplate e integração:** Geração rápida e consistente de modelos SQLAlchemy, schemas Pydantic v2, componentes React com `PointerEvent` no Canvas HTML5 e consultas SQL agregadas para o Dashboard e o Simulador de Chat offline.
- **Qualidade e testes:** Criação da suíte `pytest` cobrindo pré-processamento, inferência, rejeição de rabiscos (`"Não sei"`) e fluxo completo de API com PostgreSQL, reduzindo regressões entre fases.

### Onde a IA falhou ou exigiu correção humana (exemplos reais)
- **Fonte de dados indisponível (`heart.npy`):** Ao preparar o dataset do Quick, Draw!, a URL esperada para a classe `heart` retornou **HTTP 404**. Foi necessária intervenção para substituir o download quebrado por um gerador paramétrico local de traço manual em `ml/dataset.py`, mantendo o balanceamento das 18 classes sem depender de rede.
- **Risco de duplicação de pré-processamento:** Sem revisão explícita das specs, agentes tendem a reescrever normalizações de imagem dentro da API FastAPI. Exigimos que `/backend` importasse diretamente `ml/inference.py` e `ml/preprocessing.py` para eliminar *train-serve skew*.
- **Vigilância sobre escopo e regras:** Na definição inicial da arquitetura, foi necessário barrar sugestões comuns de LLMs — como uso de modelos pré-treinados prontos, RAG ou chamadas a APIs externas para o chat — garantindo conformidade estrita com execução 100% local em CPU e setup em até 5 comandos.
