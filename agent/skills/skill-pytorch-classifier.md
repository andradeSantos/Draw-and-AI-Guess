# Skill — Classificador PyTorch Local (`skill-pytorch-classifier`)

## Quando usar
Ao definir a arquitetura da CNN, escrever o loop de treinamento, avaliar métricas ou calibrar a regra de incerteza ("Não sei").

## Responsabilidades
- Construir uma CNN leve e explicável em PyTorch (2 a 3 blocos convolucionais + classificador linear para as 18 classes).
- Garantir execução 100% em CPU tanto no treino quanto na inferência (`torch.inference_mode()`).
- Fixar *random seeds* (`torch`, `numpy`, `random`) para reprodutibilidade.
- Calibrar os limiares da regra **"Não sei"** ($\max(P) < \tau_1$ ou $P_1 - P_2 < \tau_2$) usando o conjunto de validação e amostras de rabisco.
- Exportar artefatos versionados: pesos `.pt` e metadados `.json` (lista de classes, versão, normalização e limiares).

## Padrões Técnicos e Boas Práticas
- Gerar ao final de todo treino: acurácia em treino/validação/teste, matriz de confusão e taxa de rejeição de rabiscos.
- Usar *early stopping* ou seleção do melhor checkpoint baseado no conjunto de validação (nunca no de teste).
- Manter código claro e didático para explicação ao vivo.

## O que NÃO fazer
- **NÃO** usar modelos pré-treinados prontos (ex.: ResNet/MobileNet com pesos ImageNet) nem APIs externas de IA.
- **NÃO** exigir GPU para rodar a inferência.
- **NÃO** treinar ou avaliar com vazamento de dados entre treino, validação e teste.
