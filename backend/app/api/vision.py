"""
Vision module (damage detection on car photos)

POST /inspection/{id}/vision/images                       upload car photos
POST /inspection/{id}/vision/analyze                      run the Vision Service (YOLOv8)
GET  /inspection/{id}/vision/images/{image_id}            original photo
GET  /inspection/{id}/vision/images/{image_id}/annotated  photo with damage boxes
"""

import uuid
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response

from app.core.config import settings
from app.core.store import inspections_db
from app.services.vision_client import VisionServiceClient, VisionServiceError

router = APIRouter(prefix="/inspection/{inspection_id}/vision", tags=["vision"])

vision_client = VisionServiceClient()
IMAGE_EXTS = (".jpg", ".jpeg", ".png")


def _get_inspection(inspection_id: str) -> dict:
    if inspection_id not in inspections_db:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return inspections_db[inspection_id]


@router.post("/images")
async def upload_images(inspection_id: str, files: List[UploadFile] = File(...)):
    inspection = _get_inspection(inspection_id)
    max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
    uploaded = []
    for file in files:
        name = file.filename or "image"
        if not name.lower().endswith(IMAGE_EXTS):
            raise HTTPException(status_code=400, detail=f"{name}: only .jpg, .jpeg, .png are accepted")
        contents = await file.read()
        if len(contents) > max_bytes:
            raise HTTPException(status_code=400,
                                detail=f"{name}: file size exceeds maximum allowed ({settings.MAX_IMAGE_SIZE_MB} MB)")
        uploaded.append({
            "file_id": f"IMG-{str(uuid.uuid4())[:8].upper()}",
            "filename": name,
            "size": len(contents),
            "content_type": file.content_type,
            "contents": contents,
        })
    inspection["images"].extend(uploaded)
    return {
        "inspection_id": inspection_id,
        "uploaded_images": len(uploaded),
        "files": [{k: v for k, v in f.items() if k != "contents"} for f in uploaded],
    }


@router.post("/analyze")
async def analyze(inspection_id: str):
    inspection = _get_inspection(inspection_id)
    images = inspection["images"]
    if not images:
        raise HTTPException(status_code=400, detail="No car images uploaded for vision analysis")
    try:
        result = await vision_client.analyze_images(images)
    except VisionServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Stored in the exact shape of vehicle_schema_v1.json -> vision
    inspection["vision_results"] = {
        "damage_detection": {
            "model": result.get("model"),
            "image_results": result.get("image_results", []),
        },
        "odometer": result.get("odometer") or {
            "detected": False, "value_km": None, "confidence": None, "image_id": None, "evidence": []
        },
    }
    total = sum(len(r.get("damages", [])) for r in result.get("image_results", []))
    return {
        "inspection_id": inspection_id,
        "status": "vision_analysis_completed",
        "images_processed": len(images),
        "total_damages": total,
        "vision": inspection["vision_results"],
    }


@router.get("/images/{image_id}")
def get_original_image(inspection_id: str, image_id: str):
    for img in _get_inspection(inspection_id)["images"]:
        if img["file_id"] == image_id:
            return Response(content=img["contents"], media_type=img.get("content_type") or "image/jpeg")
    raise HTTPException(status_code=404, detail="Image not found")


@router.get("/images/{image_id}/annotated")
async def get_annotated_image(inspection_id: str, image_id: str):
    """Image with damage boxes drawn (proxied from Vision). Falls back to the original."""
    _get_inspection(inspection_id)
    data = await vision_client.annotated(image_id)
    if data is not None:
        return Response(content=data, media_type="image/jpeg")
    return get_original_image(inspection_id, image_id)
