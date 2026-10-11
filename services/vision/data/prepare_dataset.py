"""
Dataset preparation for the CarVal Vision Service
Member 1 - Vision/Damage Detection

Converts a downloaded car-damage dataset into a YOLO dataset with our six
classes (dent, scratch, crack, glass, lamp, tire) and train/val/test splits.

Supported sources:
  roboflow  Roboflow Universe export in "YOLOv8" format
            (train/ valid/ test/ folders, each with images/ and labels/,
            plus data.yaml). Polygon labels are converted to boxes.
  cardd     CarDD in COCO format (annotations/*.json + image folders).

Usage:
  # 1. See which classes a dataset has and how they map
  python data/prepare_dataset.py inspect --source roboflow --src datasets/raw/roboflow

  # 2. Build the CarVal dataset
  python data/prepare_dataset.py build --source roboflow --src datasets/raw/roboflow

Output (default datasets/carval_damage/):
  images/{train,val,test}/  labels/{train,val,test}/  data.yaml  dataset_summary.json
"""

import argparse
import json
import random
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

VISION_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VISION_DIR))
from damage_classes import CLASSES, CLASS_TO_ID  # noqa: E402

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
SPLITS = ("train", "val", "test")
# Roboflow calls the validation split "valid"
SPLIT_ALIASES = {"train": "train", "valid": "val", "val": "val", "test": "test"}

DEFAULT_CLASS_MAP = VISION_DIR / "data" / "class_map.yaml"
DEFAULT_OUT = VISION_DIR / "datasets" / "carval_damage"


# ---------------------------------------------------------------------------
# Class mapping
# ---------------------------------------------------------------------------

def normalise(name: str) -> str:
    return " ".join(str(name).lower().replace("-", " ").replace("_", " ").split())


def load_class_map(path: Path) -> dict:
    with open(path) as f:
        raw = yaml.safe_load(f) or {}
    mapping = {}
    for src, dst in (raw.get("mapping") or {}).items():
        if dst is not None and dst not in CLASS_TO_ID:
            raise ValueError(f"class_map: '{src}' maps to unknown class '{dst}'. Use one of {CLASSES} or null.")
        mapping[normalise(src)] = dst
    return mapping


def resolve(name: str, mapping: dict):
    """Return (carval_class or None, status) where status is mapped/dropped/unmapped."""
    key = normalise(name)
    if key not in mapping:
        return None, "unmapped"
    if mapping[key] is None:
        return None, "dropped"
    return mapping[key], "mapped"


# ---------------------------------------------------------------------------
# Readers: each returns a list of samples
#   {"image": Path, "split": "train"|"val"|"test"|None,
#    "boxes": [(source_class_name, cx, cy, w, h), ...]}  (normalised 0-1)
# ---------------------------------------------------------------------------

def read_roboflow(src: Path) -> list:
    yaml_files = list(src.glob("data.yaml")) or list(src.rglob("data.yaml"))
    if not yaml_files:
        raise FileNotFoundError(f"No data.yaml under {src}. Is this a Roboflow YOLOv8 export?")
    root = yaml_files[0].parent
    with open(yaml_files[0]) as f:
        names = yaml.safe_load(f).get("names")
    if isinstance(names, dict):
        names = [names[k] for k in sorted(names)]
    if not names:
        raise ValueError(f"{yaml_files[0]} has no 'names' list")

    samples = []
    for split_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        split = SPLIT_ALIASES.get(split_dir.name.lower())
        img_dir = split_dir / "images"
        if split is None or not img_dir.is_dir():
            continue
        for img in sorted(img_dir.iterdir()):
            if img.suffix.lower() not in IMAGE_EXTS:
                continue
            label_file = split_dir / "labels" / (img.stem + ".txt")
            boxes = []
            if label_file.exists():
                for line in label_file.read_text().splitlines():
                    box = parse_yolo_line(line, names)
                    if box:
                        boxes.append(box)
            samples.append({"image": img, "split": split, "boxes": boxes})
    return samples


