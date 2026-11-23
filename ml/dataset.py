"""Preparação do dataset (MNIST + Quick, Draw! + rabiscos) e Data Augmentation (SPEC 01 & 03)."""

from __future__ import annotations

import urllib.request
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageDraw
from torch.utils.data import Dataset
from torchvision import datasets
from torchvision.transforms import v2

from ml.classes import CLASSES, SYMBOL_CLASSES
from ml.preprocessing import preprocess_image

DATA_DIR = Path(__file__).resolve().parent / "data"
RAW_DIR = DATA_DIR / "raw"
QUICKDRAW_DIR = RAW_DIR / "quickdraw"
PROCESSED_DIR = DATA_DIR / "processed"
SPLITS_PATH = PROCESSED_DIR / "dataset_splits.npz"
NOISE_PATH = PROCESSED_DIR / "noise_eval.npy"

QUICKDRAW_BASE_URL = "https://storage.googleapis.com/quickdraw_dataset/full/numpy_bitmap"


def _download_quickdraw_category(category: str, dest_path: Path) -> None:
    if dest_path.exists():
        return
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    url = f"{QUICKDRAW_BASE_URL}/{category.replace(' ', '%20')}.npy"
    print(f"[dataset] Baixando Quick, Draw! '{category}' de {url}...")
    tmp_path = dest_path.with_suffix(".tmp")
    urllib.request.urlretrieve(url, tmp_path)
    tmp_path.rename(dest_path)


def _generate_heart_samples(n_samples: int, rng: np.random.Generator) -> np.ndarray:
    """Gera amostras variadas de coração estilo desenho à mão (Quick, Draw! não possui heart.npy)."""
    samples = np.empty((n_samples, 28, 28), dtype=np.uint8)
    t = np.linspace(0, 2 * np.pi, 64)
    base_x = 16 * (np.sin(t) ** 3)
    base_y = -(13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t))

    for i in range(n_samples):
        canvas = Image.new("L", (112, 112), 0)
        draw = ImageDraw.Draw(canvas)

        scale_x = float(rng.uniform(1.8, 2.7))
        scale_y = float(rng.uniform(1.8, 2.7))
        angle = float(rng.uniform(-0.26, 0.26))
        cx = 56.0 + float(rng.uniform(-6.0, 6.0))
        cy = 56.0 + float(rng.uniform(-6.0, 6.0))

        # Ruído suave ao longo do contorno para simular traço humano
        jitter_x = rng.normal(0.0, 0.8, size=len(t))
        jitter_y = rng.normal(0.0, 0.8, size=len(t))

        cos_a, sin_a = np.cos(angle), np.sin(angle)
        xs = base_x * scale_x + jitter_x
        ys = base_y * scale_y + jitter_y
        rx = cx + (xs * cos_a - ys * sin_a)
        ry = cy + (xs * sin_a + ys * cos_a)

        pts = [(float(x), float(y)) for x, y in zip(rx, ry)]
        pts.append(pts[0])
        draw.line(pts, fill=255, width=int(rng.integers(4, 9)))

        resized = canvas.resize((28, 28), resample=Image.Resampling.BILINEAR)
        samples[i] = np.asarray(resized, dtype=np.uint8)

    return samples


def _preprocess_batch(images_uint8: np.ndarray) -> np.ndarray:
    """Passa todas as amostras pelo mesmo preprocess_image() para zero Train-Serve Skew."""
    processed = np.empty((len(images_uint8), 28, 28), dtype=np.float32)
    kept = 0
    for img in images_uint8:
        res = preprocess_image(img)
        if not res.is_empty and res.array_28x28 is not None:
            processed[kept] = res.array_28x28
            kept += 1
    return processed[:kept]


def generate_scribble_samples(n_samples: int = 300, seed: int = 42) -> np.ndarray:
    """Gera bateria sintética de rabiscos, pontos esparsos e borrões para validar 'Não sei'."""
    rng = np.random.default_rng(seed)
    samples = np.empty((n_samples, 28, 28), dtype=np.float32)

    for i in range(n_samples):
        canvas = Image.new("L", (140, 140), 255)
        draw = ImageDraw.Draw(canvas)
        kind = i % 3

        if kind == 0:
            # Rabisco caótico com múltiplos segmentos cruzados
            pts = [(int(rng.integers(5, 135)), int(rng.integers(5, 135))) for _ in range(int(rng.integers(10, 22)))]
            draw.line(pts, fill=0, width=int(rng.integers(3, 8)))
        elif kind == 1:
            # Pontos esparsos e pequenos riscos desconexos
            for _ in range(int(rng.integers(8, 20))):
                x0, y0 = int(rng.integers(10, 130)), int(rng.integers(10, 130))
                x1 = int(np.clip(x0 + rng.integers(-12, 13), 0, 139))
                y1 = int(np.clip(y0 + rng.integers(-12, 13), 0, 139))
                draw.line([(x0, y0), (x1, y1)], fill=0, width=int(rng.integers(2, 6)))
        else:
            # Ruído denso / borrão irregular
            arr_noise = np.full((140, 140), 255, dtype=np.uint8)
            mask = rng.random((140, 140)) > 0.72
            arr_noise[mask] = rng.integers(0, 90, size=int(mask.sum()), dtype=np.uint8)
            canvas = Image.fromarray(arr_noise, mode="L")

        res = preprocess_image(canvas)
        if not res.is_empty and res.array_28x28 is not None:
            samples[i] = res.array_28x28
        else:
            samples[i] = np.zeros((28, 28), dtype=np.float32)

    return samples


