"""
Diagnostic (OBD-II scanner photo) endpoints
Lives next to the inspection routes and shares the same in-memory store.

POST /inspection/{id}/diagnostics/photos                    upload scanner-screen photo(s)
POST /inspection/{id}/diagnostics/extract/{evidence_id}     run OCR -> proposals (needs user review)
POST /inspection/{id}/diagnostics/confirm/{evidence_id}     save what the USER confirmed
GET  /inspection/{id}/diagnostics                           engine_assessment for this inspection
GET  /inspection/{id}/diagnostics/photos/{evidence_id}      the stored photo (for the review screen)

Diagnostic photos are stored in inspection["diagnostics"], NOT in inspection["images"],
so they can never be sent to the damage-detection (YOLO) pipeline by accident.
"""

import logging
import re
import uuid
from datetime import datetime
from io import BytesIO
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image

from app.api.inspection import inspections_db
from app.core.config import settings
from app.schemas.diagnostics import DiagnosticConfirmRequest
from app.services.diagnostic_assessment import build_engine_assessment, public_evidence
from app.services.diagnostic_ocr import DiagnosticOCRError, extract_diagnostic_text
from app.services.dtc_catalog import lookup_code

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inspection", tags=["diagnostics"])

IMAGE_EXTS = (".jpg", ".jpeg", ".png")
DTC_STRICT_FULL = re.compile(r"^[PBCU][0-3][0-9A-F]{3}$")


def _get_inspection(inspection_id: str) -> dict:
    if inspection_id not in inspections_db:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return inspections_db[inspection_id]


def _get_evidence(inspection: dict, evidence_id: str) -> dict:
    for ev in inspection.setdefault("diagnostics", []):
        if ev["evidence_id"] == evidence_id:
            return ev
    raise HTTPException(status_code=404, detail="Diagnostic evidence not found")


@router.post("/{inspection_id}/diagnostics/photos")
async def upload_diagnostic_photos(inspection_id: str, files: List[UploadFile] = File(...)):
    inspection = _get_inspection(inspection_id)
    max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
    stored = []

    for file in files:
        name = file.filename or "scanner_photo"
        if not name.lower().endswith(IMAGE_EXTS):
            raise HTTPException(status_code=400, detail=f"{name}: only .jpg, .jpeg, .png are accepted")
        contents = await file.read()
        if len(contents) > max_bytes:
            raise HTTPException(status_code=400, detail=f"{name}: exceeds {settings.MAX_IMAGE_SIZE_MB} MB limit")
        try:
            Image.open(BytesIO(contents)).verify()  # rejects files that are not real images
        except Exception:
            raise HTTPException(status_code=400, detail=f"{name}: not a valid image file")

        stored.append({
            "evidence_id": f"DIA-{str(uuid.uuid4())[:8].upper()}",
            "source_type": "scanner_screen_photo",
            "source_image_id": f"DGN-{str(uuid.uuid4())[:8].upper()}",
            "uploaded_filename": name,
            "content_type": file.content_type,
            "size": len(contents),
            "uploaded_at": datetime.now().isoformat(),
            "contents": contents,
            "ocr_status": "uploaded",
            "ocr_error": None,
            "ocr_text": None,
            "ocr_proposals": None,          # raw OCR output kept for the audit trail
            "extracted_codes": [],          # replaced by user-confirmed values on confirm
            "extracted_readings": [],
            "scan_context": "unknown",
            "no_codes_visible": False,
            "captured_at": None,
            "confirmed_at": None,
            "notes": [],
        })

    inspection.setdefault("diagnostics", []).extend(stored)
    return {
        "inspection_id": inspection_id,
        "uploaded": len(stored),
        "evidence": [public_evidence(e) for e in stored],
    }


