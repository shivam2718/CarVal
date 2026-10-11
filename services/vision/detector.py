"""
Damage detector: YOLOv8 inference, severity rule and box drawing
Member 1 - Vision/Damage Detection
"""

import io
import logging
import threading
from pathlib import Path
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFont, ImageOps

from config import FALLBACK_WEIGHTS, Settings
from damage_classes import CLASSES

log = logging.getLogger("vision")

FALLBACK_MODEL_NAME = "yolov8n-coco-fallback (not damage-trained)"

# One colour per class for the annotated image
CLASS_COLORS = {
    "dent": (255, 99, 71),
    "scratch": (255, 193, 7),
    "crack": (156, 39, 176),
    "glass": (3, 169, 244),
    "lamp": (76, 175, 80),
    "tire": (255, 87, 34),
}


def severity_from_area(area_ratio: float) -> str:
    """Rule-based severity: how much of the photo the damage box covers.

    This is a heuristic, not a trained severity model (that is a Review 3+ extension).
    """
    if area_ratio < 0.02:
        return "low"
    if area_ratio < 0.10:
        return "medium"
    return "high"


def load_image(source) -> Image.Image:
    """Open an image as RGB with EXIF rotation applied, so boxes match what a browser displays."""
    img = Image.open(source)
    img = ImageOps.exif_transpose(img)
    return img.convert("RGB")


class DamageDetector:
    """Loads weights once and runs detection. Falls back to pretrained weights if none are trained yet."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.model = None
        self.mode = "unavailable"  # trained | fallback | unavailable
        self.weights_path: Optional[Path] = None
        self.device = "cpu"
        self._lock = threading.Lock()  # Ultralytics predictors are not thread-safe

    @property
    def model_name(self) -> str:
        return self.settings.model_name if self.mode == "trained" else FALLBACK_MODEL_NAME

    def load(self):
        from ultralytics import YOLO

        self.device = self._pick_device()
        for path in self.settings.weight_candidates():
            if path.exists():
                model = YOLO(str(path))
                names = [model.names[k] for k in sorted(model.names)]
                if names != CLASSES:
                    log.warning("%s has classes %s, not %s; ignoring it", path, names[:8], CLASSES)
                    continue
                self.model, self.weights_path, self.mode = model, path, "trained"
                log.info("Loaded damage model %s on %s", path, self.device)
                return

        # Fallback: pretrained COCO weights. They know cars, not dents, so this mode reports
        # zero damages. It keeps the service and its contract working until trained weights exist.
        try:
            source = FALLBACK_WEIGHTS if FALLBACK_WEIGHTS.exists() else "yolov8n.pt"
            self.model, self.mode = YOLO(str(source)), "fallback"
            self.weights_path = FALLBACK_WEIGHTS if FALLBACK_WEIGHTS.exists() else None
            log.warning("No trained weights found (looked for %s). Running in FALLBACK mode: "
                        "no damages will be reported.", [str(p) for p in self.settings.weight_candidates()])
        except Exception as exc:  # offline and no cached weights
            self.model, self.mode = None, "unavailable"
            log.error("Could not load any weights (%s). Service will report no damages.", exc)

    def _pick_device(self) -> str:
        if self.settings.device != "auto":
            return self.settings.device
        import torch
        if torch.cuda.is_available():
            return "0"
        if torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    def detect(self, img: Image.Image, image_id: str, start_index: int = 1, conf: Optional[float] = None) -> List[dict]:
        """Return damages for one image, as dicts matching vehicle_schema_v1 vision.damage_detection."""
        if self.mode != "trained":
            return []
        with self._lock:
            result = self.model.predict(
                source=img, conf=conf if conf is not None else self.settings.confidence,
                iou=self.settings.iou, imgsz=self.settings.imgsz, device=self.device, verbose=False,
            )[0]

        W, H = img.size
        damages = []
        boxes = sorted(result.boxes, key=lambda b: float(b.conf[0]), reverse=True)
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = (float(v) for v in box.xyxy[0])
            x1, x2 = max(0, min(W, x1)), max(0, min(W, x2))
            y1, y2 = max(0, min(H, y1)), max(0, min(H, y2))
            area_ratio = ((x2 - x1) * (y2 - y1)) / (W * H)
            damages.append({
                "damage_id": f"DMG-{start_index + i:03d}",
                "type": CLASSES[int(box.cls[0])],
                "confidence": round(float(box.conf[0]), 4),
                "bbox": {"x1": int(round(x1)), "y1": int(round(y1)), "x2": int(round(x2)), "y2": int(round(y2))},
                "severity": severity_from_area(area_ratio),
                "affected_part": None,  # no part-detection model yet
                "evidence": [image_id],
            })
        return damages


def draw_annotations(img: Image.Image, damages: List[dict]) -> bytes:
    """Return a JPEG of the image with a box, class and confidence for each damage."""
    img = img.copy()
    draw = ImageDraw.Draw(img)
    W, H = img.size
    line = max(2, round(max(W, H) / 400))
    font = ImageFont.load_default(size=max(12, round(max(W, H) / 45)))

    for d in damages:
        b = d["bbox"]
        color = CLASS_COLORS.get(d["type"], (255, 0, 0))
        draw.rectangle([b["x1"], b["y1"], b["x2"], b["y2"]], outline=color, width=line)
        label = f"{d['type']} {d['confidence']:.2f}"
        tb = draw.textbbox((0, 0), label, font=font)
        tw, th = tb[2] - tb[0], tb[3] - tb[1]
        ty = b["y1"] - th - 6 if b["y1"] - th - 6 >= 0 else b["y1"] + line
        draw.rectangle([b["x1"], ty, b["x1"] + tw + 8, ty + th + 6], fill=color)
        draw.text((b["x1"] + 4, ty + 1), label, fill=(255, 255, 255), font=font)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()