def prepare_dataset(
    samples_per_class: int = 2000,
    seed: int = 42,
    force: bool = False,
) -> tuple[dict[str, tuple[np.ndarray, np.ndarray]], np.ndarray]:
    """Prepara e salva splits estratificados (70% / 15% / 15%) e bateria de rabiscos."""
    if SPLITS_PATH.exists() and NOISE_PATH.exists() and not force:
        data = np.load(SPLITS_PATH)
        noise = np.load(NOISE_PATH)
        splits = {
            "train": (data["x_train"], data["y_train"]),
            "val": (data["x_val"], data["y_val"]),
            "test": (data["x_test"], data["y_test"]),
        }
        return splits, noise

    rng = np.random.default_rng(seed)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Carrega MNIST (dígitos 0-9)
    mnist_train = datasets.MNIST(root=str(RAW_DIR), train=True, download=True)
    mnist_imgs = mnist_train.data.numpy()  # (60000, 28, 28) uint8
    mnist_targets = mnist_train.targets.numpy()

    x_train_list, y_train_list = [], []
    x_val_list, y_val_list = [], []
    x_test_list, y_test_list = [], []

    for class_spec in CLASSES:
        if class_spec.category == "digit":
            idx = np.where(mnist_targets == class_spec.index)[0]
            chosen = rng.choice(idx, size=min(samples_per_class + 150, len(idx)), replace=False)
            raw_samples = mnist_imgs[chosen]
        elif class_spec.label == "heart":
            raw_samples = _generate_heart_samples(samples_per_class + 150, rng)
        else:
            assert class_spec.quickdraw_name is not None
            qd_path = QUICKDRAW_DIR / f"{class_spec.quickdraw_name}.npy"
            _download_quickdraw_category(class_spec.quickdraw_name, qd_path)
            qd_all = np.load(qd_path, mmap_mode="r")
            chosen = rng.choice(len(qd_all), size=min(samples_per_class + 150, len(qd_all)), replace=False)
            raw_samples = np.array(qd_all[chosen], dtype=np.uint8).reshape(-1, 28, 28)

        proc = _preprocess_batch(raw_samples)[:samples_per_class]
        n = len(proc)
        perm = rng.permutation(n)
        proc = proc[perm]

        n_train = int(0.70 * n)
        n_val = int(0.15 * n)

        x_train_list.append(proc[:n_train])
        y_train_list.append(np.full(n_train, class_spec.index, dtype=np.int64))

        x_val_list.append(proc[n_train : n_train + n_val])
        y_val_list.append(np.full(n_val, class_spec.index, dtype=np.int64))

        n_test = n - n_train - n_val
        x_test_list.append(proc[n_train + n_val :])
        y_test_list.append(np.full(n_test, class_spec.index, dtype=np.int64))

        print(f"[dataset] Classe {class_spec.index:02d} ({class_spec.label}): {n_train} train / {n_val} val / {n_test} test")

    def _concat_shuffle(xs: list[np.ndarray], ys: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
        x = np.concatenate(xs, axis=0)
        y = np.concatenate(ys, axis=0)
        p = rng.permutation(len(x))
        return x[p], y[p]

    x_train, y_train = _concat_shuffle(x_train_list, y_train_list)
    x_val, y_val = _concat_shuffle(x_val_list, y_val_list)
    x_test, y_test = _concat_shuffle(x_test_list, y_test_list)

    np.savez_compressed(
        SPLITS_PATH,
        x_train=x_train,
        y_train=y_train,
        x_val=x_val,
        y_val=y_val,
        x_test=x_test,
        y_test=y_test,
    )

    noise = generate_scribble_samples(n_samples=300, seed=seed)
    np.save(NOISE_PATH, noise)

    splits = {
        "train": (x_train, y_train),
        "val": (x_val, y_val),
        "test": (x_test, y_test),
    }
    return splits, noise


class DrawingTensorDataset(Dataset):
    """Dataset PyTorch com Data Augmentation opcional para simular desenhos ao vivo."""

    def __init__(self, x: np.ndarray, y: np.ndarray, augment: bool = False) -> None:
        self.x = torch.from_numpy(x).unsqueeze(1).float()  # (N, 1, 28, 28)
        self.y = torch.from_numpy(y).long()
        self.augment = augment
        self.affine = v2.RandomAffine(
            degrees=12.0,
            translate=(0.10, 0.10),
            scale=(0.88, 1.12),
        )

    def __len__(self) -> int:
        return len(self.x)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        img = self.x[idx]
        if self.augment:
            img = self.affine(img)
            # Variação leve de espessura de traço em 25% das amostras
            r = float(torch.rand(1).item())
            if r < 0.25:
                img = torch.nn.functional.max_pool2d(img.unsqueeze(0), kernel_size=3, stride=1, padding=1).squeeze(0)
        return img, self.y[idx]
