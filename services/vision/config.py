"""
Vision Service configuration
Member 1 - Vision/Damage Detection

Read from environment variables (or services/vision/.env, which is gitignored).
Nothing here needs to be set for a default local run.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

VISION_DIR = Path(__file__).resolve().parent
load_dotenv(VISION_DIR / ".env")

DEFAULT_WEIGHTS = VISION_DIR / "weights" / "best.pt"
FALLBACK_WEIGHTS = VISION_DIR / "weights" / "yolov8n.pt"


def _path_or_none(value: Optional[str]) -> Optional[Path]:
    return Path(value).expanduser() if value else None


@dataclass
class Settings:
    service_name: str = "CarVal Vision Service"
    version: str = "0.1.0"
    host: str = field(default_factory=lambda: os.getenv("VISION_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(os.getenv("VISION_PORT", "8001")))

    # Model. Tried in order: VISION_MODEL_PATH, weights/best.pt; otherwise fallback mode.
    model_path: Optional[Path] = field(default_factory=lambda: _path_or_none(os.getenv("VISION_MODEL_PATH")))
    model_name: str = field(default_factory=lambda: os.getenv("VISION_MODEL_NAME", "YOLOv8-damage-detection-v1"))
    device: str = field(default_factory=lambda: os.getenv("VISION_DEVICE", "auto"))  # auto | mps | cpu | 0
    imgsz: int = field(default_factory=lambda: int(os.getenv("VISION_IMGSZ", "640")))
    confidence: float = field(default_factory=lambda: float(os.getenv("VISION_CONFIDENCE_THRESHOLD", "0.25")))
    iou: float = field(default_factory=lambda: float(os.getenv("VISION_IOU_THRESHOLD", "0.5")))

    # Where bare image IDs (e.g. "IMG-001") are looked up. Member 3's backend saves uploads here.
    image_dir: Optional[Path] = field(default_factory=lambda: _path_or_none(os.getenv("VISION_IMAGE_DIR")))

    max_upload_mb: int = 10
    allowed_extensions: List[str] = field(default_factory=lambda: [".jpg", ".jpeg", ".png"])
    annotated_cache_size: int = 50
    cors_origins: List[str] = field(default_factory=lambda: ["http://localhost:3000", "http://localhost:8000"])

    def weight_candidates(self) -> List[Path]:
        paths = [self.model_path] if self.model_path else []
        paths.append(DEFAULT_WEIGHTS)
        return paths


settings = Settings()
