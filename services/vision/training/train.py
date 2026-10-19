"""
YOLOv8 training for the CarVal Vision Service
Member 1 - Vision/Damage Detection

Two presets:
  baseline  COCO-pretrained yolov8n, default hyperparameters, no class balancing.
            This is the Review 2 "baseline" number.
  finetune  Same start point, longer schedule, cosine LR and repeat-factor
            sampling for the rare classes (tire, glass, lamp).
Every preset value can be overridden on the command line.

Class imbalance (CarDD train boxes: scratch 2560, dent 1806, crack 651,
lamp 494, glass 475, tire 225) is handled with repeat-factor sampling
(Gupta et al., LVIS 2019): each training image is repeated
r = max over its classes of max(1, sqrt(t / f_c)) times, where f_c is the
fraction of training images containing class c and t defaults to the
frequency of the most common class. r is capped by --rfs-max. Only the
train split is resampled; val and test are untouched, so metrics stay honest.

Usage (from services/vision/):
  python training/train.py --preset baseline --data ~/Documents/BTP/datasets/CarDD_yolo/data.yaml
  python training/train.py --preset finetune --data ~/Documents/BTP/datasets/CarDD_yolo/data.yaml
  # quick smoke test (a few minutes):
  python training/train.py --preset finetune --data ... --epochs 1 --fraction 0.05 --imgsz 320

The best checkpoint is also copied to weights/best.pt (used by the API) with
weights/model_info.json describing where it came from.
"""

import argparse
import json
import math
import random
import shutil
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import yaml

VISION_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VISION_DIR))
from damage_classes import CLASSES  # noqa: E402

WEIGHTS_DIR = VISION_DIR / "weights"
RUNS_DIR = VISION_DIR / "runs"

PRESETS = {
    "baseline": {
        "model": "yolov8n.pt",
        "epochs": 30,
        "balance": "none",
        "patience": 100,
        "cos_lr": False,
    },
    "finetune": {
        "model": "yolov8n.pt",
        "epochs": 80,
        "balance": "rfs",
        "patience": 20,
        "cos_lr": True,
    },
}


def pick_device(requested: str) -> str:
    if requested != "auto":
        return requested
    import torch
    if torch.cuda.is_available():
        return "0"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def resolve_model(model: str) -> str:
    """Bare names like 'yolov8n.pt' are downloaded into weights/ instead of the cwd."""
    p = Path(model).expanduser()
    if p.exists() or p.parent != Path("."):
        return str(p)
    WEIGHTS_DIR.mkdir(exist_ok=True)
    return str(WEIGHTS_DIR / p.name)


def load_data_yaml(path: Path) -> dict:
    with open(path) as f:
        data = yaml.safe_load(f)
    root = Path(data.get("path") or path.parent).expanduser()
    if not root.is_absolute():
        root = (path.parent / root).resolve()
    data["path"] = str(root)
    names = data["names"]
    names = [names[k] for k in sorted(names)] if isinstance(names, dict) else list(names)
    if names != CLASSES:
        sys.exit(f"{path} has classes {names}, expected {CLASSES}. Rebuild with data/prepare_dataset.py.")
    return data


