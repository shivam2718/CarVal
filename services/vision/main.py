"""
Vision Service - FastAPI (port 8001)
Member 1 - Vision/Damage Detection

Implements "Vision Service Interface (Member 1)" from docs/API_CONTRACT.md:
  POST /analyze   Body: {"image_paths": ["IMG-001", ...]}   ->   {"model": ..., "image_results": [...]}

The response fields follow schemas/vehicle_schema_v1.json exactly:
  response.model, response.image_results  -> vision.damage_detection.model / .image_results
  response.odometer                        -> vision.odometer

Extras that are not part of the Vehicle JSON live on their own endpoints:
  POST /analyze/upload     same response, for a multipart image upload (demo, no backend needed)
  GET  /annotated/{id}     JPEG of that image with boxes, class and confidence drawn on
  POST /vision/analyze     single-image alias from services/vision/README.md
  GET  /demo               tiny upload page for the Review 2 demo
"""

import logging
import re
import threading
import uuid
from collections import OrderedDict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional, Union

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field

from config import VISION_DIR, settings
from damage_classes import CLASSES
from detector import DamageDetector, draw_annotations, load_image

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("vision")

detector = DamageDetector(settings)

# Annotated JPEGs of recent analyses, so GET /annotated/{image_id} works after /analyze
_annotated: "OrderedDict[str, bytes]" = OrderedDict()
_annotated_lock = threading.Lock()


@asynccontextmanager
async def lifespan(_: FastAPI):
    detector.load()
    yield


