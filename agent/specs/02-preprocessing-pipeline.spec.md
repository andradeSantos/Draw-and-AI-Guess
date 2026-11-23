# SPEC 02 — Pipeline de Pré-Processamento de Imagens

> **Status:** Aprovada (Fase 2)  
> **Skill vinculada:** `/agent/skills/skill-image-preprocessing.md`  
> **Módulos afetados:** `/ml/preprocessing.py` (importado futuramente por `/backend`)

---

## 1. Objetivo
Definir um pipeline **único, determinístico e puro** de pré-processamento de imagens para eliminar *Train-Serve Skew* entre o treinamento em `/ml` e a inferência ao vivo no `/backend` (FastAPI).

---

## 2. Contrato de Entrada e Saída

### Entradas Suportadas
- `str`: imagem codificada em PNG/JPEG **Base64** (com ou sem prefixo `data:image/png;base64,...`), vinda do Canvas HTML5.
- `bytes`: bytes brutos de imagem PNG/JPEG.
- `PIL.Image.Image`: imagem Pillow (RGB, RGBA ou L).
- `np.ndarray`: matriz 2D `(H, W)` ou 3D `(H, W, C)` em `uint8` (`0–255`) ou `float32` (`0.0–1.0`).

### Saída Padronizada
Objeto estruturado (`PreprocessResult`) contendo:
- `is_empty: bool` — `True` se o canvas estiver em branco ou sem traços relevantes.
- `tensor: torch.Tensor | None` — tensor `float32` de formato `(1, 28, 28)` quando válido (ou `None` se `is_empty=True`).
- `array_28x28: np.ndarray | None` — matriz `float32` `(28, 28)` no intervalo `[0.0, 1.0]` (traço claro em fundo preto `0.0`).
- `reason: str | None` — motivo quando `is_empty=True` (ex.: `"blank_canvas"`).

---

## 3. Regras de Transformação (Ordem Obrigatória)
1. **Normalização de Canal e Fundo (Canvas HTML5):**
   - Se a imagem for `RGBA`, compor sobre fundo **branco** (`255, 255, 255`) antes de converter para escala de cinza (`L`).
   - Detectar automaticamente a polaridade: se a média da borda (ou mediana global) for clara (`> 127`), inverter (`255 - img`) para que o **fundo seja sempre escuro (`0`) e o traço claro (`> 0`)**, igual ao padrão MNIST / Quick, Draw!.
2. **Remoção de Ruído de Fundo e Detecção de Canvas Vazio:**
   - Zerar pixels abaixo de um limiar mínimo de tinta (`ink_threshold = 20` em `0–255`).
   - Se a soma de pixels ativos ou o valor máximo for insuficiente (`active_pixels < 8`), retornar `is_empty=True` sem acionar o modelo.
3. **Recorte por *Bounding Box*:**
   - Calcular o retângulo mínimo `(x_min, y_min, x_max, y_max)` que envolve os pixels ativos.
4. **Centralização pelo Centro de Massa com *Aspect Ratio* e *Padding*:**
   - Redimensionar o recorte preservando a proporção (*aspect ratio*) para caber em uma caixa de `20x20` dentro de um quadro `28x28` (deixando margem mínima de `4px` de respiro).
   - Posicionar a imagem no quadro `28x28` alinhando o **centro de massa** dos pixels de tinta ao centro `(14, 14)` (com *clamping* para não cortar bordas).
5. **Suavização Leve e Normalização Final:**
   - Aplicar filtro gaussiano leve (`radius = 0.45`) para uniformizar serrilhados e diferenças de espessura de traço.
   - Re-normalizar para `[0.0, 1.0]` (`float32`) e converter para `torch.Tensor` `(1, 28, 28)`.

---

## 4. Critérios de Aceite
- [ ] Mesmo módulo importável por `/ml` e `/backend` sem dependência de FastAPI ou banco de dados.
- [ ] Canvas totalmente branco ou transparente retorna `is_empty=True` sem exceção.
- [ ] Traços desenhados nos cantos do canvas são recortados e centralizados no quadro `28x28`.
- [ ] Saída determinística com formato `(1, 28, 28)` e valores em `[0.0, 1.0]`.