# Plain `def` (not async): OCR is CPU work, FastAPI runs it in a worker thread so the server stays responsive.
@router.post("/{inspection_id}/diagnostics/extract/{evidence_id}")
def extract_diagnostic(inspection_id: str, evidence_id: str):
    inspection = _get_inspection(inspection_id)
    ev = _get_evidence(inspection, evidence_id)
    if ev["ocr_status"] == "confirmed":
        raise HTTPException(status_code=409, detail="Evidence is already confirmed")

    try:
        result = extract_diagnostic_text(ev["contents"])
    except DiagnosticOCRError as e:
        logger.warning(f"Diagnostic OCR failed for {evidence_id}: {e}")
        ev["ocr_status"] = "ocr_failed"
        ev["ocr_error"] = str(e)
        return {"evidence": public_evidence(ev), "review_required": True, "manual_entry_required": True}

    ev["ocr_status"] = "needs_user_confirmation"
    ev["ocr_error"] = None
    ev["ocr_text"] = result["ocr_text"]
    ev["scan_context"] = result["scan_context"]
    ev["ocr_proposals"] = {
        "codes": result["proposed_codes"],
        "uncertain_codes": result["uncertain_codes"],
        "readings": result["proposed_readings"],
        "status_keywords_seen": result["status_keywords_seen"],
    }
    # current (unconfirmed) working copy, in the schema shape
    ev["extracted_codes"] = [
        {"code": c["code"], "description": (lookup_code(c["code"]) or {}).get("description"),
         "scanner_status": "unknown", "ocr_confidence": c["ocr_confidence"], "user_confirmed": False}
        for c in result["proposed_codes"]
    ]
    ev["extracted_readings"] = result["proposed_readings"]
    return {"evidence": public_evidence(ev), "review_required": True, "manual_entry_required": False}


@router.post("/{inspection_id}/diagnostics/confirm/{evidence_id}")
def confirm_diagnostic(inspection_id: str, evidence_id: str, body: DiagnosticConfirmRequest):
    inspection = _get_inspection(inspection_id)
    ev = _get_evidence(inspection, evidence_id)

    proposals = {c["code"]: c for c in ((ev.get("ocr_proposals") or {}).get("codes") or [])}
    confirmed_codes, seen = [], set()
    for item in body.codes:
        code = item.code.strip().upper()
        if not DTC_STRICT_FULL.match(code):
            raise HTTPException(status_code=422, detail=f"'{item.code}' is not a valid DTC (example: P0100)")
        if code in seen:
            continue
        seen.add(code)
        info = lookup_code(code)
        proposed = proposals.get(code)
        confirmed_codes.append({
            "code": code,
            "description": (info or {}).get("description"),
            "in_catalogue": info is not None,   # False -> shown as "not in catalogue", never guessed
            "scanner_status": item.scanner_status,
            "ocr_confidence": proposed["ocr_confidence"] if proposed else None,
            "entry_source": "ocr_confirmed" if proposed else "user_added",
            "user_confirmed": True,
        })

    if not confirmed_codes and not body.no_codes_visible:
        raise HTTPException(status_code=422, detail="Add at least one code, or tick 'no readable code on this screen'")

    ev["extracted_codes"] = confirmed_codes
    ev["extracted_readings"] = [
        {"label": r.label.strip(), "value": r.value.strip(), "unit": r.unit, "context": r.context, "user_confirmed": True}
        for r in body.readings if r.label.strip() and r.value.strip()
    ]
    ev["scan_context"] = body.scan_context
    ev["no_codes_visible"] = body.no_codes_visible and not confirmed_codes
    ev["notes"] = [n.strip() for n in body.notes if n.strip()]
    ev["ocr_status"] = "confirmed"
    ev["confirmed_at"] = datetime.now().isoformat()

    return {"evidence": public_evidence(ev), "engine_assessment": build_engine_assessment(inspection)}


@router.get("/{inspection_id}/diagnostics")
def get_diagnostics(inspection_id: str):
    return build_engine_assessment(_get_inspection(inspection_id))


@router.get("/{inspection_id}/diagnostics/photos/{evidence_id}")
def get_diagnostic_photo(inspection_id: str, evidence_id: str):
    ev = _get_evidence(_get_inspection(inspection_id), evidence_id)
    return Response(content=ev["contents"], media_type=ev.get("content_type") or "image/jpeg")