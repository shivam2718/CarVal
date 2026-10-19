"""
Evaluation for the CarVal Vision Service
Member 1 - Vision/Damage Detection

Scores one or more YOLO weights on a split (default: test) and writes
precision, recall, mAP@50 and mAP@50-95, overall and per class, to
reports/metrics.json and reports/metrics.md.

Precision and recall are the Ultralytics values at the confidence that
maximises F1 for each model. mAP is computed over all confidences
(conf=0.001), as is standard.

Usage (from services/vision/):
  python evaluation/evaluate.py --data ~/Documents/BTP/datasets/CarDD_yolo/data.yaml \\
      --weights weights/baseline_best.pt:baseline \\
      --weights weights/finetune_best.pt:finetune

  --weights takes path or path:label. Repeat it to compare models.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

VISION_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VISION_DIR))
from damage_classes import CLASSES  # noqa: E402

DEFAULT_OUT = VISION_DIR / "reports"


def pick_device(requested: str) -> str:
    if requested != "auto":
        return requested
    import torch
    if torch.cuda.is_available():
        return "0"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def split_weights_arg(value: str):
    # "path:label" - but a path may itself contain ':' on Windows, so split on the last one only
    if ":" in value and not value.rsplit(":", 1)[1].endswith(".pt"):
        path, label = value.rsplit(":", 1)
    else:
        path, label = value, Path(value).stem
    return Path(path).expanduser(), label


def evaluate_one(weights: Path, label: str, data: Path, split: str, imgsz: int, device: str, plots_dir: Path):
    from ultralytics import YOLO

    model = YOLO(str(weights))
    names = [model.names[k] for k in sorted(model.names)]
    if names != CLASSES:
        sys.exit(f"{weights} has classes {names}, expected {CLASSES}")

    res = model.val(data=str(data), split=split, imgsz=imgsz, device=device, batch=16,
                    plots=True, project=str(plots_dir), name=label, exist_ok=True, verbose=False)
    box = res.box

    per_class = {}
    for pos, cls_id in enumerate(box.ap_class_index):
        per_class[CLASSES[int(cls_id)]] = {
            "instances": int(res.nt_per_class[int(cls_id)]) if hasattr(res, "nt_per_class") else None,
            "precision": float(box.p[pos]),
            "recall": float(box.r[pos]),
            "map50": float(box.ap50[pos]),
            "map50_95": float(box.ap[pos]),
        }
    for c in CLASSES:  # classes with no ground truth in the split
        per_class.setdefault(c, {"instances": 0, "precision": None, "recall": None, "map50": None, "map50_95": None})

    return {
        "label": label,
        "weights": weights.name,
        "model_params": int(sum(p.numel() for p in model.model.parameters())),
        "overall": {
            "precision": float(box.mp),
            "recall": float(box.mr),
            "map50": float(box.map50),
            "map50_95": float(box.map),
        },
        "per_class": {c: per_class[c] for c in CLASSES},
        "speed_ms_per_image": {k: round(float(v), 2) for k, v in res.speed.items()},
    }


def fmt(v, digits=3):
    return "n/a" if v is None else f"{v:.{digits}f}"


def render_markdown(report: dict) -> str:
    models = report["models"]
    lines = [
        "# CarVal Vision: damage detection evaluation",
        "",
        f"- **Split:** `{report['split']}` ({report['split_images']} images, {report['split_instances']} damage boxes)",
        f"- **Dataset:** {report['data']}",
        f"- **Image size:** {report['imgsz']}  |  **Device:** {report['device']}  |  **Date:** {report['generated_at'][:10]}",
        "- **Metrics:** Precision and recall are at each model's best-F1 confidence threshold. "
        "mAP@50 is the mean average precision at IoU 0.5; mAP@50-95 averages IoU 0.5 to 0.95.",
        "",
        "## Overall",
        "",
        "| Model | Params | Precision | Recall | mAP@50 | mAP@50-95 |",
        "|---|---|---|---|---|---|",
    ]
    for m in models:
        o = m["overall"]
        lines.append(f"| {m['label']} | {m['model_params'] / 1e6:.1f}M | {fmt(o['precision'])} | {fmt(o['recall'])} "
                     f"| **{fmt(o['map50'])}** | {fmt(o['map50_95'])} |")

    lines += ["", "## Per class", ""]
    header = "| Class | Boxes |" + "".join(f" {m['label']} P | {m['label']} R | {m['label']} mAP@50 |" for m in models)
    sep = "|---|---|" + "---|---|---|" * len(models)
    lines += [header, sep]
    for c in CLASSES:
        first = models[0]["per_class"][c]
        row = f"| {c} | {first['instances']} |"
        for m in models:
            pc = m["per_class"][c]
            row += f" {fmt(pc['precision'])} | {fmt(pc['recall'])} | {fmt(pc['map50'])} |"
        lines.append(row)

    lines += ["", "## Speed", "", "| Model | Preprocess | Inference | Postprocess |", "|---|---|---|---|"]
    for m in models:
        s = m["speed_ms_per_image"]
        lines.append(f"| {m['label']} | {s.get('preprocess')} ms | {s.get('inference')} ms | {s.get('postprocess')} ms |")
    lines.append("")
    return "\n".join(lines)


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", type=Path, required=True, help="data.yaml")
    p.add_argument("--weights", action="append", required=True, help="path or path:label (repeatable)")
    p.add_argument("--split", default="test", choices=["train", "val", "test"])
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--device", default="auto", help="auto | mps | cpu | 0")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    data = args.data.expanduser().resolve()
    if not data.exists():
        sys.exit(f"{data} not found")
    device = pick_device(args.device)
    args.out.mkdir(parents=True, exist_ok=True)

    models = []
    for w in args.weights:
        path, label = split_weights_arg(w)
        if not path.exists():
            sys.exit(f"{path} not found")
        print(f"\n=== Evaluating {label} ({path}) on '{args.split}' [{device}] ===")
        models.append(evaluate_one(path, label, data, args.split, args.imgsz, device, args.out / "plots"))

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data": str(data),
        "split": args.split,
        "imgsz": args.imgsz,
        "device": device,
        "classes": CLASSES,
        "split_images": None,
        "split_instances": None,
        "models": models,
    }
    # Split size comes from the dataset summary if it sits next to data.yaml, else from the label files
    summary = data.parent / "dataset_summary.json"
    if summary.exists():
        s = json.loads(summary.read_text())["splits"][args.split]
        report["split_images"], report["split_instances"] = s["images"], sum(s["instances"].values())
    else:
        report["split_instances"] = sum((m["per_class"][c]["instances"] or 0) for c in CLASSES for m in models[:1])

    (args.out / "metrics.json").write_text(json.dumps(report, indent=2))
    md = render_markdown(report)
    (args.out / "metrics.md").write_text(md)
    print("\n" + md)
    print(f"✓ Wrote {args.out / 'metrics.json'} and {args.out / 'metrics.md'}")


if __name__ == "__main__":
    main()
