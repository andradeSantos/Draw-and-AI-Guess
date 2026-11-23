# SPEC 03 — Modelo CNN Próprio em PyTorch e Política de Incerteza ("Não sei")

> **Status:** Aprovada (Fase 2)  
> **Skill vinculada:** `/agent/skills/skill-pytorch-classifier.md`  
> **Módulos afetados:** `/ml/dataset.py`, `/ml/model.py`, `/ml/train.py`, `/ml/inference.py`

---

## 1. Objetivo
Especificar a arquitetura da CNN própria treinada do zero em PyTorch (CPU), a estratégia de *data augmentation* para reduzir *data drift* em desenhos ao vivo, os critérios de avaliação e a política matemática de rejeição **"Não sei"**.

---

## 2. Arquitetura da CNN (`DrawGuessCNN`)
Rede convolucional leve e explicável para entradas `(N, 1, 28, 28)` e **18 classes**:
- **Bloco 1:** `Conv2d(1 -> 32, kernel=3, padding=1)` + `BatchNorm2d(32)` + `ReLU` + `MaxPool2d(2)` -> `(32, 14, 14)`
- **Bloco 2:** `Conv2d(32 -> 64, kernel=3, padding=1)` + `BatchNorm2d(64)` + `ReLU` + `MaxPool2d(2)` -> `(64, 7, 7)`
- **Bloco 3:** `Conv2d(64 -> 128, kernel=3, padding=1)` + `BatchNorm2d(128)` + `ReLU` + `AdaptiveAvgPool2d(4, 4)` -> `(128, 4, 4)`
- **Classificador:** `Flatten` -> `Dropout(0.25)` -> `Linear(2048 -> 128)` + `ReLU` + `Dropout(0.20)` -> `Linear(128 -> 18)`

**Restrição:** Execução e inferência **100% em CPU** (`torch.inference_mode()`), tempo de inferência alvo `< 50 ms` por imagem.

---

## 3. Data Augmentation (Anti-*Data Drift* Ao Vivo)
Aplicada **exclusivamente no conjunto de treino** para simular variações reais de visitantes no Canvas:
- Pequenas rotações (`±12°`)
- Pequenas translações (`±10%`) e escala (`0.88x – 1.12x`)
- Variação leve de espessura de traço (dilatação/erosão morfológica leve aleatória)

---

## 4. Política de Incerteza ("Não sei")
A função `predict(image_input)` aplica Softmax sobre os logits `P = softmax(logits)` e retorna **"Não sei"** (`is_unknown=True`) se **qualquer** uma das condições ocorrer:
1. **Canvas vazio:** `preprocess()` retorna `is_empty=True`.
2. **Baixa confiança:** $\max(P) < \tau_1$ (`confidence_threshold`, calibrado na validação).
3. **Baixa margem (ambiguidade entre top-1 e top-2):** $P_1 - P_2 < \tau_2$ (`margin_threshold`, calibrado na validação).

*(Os valores calibrados de $\tau_1$ e $\tau_2$ são gravados em `/ml/artifacts/metadata.json` ao final do treino.)*

---

## 5. Artefatos e Critérios de Aceite
- **Artefatos salvos em `/ml/artifacts/`:**
  - `draw_cnn.pt` (pesos do melhor checkpoint na validação)
  - `metadata.json` (18 classes, versão, $\tau_1$, $\tau_2$, métricas de teste e rejeição)
  - `evaluation_report.json` (acurácia, matriz de confusão `18x18`, pares mais confundidos, taxa de rejeição de rabiscos e latência média em CPU)
- **Critérios de aceite:**
  - [ ] Treino reprodutível com `seed=42` e divisão estratificada `70% / 15% / 15%`.
  - [ ] Inferência em CPU `< 50 ms`.
  - [ ] Rejeição explícita ("Não sei") em bateria de rabiscos aleatórios.
  - [ ] Todos os testes `pytest` aprovados.
