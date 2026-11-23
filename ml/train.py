"""Treinamento local (CPU), calibração do 'Não sei' e avaliação do modelo CNN (SPEC 03)."""

from __future__ import annotations

import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

from ml.classes import CLASSES, INDEX_TO_LABEL, NUM_CLASSES
from ml.dataset import DrawingTensorDataset, prepare_dataset
from ml.model import DrawGuessCNN

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"


def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


@torch.inference_mode()
def _collect_probs(model: DrawGuessCNN, x: np.ndarray, batch_size: int = 256) -> np.ndarray:
    model.eval()
    probs_list = []
    tensor_x = torch.from_numpy(x).unsqueeze(1).float()
    for i in range(0, len(tensor_x), batch_size):
        logits = model(tensor_x[i : i + batch_size])
        probs_list.append(torch.softmax(logits, dim=1).numpy())
    return np.concatenate(probs_list, axis=0)


def calibrate_uncertainty_thresholds(
    val_probs: np.ndarray,
    val_labels: np.ndarray,
    noise_probs: np.ndarray,
) -> tuple[float, float]:
    """Calibra (tau1, tau2) equilibrando rejeição de rabiscos e cobertura de desenhos válidos."""
    val_sorted = np.sort(val_probs, axis=1)
    val_p1 = val_sorted[:, -1]
    val_margin = val_sorted[:, -1] - val_sorted[:, -2]
    val_correct = val_probs.argmax(axis=1) == val_labels

    noise_sorted = np.sort(noise_probs, axis=1)
    noise_p1 = noise_sorted[:, -1]
    noise_margin = noise_sorted[:, -1] - noise_sorted[:, -2]

    best_score = -1.0
    best_pair = (0.55, 0.15)

    for tau1 in np.round(np.arange(0.40, 0.76, 0.05), 2):
        for tau2 in np.round(np.arange(0.10, 0.31, 0.05), 2):
            accepted_val = (val_p1 >= tau1) & (val_margin >= tau2)
            val_coverage = float(accepted_val.mean())
            if val_coverage < 0.70:
                continue
            accepted_acc = float(val_correct[accepted_val].mean()) if accepted_val.any() else 0.0
            noise_rejected = float(((noise_p1 < tau1) | (noise_margin < tau2)).mean())

            # Pontuação priorizando alta rejeição de rabiscos sem sacrificar cobertura/acurácia
            score = 0.50 * noise_rejected + 0.30 * accepted_acc + 0.20 * val_coverage
            if score > best_score:
                best_score = score
                best_pair = (float(tau1), float(tau2))

    return best_pair


def compute_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
    cm = np.zeros((NUM_CLASSES, NUM_CLASSES), dtype=int)
    for t, p in zip(y_true, y_pred):
        cm[int(t), int(p)] += 1
    return cm


def top_confused_pairs(cm: np.ndarray, top_n: int = 5) -> list[dict[str, object]]:
    pairs = []
    for i in range(NUM_CLASSES):
        for j in range(NUM_CLASSES):
            if i != j and cm[i, j] > 0:
                pairs.append(
                    {
                        "true_class": INDEX_TO_LABEL[i],
                        "predicted_class": INDEX_TO_LABEL[j],
                        "count": int(cm[i, j]),
                    }
                )
    pairs.sort(key=lambda item: int(item["count"]), reverse=True)
    return pairs[:top_n]


