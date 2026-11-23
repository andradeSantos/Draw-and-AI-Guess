# Skill — Pré-processamento de Imagem (`skill-image-preprocessing`)

## Quando usar
Sempre que criar, alterar ou testar a transformação de imagens no treino (`/ml`) ou na inferência (`/backend`).

## Responsabilidades
- Garantir **paridade total entre treino e inferência** (zero *Train-Serve Skew*): o backend deve importar e executar exatamente a mesma função de pré-processamento usada no treinamento em `/ml`.
- Tratar corretamente imagens vindas do Canvas HTML5 (fundo transparente RGBA ou branco) convertendo para a mesma polaridade do dataset de treino (traço claro em fundo escuro ou vice-versa, de forma única e documentada).
- Detectar e rejeitar canvas vazio (sem traços relevantes) antes de acionar a CNN.
- Aplicar recorte por *bounding box* do desenho com margem (*padding*), preservando a proporção antes de redimensionar para o tamanho de entrada do modelo (ex.: `28x28`).

## Padrões Técnicos e Boas Práticas
- Usar Pillow (`PIL.Image`) e `numpy` com operações determinísticas.
- Validar tipos de entrada, dimensões e faixa de valores do tensor resultante.
- Manter o módulo puro (sem dependência de FastAPI ou banco de dados) para ser importável tanto por `/ml` quanto por `/backend`.

## O que NÃO fazer
- **NÃO** duplicar código de pré-processamento entre `/ml` e `/backend`.
- **NÃO** aplicar *data augmentation* aleatória (rotação, ruído, distorção) no pipeline de inferência.
- **NÃO** enviar imagens para APIs externas ou serviços em nuvem.
