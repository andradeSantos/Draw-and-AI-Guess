# SPEC 01 — Domínio, Classes e Estratégia de Dataset

> **Status:** Aprovada (Fase 1)  
> **Módulos afetados:** `/ml`, `/backend`, `/frontend`

---

## 1. Objetivo
Definir o conjunto fechado de classes que o modelo PyTorch deve reconhecer, a origem dos dados de treinamento/validação/teste, a estratégia de coleta de desenhos próprios no Canvas e o tratamento de amostras de ruído/rabisco para suportar o estado **"Não sei"**.

---

## 2. Lista Exata de Classes (18 Classes Válidas)

O modelo classificará desenhos em **18 classes válidas** (índices `0` a `17`), combinando dígitos e símbolos simples:

| Índice | ID Técnico (`label`) | Nome de Exibição (PT-BR) | Categoria | Origem Principal |
| :--- | :--- | :--- | :--- | :--- |
| `0`–`9` | `digit_0` .. `digit_9` | `0` .. `9` | Dígitos (10) | MNIST + desenhos próprios |
| `10` | `star` | `Estrela` | Símbolo (1) | Quick, Draw! + desenhos próprios |
| `11` | `house` | `Casa` | Símbolo (2) | Quick, Draw! + desenhos próprios |
| `12` | `circle` | `Círculo` | Símbolo (3) | Quick, Draw! + desenhos próprios |
| `13` | `triangle` | `Triângulo` | Símbolo (4) | Quick, Draw! + desenhos próprios |
| `14` | `square` | `Quadrado` | Símbolo (5) | Quick, Draw! + desenhos próprios |
| `15` | `heart` | `Coração` | Símbolo (6) | Gerador paramétrico local (traço manual) + desenhos próprios |
| `16` | `cloud` | `Nuvem` | Símbolo (7) | Quick, Draw! + desenhos próprios |
| `17` | `tree` | `Árvore` | Símbolo (8) | Quick, Draw! + desenhos próprios |

> **Nota sobre "Não sei" (`unknown`):** "Não sei" **não** é tratado apenas como um chute qualquer — ele é acionado pela regra de incerteza (confiança/margem na SPEC 02) **e** validado com uma bateria dedicada de amostras de ruído/rabisco fora das 18 classes.

---

## 3. Estratégia de Dados

### 3.1 Fontes de Dados
1. **Dígitos (`0–9`):** Dataset público **MNIST** (via `torchvision.datasets.MNIST` ou arquivo local em `/ml/data/raw/`), com subamostragem balanceada por classe para equiparar a quantidade de exemplos por classe aos símbolos.
2. **8 Símbolos Simples:** Subconjunto público do **Quick, Draw!** (arquivos `.npy` em formato `28x28` ou *bitmap* equivalente baixados localmente para `/ml/data/raw/quickdraw/`), com quantidade balanceada por classe (ex.: 2.000 a 5.000 amostras por classe).
3. **Amostras Próprias do Canvas (Anti-*Data Drift*):** Coleta controlada de desenhos feitos diretamente no Canvas da aplicação (ou script auxiliar local) para cada uma das 18 classes, incorporada ao conjunto de treino/validação e usada em um conjunto separado de avaliação ao vivo.
4. **Amostras de Ruído e Rabiscos (Rejeição / "Não sei"):**
   - Geração sintética controlada (linhas aleatórias cruzadas, pontos esparsos, borrões, traços incompletos) + rabiscos coletados manualmente.
   - Mantidas em conjunto separado (`/ml/data/noise/`) para calibrar os limiares $\tau_1$ e $\tau_2$ da SPEC 02 e compor a suíte de testes de rejeição. *(Opcionalmente, pode-se avaliar na Fase 2 se uma classe auxiliar `noise` ajuda ou se apenas entropia/limiares são suficientes.)*

### 3.2 Padronização de Formato
- Todas as amostras devem passar exatamente pelo mesmo pipeline de pré-processamento antes de entrar na rede (`28x28` ou `32x32` em escala de cinza, fundo preto e traço branco — ou convenção única documentada na SPEC 02 — normalizados em `[0, 1]` ou média/desvio padrão fixos).

---

## 4. Divisão Treino / Validação / Teste

Divisão **estratificada por classe** com *random seed* fixa (ex.: `seed=42`) e **zero vazamento** entre os conjuntos:

| Conjunto | Proporção | Finalidade |
| :--- | :--- | :--- |
| **Treino (`train`)** | **70%** | Ajuste de pesos da CNN |
| **Validação (`val`)** | **15%** | Escolha de hiperparâmetros, *early stopping* e calibração dos limiares do "Não sei" |
| **Teste Offline (`test`)** | **15%** | Medição final imparcial de acurácia e matriz de confusão (nunca visto no treino) |
| **Teste Ao Vivo (`live_canvas`)** | Conjunto dedicado | Medição de *data drift* com desenhos reais do Canvas |
| **Bateria de Rabiscos (`noise_eval`)** | Conjunto dedicado | Validação da taxa de rejeição ("Não sei") |

---

## 5. Critérios de Aceite da SPEC 01
- [ ] Lista fechada de 18 classes (`0–9` + 8 símbolos) documentada e mapeada em arquivo de configuração/metadados único.
- [ ] Script de preparação de dados reproduzível (`seed` fixa) gerando divisão estratificada `70% / 15% / 15%` sem vazamento de amostras.
- [ ] Balanceamento verificado entre as 18 classes no conjunto de treino.
- [ ] Presença de conjunto separado de rabiscos/ruídos para validação do comportamento "Não sei".
- [ ] Nenhum dado pessoal ou imagem externa enviada para fora do ambiente local.