app = FastAPI(
    title=settings.service_name,
    description="YOLOv8 damage detection for car images (dent, scratch, crack, glass, lamp, tire)",
    version=settings.version,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Models: field names are exactly those of schemas/vehicle_schema_v1.json
# ---------------------------------------------------------------------------

class BBox(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int


class Damage(BaseModel):
    damage_id: str
    type: str
    confidence: float
    bbox: BBox
    severity: Optional[str] = None
    affected_part: Optional[str] = None
    evidence: List[str] = Field(default_factory=list)


class ImageResult(BaseModel):
    image_id: str
    damages: List[Damage]


class Odometer(BaseModel):
    detected: bool = False
    value_km: Optional[float] = None
    confidence: Optional[float] = None
    image_id: Optional[str] = None
    evidence: List[str] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    model: str
    image_results: List[ImageResult]
    odometer: Odometer = Field(default_factory=Odometer)  # not implemented until Review 3: always detected=false


class ImageRef(BaseModel):
    image_id: str
    path: str


class AnalyzeRequest(BaseModel):
    # The contract example passes IDs ("IMG-001"); real file paths and {image_id, path} pairs also work
    image_paths: List[Union[str, ImageRef]] = Field(min_length=1)
    confidence: Optional[float] = Field(default=None, ge=0, le=1, description="Override the default threshold")


class SingleAnalyzeRequest(BaseModel):
    image_path: str
    image_id: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)


class SingleAnalyzeResponse(BaseModel):
    image_id: str
    model: str
    damages: List[Damage]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _remember_annotated(image_id: str, jpeg: bytes):
    with _annotated_lock:
        _annotated[image_id] = jpeg
        _annotated.move_to_end(image_id)
        while len(_annotated) > settings.annotated_cache_size:
            _annotated.popitem(last=False)


def _is_image_file(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in settings.allowed_extensions


def resolve_image(ref: Union[str, ImageRef]) -> "tuple[str, Path]":
    """Map one request entry to (image_id, file path). Raises 404 if no image file can be found."""
    if isinstance(ref, ImageRef):
        path = Path(ref.path).expanduser()
        if not _is_image_file(path):
            raise HTTPException(404, f"Image file not found or not a jpg/png: {ref.path}")
        return ref.image_id, path

    text = str(ref).strip()
    path = Path(text).expanduser()
    if _is_image_file(path):
        return path.stem, path

    # Bare ID such as "IMG-001": look in VISION_IMAGE_DIR for IMG-001.jpg / .jpeg / .png
    if settings.image_dir and re.fullmatch(r"[\w.-]+", text):
        for ext in settings.allowed_extensions:
            candidate = settings.image_dir / f"{text}{ext}"
            if candidate.is_file():
                return text, candidate
        detail = f"No image for '{text}' in {settings.image_dir}"
    else:
        detail = (f"Image '{text}' is not a file path and VISION_IMAGE_DIR is not set, "
                  "so the ID cannot be resolved. Send file paths or set VISION_IMAGE_DIR.")
    raise HTTPException(404, detail)


def run_analysis(items: "List[tuple[str, Image.Image]]", conf: Optional[float]) -> AnalyzeResponse:
    results, next_id = [], 1
    for image_id, img in items:
        damages = detector.detect(img, image_id, start_index=next_id, conf=conf)
        next_id += len(damages)
        _remember_annotated(image_id, draw_annotations(img, damages))
        results.append(ImageResult(image_id=image_id, damages=damages))
    return AnalyzeResponse(model=detector.model_name, image_results=results)


def read_upload(file: UploadFile) -> Image.Image:
    name = file.filename or "upload"
    if Path(name).suffix.lower() not in settings.allowed_extensions:
        raise HTTPException(400, f"{name}: only {', '.join(settings.allowed_extensions)} files are accepted")
    data = file.file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(400, f"{name}: file size exceeds maximum allowed ({settings.max_upload_mb} MB)")
    try:
        import io
        return load_image(io.BytesIO(data))
    except (UnidentifiedImageError, OSError):
        raise HTTPException(400, f"{name}: not a valid image")


def upload_image_id(file: UploadFile) -> str:
    """Keep a backend-style ID in the file name (IMG-1A2B3C4D.jpg); otherwise make one."""
    stem = Path(file.filename or "").stem
    return stem if re.fullmatch(r"IMG-[\w-]+", stem) else f"IMG-{uuid.uuid4().hex[:8].upper()}"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "service": settings.service_name,
        "version": settings.version,
        "endpoints": {
            "health": "GET /health",
            "analyze": "POST /analyze",
            "analyze_upload": "POST /analyze/upload",
            "annotated_image": "GET /annotated/{image_id}",
            "demo": "GET /demo",
            "docs": "GET /docs",
        },
    }


@app.get("/health")
def health():
    ok = detector.mode in ("trained", "fallback")
    return {
        "status": "healthy" if ok else "degraded",
        "service": "vision",
        "model_loaded": ok,
        "model_mode": detector.mode,  # trained | fallback | unavailable
        "model": detector.model_name,
        "weights": str(detector.weights_path) if detector.weights_path else None,
        "device": detector.device,
        "classes": CLASSES,
        "confidence_threshold": settings.confidence,
        "note": None if detector.mode == "trained"
        else "No trained damage weights found: no damages are reported. Put best.pt in services/vision/weights/.",
    }


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    """Detect damage in the images named by `image_paths` (contract: docs/API_CONTRACT.md)."""
    resolved = [resolve_image(ref) for ref in req.image_paths]
    items = []
    for image_id, path in resolved:
        try:
            items.append((image_id, load_image(path)))
        except (UnidentifiedImageError, OSError):
            raise HTTPException(400, f"{path.name}: not a valid image")
    return run_analysis(items, req.confidence)


@app.post("/analyze/upload", response_model=AnalyzeResponse)
def analyze_upload(files: List[UploadFile] = File(...), confidence: Optional[float] = None):
    """Same result as /analyze for uploaded images. Fetch the drawn boxes from /annotated/{image_id}."""
    items = [(upload_image_id(f), read_upload(f)) for f in files]
    return run_analysis(items, confidence)


@app.post("/vision/analyze", response_model=SingleAnalyzeResponse)
def vision_analyze(req: SingleAnalyzeRequest):
    """Single-image form from services/vision/README.md."""
    ref: Union[str, ImageRef] = ImageRef(image_id=req.image_id, path=req.image_path) if req.image_id else req.image_path
    image_id, path = resolve_image(ref)
    try:
        img = load_image(path)
    except (UnidentifiedImageError, OSError):
        raise HTTPException(400, f"{path.name}: not a valid image")
    out = run_analysis([(image_id, img)], req.confidence)
    return SingleAnalyzeResponse(image_id=image_id, model=out.model, damages=out.image_results[0].damages)


@app.get("/annotated/{image_id}")
def annotated(image_id: str):
    """JPEG of a recently analysed image with boxes, class and confidence drawn on."""
    with _annotated_lock:
        jpeg = _annotated.get(image_id)
    if jpeg is None:
        raise HTTPException(404, f"No annotated image for '{image_id}'. Analyse it first (the last "
                                 f"{settings.annotated_cache_size} are kept).")
    return Response(content=jpeg, media_type="image/jpeg")


@app.get("/demo", include_in_schema=False)
def demo():
    return FileResponse(VISION_DIR / "demo.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=False)