def train_and_evaluate(
    epochs: int = 12,
    batch_size: int = 128,
    lr: float = 1e-3,
    samples_per_class: int = 2000,
    seed: int = 42,
) -> dict[str, object]:
    set_seed(seed)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    splits, noise_eval = prepare_dataset(samples_per_class=samples_per_class, seed=seed)
    x_train, y_train = splits["train"]
    x_val, y_val = splits["val"]
    x_test, y_test = splits["test"]

    train_loader = DataLoader(
        DrawingTensorDataset(x_train, y_train, augment=True),
        batch_size=batch_size,
        shuffle=True,
    )
    val_loader = DataLoader(
        DrawingTensorDataset(x_val, y_val, augment=False),
        batch_size=256,
        shuffle=False,
    )

    model = DrawGuessCNN(num_classes=NUM_CLASSES)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.05)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_acc = -1.0
    best_state: dict[str, torch.Tensor] | None = None

    print(f"[train] Iniciando treino em CPU ({len(x_train)} treino, {len(x_val)} val, {len(x_test)} teste)...")
    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        for bx, by in train_loader:
            optimizer.zero_grad()
            logits = model(bx)
            loss = criterion(logits, by)
            loss.backward()
            optimizer.step()
            running_loss += float(loss.item()) * len(bx)
        scheduler.step()

        model.eval()
        correct = 0
        total = 0
        with torch.inference_mode():
            for bx, by in val_loader:
                preds = model(bx).argmax(dim=1)
                correct += int((preds == by).sum().item())
                total += len(by)
        val_acc = correct / total
        avg_loss = running_loss / len(x_train)
        print(f"[train] Epoch {epoch:02d}/{epochs} | loss={avg_loss:.4f} | val_acc={val_acc:.4f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    assert best_state is not None
    model.load_state_dict(best_state)
    model.eval()

    # Calibração de limiares usando validação + rabiscos
    val_probs = _collect_probs(model, x_val)
    noise_probs = _collect_probs(model, noise_eval)
    tau1, tau2 = calibrate_uncertainty_thresholds(val_probs, y_val, noise_probs)

    # Avaliação final imparcial no conjunto de teste
    test_probs = _collect_probs(model, x_test)
    test_preds = test_probs.argmax(axis=1)
    test_acc = float((test_preds == y_test).mean())

    test_sorted = np.sort(test_probs, axis=1)
    test_accepted = (test_sorted[:, -1] >= tau1) & ((test_sorted[:, -1] - test_sorted[:, -2]) >= tau2)
    test_acc_accepted = float((test_preds[test_accepted] == y_test[test_accepted]).mean()) if test_accepted.any() else 0.0
    test_coverage = float(test_accepted.mean())

    noise_sorted = np.sort(noise_probs, axis=1)
    noise_rejection_rate = float(((noise_sorted[:, -1] < tau1) | ((noise_sorted[:, -1] - noise_sorted[:, -2]) < tau2)).mean())

    # Latência média em CPU (1 imagem por vez)
    sample_tensor = torch.from_numpy(x_test[:1]).unsqueeze(1).float()
    t0 = time.perf_counter()
    with torch.inference_mode():
        for _ in range(50):
            _ = model(sample_tensor)
    avg_latency_ms = ((time.perf_counter() - t0) / 50.0) * 1000.0

    cm = compute_confusion_matrix(y_test, test_preds)
    confused = top_confused_pairs(cm, top_n=5)

    weights_path = ARTIFACTS_DIR / "draw_cnn.pt"
    torch.save(best_state, weights_path)

    model_version = "cnn-v1.0.0"
    metadata = {
        "model_version": model_version,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "num_classes": NUM_CLASSES,
        "classes": [{"index": c.index, "label": c.label, "display_pt": c.display_pt} for c in CLASSES],
        "confidence_threshold": tau1,
        "margin_threshold": tau2,
        "metrics": {
            "best_val_accuracy": round(best_val_acc, 4),
            "test_accuracy": round(test_acc, 4),
            "test_accuracy_when_confident": round(test_acc_accepted, 4),
            "test_confident_coverage": round(test_coverage, 4),
            "noise_rejection_rate": round(noise_rejection_rate, 4),
            "cpu_inference_latency_ms": round(avg_latency_ms, 2),
        },
    }
    with (ARTIFACTS_DIR / "metadata.json").open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    report = {
        **metadata,
        "top_confused_pairs": confused,
        "confusion_matrix": cm.tolist(),
    }
    with (ARTIFACTS_DIR / "evaluation_report.json").open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(
        f"[eval] test_acc={test_acc:.4f} | confident_acc={test_acc_accepted:.4f} "
        f"(cov={test_coverage:.4f}) | noise_rejection={noise_rejection_rate:.4f} "
        f"| tau1={tau1}, tau2={tau2} | cpu_latency={avg_latency_ms:.2f}ms"
    )
    return report


if __name__ == "__main__":
    train_and_evaluate()