def build_rfs_dataset(data_yaml: Path, rfs_max: float, threshold, seed: int) -> Path:
    """Write train_rfs.txt (oversampled image list) and data_rfs.yaml next to the dataset."""
    data = load_data_yaml(data_yaml)
    root = Path(data["path"])
    img_dir = root / data["train"]
    # images/train -> labels/train (YOLO convention)
    label_dir = root / Path(*["labels" if part == "images" else part for part in Path(data["train"]).parts])
    images = sorted(p for p in img_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"})

    classes_per_image = []
    for img in images:
        lf = label_dir / (img.stem + ".txt")
        ids = set()
        if lf.exists():
            ids = {int(line.split()[0]) for line in lf.read_text().splitlines() if line.strip()}
        classes_per_image.append(ids)

    n = len(images)
    img_freq = Counter(c for ids in classes_per_image for c in ids)
    f = {c: img_freq.get(c, 0) / n for c in range(len(CLASSES))}
    t = threshold if threshold is not None else max(f.values())
    class_r = {c: (min(rfs_max, max(1.0, math.sqrt(t / f[c]))) if f[c] > 0 else 1.0) for c in f}

    rng = random.Random(seed)
    lines, before, after = [], Counter(), Counter()
    for img, ids in zip(images, classes_per_image):
        r = max((class_r[c] for c in ids), default=1.0)
        # stochastic rounding keeps the expected repeat count equal to r
        reps = int(r) + (1 if rng.random() < r - int(r) else 0)
        lines.extend([str(img.resolve())] * reps)
        lf = label_dir / (img.stem + ".txt")
        boxes = Counter(int(l.split()[0]) for l in lf.read_text().splitlines() if l.strip()) if lf.exists() else Counter()
        for c, k in boxes.items():
            before[c] += k
            after[c] += k * reps

    list_file = root / "train_rfs.txt"
    list_file.write_text("\n".join(lines) + "\n")
    rfs_yaml = root / "data_rfs.yaml"
    rfs_data = {k: v for k, v in data.items()}
    rfs_data["train"] = str(list_file)
    rfs_data["names"] = {i: c for i, c in enumerate(CLASSES)}
    with open(rfs_yaml, "w") as fh:
        yaml.safe_dump(rfs_data, fh, sort_keys=False)

    print(f"\nRepeat-factor sampling (t={t:.3f}, cap={rfs_max}): {n} -> {len(lines)} training images per epoch")
    print(f"{'class':<9}{'img freq':>9}{'repeat':>8}{'boxes':>8}{'-> boxes/epoch':>16}")
    for c, name in enumerate(CLASSES):
        print(f"{name:<9}{f[c]:>9.3f}{class_r[c]:>8.2f}{before[c]:>8}{after[c]:>16}")
    print()
    return rfs_yaml


def export_best(run_dir: Path, args, data_yaml: Path):
    best = run_dir / "weights" / "best.pt"
    if not best.exists():
        print(f"! No best.pt in {run_dir}/weights - nothing exported.")
        return
    WEIGHTS_DIR.mkdir(exist_ok=True)
    target = WEIGHTS_DIR / ("best.pt" if args.export_as_default else f"{run_dir.name}.pt")
    shutil.copy2(best, target)

    metrics = {}
    results_csv = run_dir / "results.csv"
    if results_csv.exists():
        import csv
        with open(results_csv) as fh:
            rows = [{k.strip(): v for k, v in r.items()} for r in csv.DictReader(fh)]
        if rows:
            best_row = max(rows, key=lambda r: float(r.get("metrics/mAP50(B)", 0) or 0))
            metrics = {k: float(v) for k, v in best_row.items() if k.startswith("metrics/") or k == "epoch"}

    info = {
        "weights": target.name,
        "run": run_dir.name,
        "preset": args.preset,
        "base_model": Path(args.model).name,
        "data": str(data_yaml),
        "balance": args.balance,
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "classes": CLASSES,
        "best_val_metrics": metrics,
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }
    (target.with_suffix(".json") if not args.export_as_default else WEIGHTS_DIR / "model_info.json").write_text(
        json.dumps(info, indent=2))
    print(f"\n✓ Best weights copied to {target}")


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--preset", choices=sorted(PRESETS), default="finetune")
    p.add_argument("--data", type=Path, required=True, help="data.yaml from prepare_dataset.py")
    p.add_argument("--model", help="Start weights, e.g. yolov8n.pt / yolov8s.pt or a .pt path")
    p.add_argument("--epochs", type=int)
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--batch", type=int, default=16, help="Use 8 for yolov8s on an 8 GB Mac; -1 = auto on CUDA")
    p.add_argument("--device", default="auto", help="auto | mps | cpu | 0 (CUDA)")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--balance", choices=["rfs", "none"])
    p.add_argument("--rfs-max", type=float, default=3.0, help="Max repeats per image")
    p.add_argument("--rfs-threshold", type=float, default=None, help="t in sqrt(t/f); default = most common class freq")
    p.add_argument("--patience", type=int)
    p.add_argument("--fraction", type=float, default=1.0, help="Use a fraction of train images (smoke tests)")
    p.add_argument("--cache", choices=["none", "ram", "disk"], default="none")
    p.add_argument("--name", help="Run name under runs/detect/ (default: <preset>_<model>)")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--export-as-default", action=argparse.BooleanOptionalAction, default=None,
                   help="Copy best.pt to weights/best.pt for the API. Default: on for finetune, off for baseline "
                        "(baseline is saved as weights/<run name>.pt)")
    args = p.parse_args(argv)

    preset = PRESETS[args.preset]
    for key in ("model", "epochs", "balance", "patience"):
        if getattr(args, key) is None:
            setattr(args, key, preset[key])
    args.cos_lr = preset["cos_lr"]
    if args.export_as_default is None:
        args.export_as_default = args.preset == "finetune"
    args.data = args.data.expanduser().resolve()
    if args.name is None:
        args.name = f"{args.preset}_{Path(args.model).stem}"
    return args


def main(argv=None):
    args = parse_args(argv)
    if not args.data.exists():
        sys.exit(f"{args.data} not found. Build it with data/prepare_dataset.py first.")
    load_data_yaml(args.data)  # validates class order

    train_yaml = args.data
    if args.balance == "rfs":
        train_yaml = build_rfs_dataset(args.data, args.rfs_max, args.rfs_threshold, args.seed)

    from ultralytics import YOLO

    device = pick_device(args.device)
    model_path = resolve_model(args.model)
    print(f"Training {model_path} on {train_yaml} | preset={args.preset} device={device} "
          f"epochs={args.epochs} imgsz={args.imgsz} batch={args.batch}")

    model = YOLO(model_path)
    model.train(
        data=str(train_yaml),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=device,
        workers=args.workers,
        patience=args.patience,
        cos_lr=args.cos_lr,
        fraction=args.fraction,
        cache=False if args.cache == "none" else args.cache,
        project=str(RUNS_DIR / "detect"),
        name=args.name,
        exist_ok=True,
        seed=args.seed,
        plots=True,
    )
    run_dir = Path(model.trainer.save_dir)
    export_best(run_dir, args, args.data)
    print(f"\nRun folder: {run_dir}")


if __name__ == "__main__":
    main()
