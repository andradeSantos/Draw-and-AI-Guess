# SPEC 02 — Modelo ML (CNN PyTorch) e Regra de Incerteza ("Não sei")

> **Status:** Placeholder estruturado (a detalhar na Fase 2)  
> **Módulos afetados:** `/ml`, `/backend/app/ml_service`

## 1. Objetivo
Especificar o pipeline compartilhado de pré-processamento de imagens, a arquitetura leve da CNN em PyTorch para CPU, o formato de exportação dos pesos e a regra matemática de decisão para **"Não sei"**.

## 2. Escopo Resumido
- **Pré-processamento único (sem *Train-Serve Skew*):** Conversão para escala de cinza, tratamento de fundo branco/transparente do Canvas HTML5, inversão de polaridade consistente, detecção de imagem vazia, recorte por *bounding box* com margem (*padding*), preservação de proporção e redimensionamento para resolução fixa.
- **Arquitetura da CNN:** 2 a 3 blocos convolucionais (`Conv2d` + `BatchNorm` + `ReLU` + `MaxPool2d`) + camadas densas para 18 classes, otimizada para inferência rápida em CPU (`torch.inference_mode()`).
- **Regra do "Não sei":** Filtro pós-Softmax combinando probabilidade máxima ($\max(P) < \tau_1$) e margem entre as duas maiores probabilidades ($P_1 - P_2 < \tau_2$), calibrado no conjunto de validação e bateria de rabiscos.
- **Artefatos:** Pesos `.pt` + arquivo JSON de metadados (mapeamento de classes, versão, limiares $\tau_1, \tau_2$ e parâmetros de normalização).
