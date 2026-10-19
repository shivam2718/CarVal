"""
Inspection Endpoints
Member 3 - Backend Integration
Orchestrates Vision Service and Document AI
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response
from app.services.vision_client import VisionServiceClient, VisionServiceError
from app.core.config import settings
from typing import List
import json
import uuid
from datetime import datetime

router = APIRouter(
    prefix="/inspection",
    tags=["inspection"]
)

vision_client = VisionServiceClient()
IMAGE_EXTS = (".jpg", ".jpeg", ".png")

# Temporary in-memory storage for Review 2 (replace with DB in Review 3)
inspections_db = {}


@router.post("")
def create_inspection():
    """
    Create a new inspection
    POST /inspection
    
    Returns: inspection_id for subsequent operations
    """
    inspection_id = f"INS-{str(uuid.uuid4())[:8].upper()}"
    
    inspections_db[inspection_id] = {
        "id": inspection_id,
        "created_at": datetime.now().isoformat(),
        "status": "created",
        "images": [],
        "documents": [],
        "vision_results": None,
        "document_results": None,
    }
    
    return {
        "inspection_id": inspection_id,
        "status": "created",
        "created_at": inspections_db[inspection_id]["created_at"]
    }


@router.post("/{inspection_id}/images")
async def upload_images(inspection_id: str, files: List[UploadFile] = File(...)):
    """POST /inspection/{inspection_id}/images - bytes are kept so Vision can be called later."""
    if inspection_id not in inspections_db:
        raise HTTPException(status_code=404, detail="Inspection not found")

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

    inspections_db[inspection_id]["images"].extend(uploaded)

    return {
        "inspection_id": inspection_id,
        "uploaded_images": len(uploaded),
        "files": [{k: v for k, v in f.items() if k != "contents"} for f in uploaded],
    }


@router.get("/{inspection_id}/images/{image_id}")
def get_original_image(inspection_id: str, image_id: str):
    """Original uploaded image (for display in the dashboard)."""
    if inspection_id not in inspections_db:
        raise HTTPException(status_code=404, detail="Inspection not found")
    for img in inspections_db[inspection_id]["images"]:
        if img["file_id"] == image_id:
            return Response(content=img["contents"], media_type=img.get("content_type") or "image/jpeg")
    raise HTTPException(status_code=404, detail="Image not found")


@router.get("/{inspection_id}/images/{image_id}/annotated")
async def get_annotated_image(inspection_id: str, image_id: str):
    """Image with damage boxes drawn (proxied from Vision). Falls back to the original."""
    if inspection_id not in inspections_db:
        raise HTTPException(status_code=404, detail="Inspection not found")
    data = await vision_client.annotated(image_id)
    if data is not None:
        return Response(content=data, media_type="image/jpeg")
    return get_original_image(inspection_id, image_id)


@router.post("/{inspection_id}/documents")
async def upload_documents(inspection_id: str, files: List[UploadFile] = File(...)):
    """
    Upload vehicle documents (RC, Insurance, Service Bills)
    POST /inspection/{inspection_id}/documents
    
    Args:
        inspection_id: Inspection ID from create_inspection
        files: Documents (PDF, images)
    """
    if inspection_id not in inspections_db:
        raise HTTPException(status_code=404, detail="Inspection not found")
    
    uploaded = []
    for file in files:
        file_id = f"DOC-{str(uuid.uuid4())[:8].upper()}"
        uploaded.append({
            "file_id": file_id,
            "filename": file.filename,
            "size": file.size,
            "content_type": file.content_type
        })
    
    inspections_db[inspection_id]["documents"].extend(uploaded)
    
    return {
        "inspection_id": inspection_id,
        "uploaded_documents": len(uploaded),
        "files": uploaded
    }


@router.post("/{inspection_id}/vision")
async def run_vision_analysis(inspection_id: str):
    """POST /inspection/{inspection_id}/vision - calls Member 1's Vision Service."""
    if inspection_id not in inspections_db:
        raise HTTPException(status_code=404, detail="Inspection not found")

    images = inspections_db[inspection_id]["images"]
    if not images:
        raise HTTPException(status_code=400, detail="No images uploaded for vision analysis")

    try:
        result = await vision_client.analyze_images(images)
    except VisionServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Stored in the exact shape of vehicle_schema_v1.json -> vision
    inspections_db[inspection_id]["vision_results"] = {
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
        "vision": inspections_db[inspection_id]["vision_results"],
    }


@router.post("/{inspection_id}/documents/extract")
def extract_documents(inspection_id: str):
    """
    Run Document AI for information extraction
    POST /inspection/{inspection_id}/documents/extract
    
    Triggered by Member 3 backend to call Member 2's Document AI Service
    """
    if inspection_id not in inspections_db:
        raise HTTPException(status_code=404, detail="Inspection not found")
    
    # TODO: Integration with Member 2's Document AI Service
    # Call: POST to document AI service with documents
    # Parse response and store in inspections_db[inspection_id]["document_results"]
    
    return {
        "inspection_id": inspection_id,
        "status": "document_extraction_started",
        "message": "Document extraction queued - Member 2 service integration pending"
    }


@router.get("/{inspection_id}")
def get_inspection_results(inspection_id: str):
    """
    Get current inspection results (combined Vehicle JSON)
    GET /inspection/{inspection_id}
    
    Returns the combined vehicle data from vision + document AI
    Follows the CarVal vehicle_schema_v1.json structure
    """
    if inspection_id not in inspections_db:
        raise HTTPException(status_code=404, detail="Inspection not found")
    
    # Build combined vehicle record following schema
    vehicle_record = {
        "schema_version": "1.0",
        "vehicle_id": inspection_id,
        "vehicle": {},
        "input_files": {
            "images": [{k: v for k, v in img.items() if k != "contents"}
                       for img in inspections_db[inspection_id]["images"]],
            "documents": inspections_db[inspection_id]["documents"]
        },
        "vision": inspections_db[inspection_id].get("vision_results", {}),
        "documents": inspections_db[inspection_id].get("document_results", {}),
        "vehicle_history": {},
        "valuation": {"status": "pending"},
        "discrepancies": [],
        "knowledge_retrieval": {"status": "pending"},
        "risk_assessment": {"status": "pending"},
        "llm_synthesis": {"status": "pending"},
        "final_report": {"status": "pending"},
        "pipeline_status": {
            "images_processed": len(inspections_db[inspection_id]["images"]) > 0,
            "documents_processed": len(inspections_db[inspection_id]["documents"]) > 0,
            "vision_completed": inspections_db[inspection_id].get("vision_results") is not None,
            "document_ai_completed": inspections_db[inspection_id].get("document_results") is not None,
            "valuation_completed": False,
            "discrepancy_completed": False,
            "rag_completed": False,
            "llm_completed": False,
            "report_completed": False
        }
    }
    
    return vehicle_record


@router.get("/{inspection_id}/report")
def get_final_report(inspection_id: str):
    """
    Get final evidence-backed report
    GET /inspection/{inspection_id}/report
    
    Available in Review 4 after LLM synthesis
    """
    if inspection_id not in inspections_db:
        raise HTTPException(status_code=404, detail="Inspection not found")
    
    return {
        "inspection_id": inspection_id,
        "status": "pending",
        "message": "Final report generation available in Review 4"
    }