def parse_yolo_line(line: str, names: list):
    parts = line.split()
    if len(parts) < 5:
        return None
    cls_id = int(float(parts[0]))
    if cls_id >= len(names):
        return None
    coords = [float(v) for v in parts[1:]]
    if len(coords) == 4:
        cx, cy, w, h = coords
    else:
        # Segmentation polygon x1 y1 x2 y2 ... -> enclosing box
        xs, ys = coords[0::2], coords[1::2]
        x1, x2, y1, y2 = min(xs), max(xs), min(ys), max(ys)
        cx, cy, w, h = (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1
    if w <= 0 or h <= 0:
        return None
    return (names[cls_id], cx, cy, w, h)


def read_cardd(src: Path) -> list:
    json_files = sorted(src.rglob("*.json"))
    json_files = [j for j in json_files if "instances" in j.name or j.parent.name == "annotations"]
    if not json_files:
        raise FileNotFoundError(f"No COCO annotation JSON under {src} (expected annotations/instances_*.json)")

    # Index every image under src by file name, so we don't depend on the exact folder layout.
    # A name can appear in several folders; the one matching the JSON's split wins.
    image_index = defaultdict(list)
    for p in src.rglob("*"):
        if p.suffix.lower() in IMAGE_EXTS:
            image_index[p.name].append(p)

    def find_image(file_name, split):
        candidates = image_index.get(Path(file_name).name, [])
        for c in candidates:
            if split and split in c.parent.name.lower():
                return c
        return candidates[0] if candidates else None

    samples = []
    for jf in json_files:
        split = None
        for key in ("train", "val", "test"):
            if key in jf.stem.lower():
                split = key
                break
        with open(jf) as f:
            coco = json.load(f)
        cats = {c["id"]: c["name"] for c in coco.get("categories", [])}
        anns_by_image = defaultdict(list)
        for ann in coco.get("annotations", []):
            anns_by_image[ann["image_id"]].append(ann)

        missing = 0
        for im in coco.get("images", []):
            path = find_image(im["file_name"], split)
            if path is None:
                missing += 1
                continue
            W, H = im["width"], im["height"]
            boxes = []
            for ann in anns_by_image.get(im["id"], []):
                x, y, w, h = ann["bbox"]
                if w <= 0 or h <= 0:
                    continue
                boxes.append((cats[ann["category_id"]], (x + w / 2) / W, (y + h / 2) / H, w / W, h / H))
            samples.append({"image": path, "split": split, "boxes": boxes})
        if missing:
            print(f"  ! {jf.name}: {missing} images listed in the JSON were not found on disk")
    return samples


READERS = {"roboflow": read_roboflow, "cardd": read_cardd}


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_inspect(args):
    mapping = load_class_map(args.class_map)
    samples = READERS[args.source](args.src)
    counts = Counter(b[0] for s in samples for b in s["boxes"])
    splits = Counter(s["split"] or "unsplit" for s in samples)

    print(f"\nDataset: {args.src}  ({args.source})")
    print(f"Images: {len(samples)}  by split: {dict(splits)}")
    print(f"\n{'source class':<28}{'instances':>10}   -> CarVal class")
    print("-" * 60)
    unmapped = []
    for name, n in counts.most_common():
        dst, status = resolve(name, mapping)
        target = dst if status == "mapped" else f"({status})"
        print(f"{name:<28}{n:>10}   -> {target}")
        if status == "unmapped":
            unmapped.append(name)
    if unmapped:
        print(f"\n! {len(unmapped)} unmapped class(es). Add them to {args.class_map} "
              f"(map to one of {CLASSES} or null) and run inspect again.")
    else:
        print("\n✓ Every source class is mapped or deliberately dropped.")


def assign_splits(samples, ratios, seed, resplit):
    """Keep the source splits when train/val/test all exist, unless --resplit."""
    present = {s["split"] for s in samples}
    if not resplit and {"train", "val", "test"} <= present:
        return samples, "source"

    rng = random.Random(seed)
    shuffled = samples[:]
    rng.shuffle(shuffled)
    n = len(shuffled)
    n_train = int(n * ratios[0])
    n_val = int(n * ratios[1])
    for i, s in enumerate(shuffled):
        s["split"] = "train" if i < n_train else "val" if i < n_train + n_val else "test"
    return shuffled, f"random {ratios} seed={seed}"


def cmd_build(args):
    mapping = load_class_map(args.class_map)
    print(f"Reading {args.source} dataset from {args.src} ...")
    samples = READERS[args.source](args.src)
    if not samples:
        sys.exit("No images found. Check --src.")

    # Remap classes
    unmapped, dropped = Counter(), Counter()
    kept = []
    for s in samples:
        boxes = []
        for name, cx, cy, w, h in s["boxes"]:
            dst, status = resolve(name, mapping)
            if status == "mapped":
                boxes.append((CLASS_TO_ID[dst], cx, cy, w, h))
            elif status == "unmapped":
                unmapped[name] += 1
            else:
                dropped[name] += 1
        if not boxes and args.drop_empty:
            continue
        kept.append({**s, "boxes": boxes})

    kept, split_mode = assign_splits(kept, args.split, args.seed, args.resplit)

    out = args.out
    if out.exists():
        if not args.overwrite:
            sys.exit(f"{out} already exists. Pass --overwrite to replace it.")
        shutil.rmtree(out)
    for split in SPLITS:
        (out / "images" / split).mkdir(parents=True, exist_ok=True)
        (out / "labels" / split).mkdir(parents=True, exist_ok=True)

    per_split = {sp: {"images": 0, "background_images": 0, "instances": Counter()} for sp in SPLITS}
    used_names = set()
    for s in kept:
        split = s["split"]
        # Avoid name clashes when different source splits reuse a file name
        stem = s["image"].stem
        name = stem
        i = 1
        while (split, name) in used_names:
            name = f"{stem}_{i}"
            i += 1
        used_names.add((split, name))

        dst_img = out / "images" / split / (name + s["image"].suffix.lower())
        if args.symlink:
            dst_img.symlink_to(s["image"].resolve())
        else:
            shutil.copy2(s["image"], dst_img)

        lines = [f"{c} {clamp(cx):.6f} {clamp(cy):.6f} {clamp(w):.6f} {clamp(h):.6f}" for c, cx, cy, w, h in s["boxes"]]
        (out / "labels" / split / (name + ".txt")).write_text("\n".join(lines) + ("\n" if lines else ""))

        stats = per_split[split]
        stats["images"] += 1
        if not s["boxes"]:
            stats["background_images"] += 1
        for c, *_ in s["boxes"]:
            stats["instances"][CLASSES[c]] += 1

    data_yaml = {
        "path": str(out.resolve()),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "nc": len(CLASSES),
        "names": {i: c for i, c in enumerate(CLASSES)},
    }
    with open(out / "data.yaml", "w") as f:
        yaml.safe_dump(data_yaml, f, sort_keys=False)

    summary = {
        "source": args.source,
        "source_path": str(args.src.resolve()),
        "split_mode": split_mode,
        "classes": CLASSES,
        "splits": {
            sp: {
                "images": v["images"],
                "background_images": v["background_images"],
                "instances": {c: v["instances"].get(c, 0) for c in CLASSES},
            }
            for sp, v in per_split.items()
        },
        "dropped_classes": dict(dropped),
        "unmapped_classes": dict(unmapped),
    }
    with open(out / "dataset_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print_summary(summary, out)


def clamp(v: float) -> float:
    return min(max(v, 0.0), 1.0)


def print_summary(summary, out):
    print(f"\n✓ Dataset written to {out}")
    print(f"  split mode: {summary['split_mode']}\n")
    header = f"{'split':<7}{'images':>8}{'bg':>6}" + "".join(f"{c:>9}" for c in CLASSES)
    print(header)
    print("-" * len(header))
    for sp, v in summary["splits"].items():
        print(f"{sp:<7}{v['images']:>8}{v['background_images']:>6}"
              + "".join(f"{v['instances'][c]:>9}" for c in CLASSES))
    for sp, v in summary["splits"].items():
        missing = [c for c in CLASSES if v["instances"][c] == 0]
        if missing and v["images"]:
            print(f"\n! {sp}: no instances of {missing}. Metrics for these classes will be empty.")
    if summary["unmapped_classes"]:
        print(f"\n! Unmapped source classes were dropped: {summary['unmapped_classes']}")
        print("  Add them to data/class_map.yaml and rebuild if they are real damage classes.")


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    def common(sp):
        sp.add_argument("--source", choices=sorted(READERS), required=True)
        sp.add_argument("--src", type=Path, required=True, help="Folder of the downloaded/unzipped dataset")
        sp.add_argument("--class-map", type=Path, default=DEFAULT_CLASS_MAP)

    common(sub.add_parser("inspect", help="List source classes and how they map"))

    b = sub.add_parser("build", help="Build the CarVal YOLO dataset")
    common(b)
    b.add_argument("--out", type=Path, default=DEFAULT_OUT)
    b.add_argument("--split", type=float, nargs=3, default=[0.7, 0.2, 0.1], metavar=("TRAIN", "VAL", "TEST"),
                   help="Ratios used when the source has no full train/val/test split (or with --resplit)")
    b.add_argument("--resplit", action="store_true", help="Ignore source splits and re-split randomly")
    b.add_argument("--seed", type=int, default=42)
    b.add_argument("--drop-empty", action="store_true",
                   help="Drop images with no CarVal boxes (default keeps them as background images)")
    b.add_argument("--symlink", action="store_true", help="Symlink images instead of copying (saves disk)")
    b.add_argument("--overwrite", action="store_true")

    args = p.parse_args(argv)
    if args.command == "build" and abs(sum(args.split) - 1.0) > 1e-6:
        p.error("--split ratios must sum to 1")
    return args


def main(argv=None):
    args = parse_args(argv)
    if args.command == "inspect":
        cmd_inspect(args)
    else:
        cmd_build(args)


if __name__ == "__main__":
    main()
