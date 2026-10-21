"""
Inspection (core) endpoints
Creates an inspection and returns the combined Vehicle JSON (vehicle_schema_v1.json).
Each module has its own router: vision.py, documents.py, obd.py, valuation.py.

POST /inspection          create an inspection
GET  /inspection/{id}     combined Vehicle JSON
GET  /inspection/{id}/report   (Review 4)
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.api.valuation import VALUATION_STUB
from app.core.store import inspections_db
from app.services.diagnostic_assessment import build_engine_assessment

router = APIRouter(prefix="/inspection", tags=["inspection"])


@router.post("")
def create_inspection():
    inspection_id = f"INS-{str(uuid.uuid4())[:8].upper()}"
    inspections_db[inspection_id] = {
        "id": inspection_id,
        "created_at": datetime.now().isoformat(),
        "status": "created",
        "images": [],
        "documents": [],
        "diagnostics": [],
        "vision_results": None,
        "document_results": None,
    }
    return {
        "inspection_id": inspection_id,
        "status": "created",
        "created_at": inspections_db[inspection_id]["created_at"],
    }


def _vehicle_summary(document_results: dict | None) -> dict:
    """Vehicle block of the common JSON, filled from the RC when one was extracted."""
    docs = document_results or {}
    fields = (docs.get("rc") or {}).get("fields") or {}
    insurance = docs.get("insurance") or {}
    owner = fields.get("owner")
    insured = insurance.get("insured_name")
    # OCR sometimes glues words together ("KUMARSAMPLE"); when the insurance policy has the same name, use its spelling
    if owner and insured and owner.replace(" ", "").lower() == insured.replace(" ", "").lower():
        owner = insured
    return {
        "registration_number": fields.get("registration_number") or insurance.get("registration_number"),
        "vin": fields.get("vin"),
        "make": fields.get("make"),
        "model": fields.get("model"),
        "manufacturing_year": fields.get("manufacturing_year"),
        "registration_year": fields.get("registration_year"),
        "fuel_type": fields.get("fuel_type"),
        "transmission": fields.get("transmission"),
        "owner": owner or insured,
        "engine": {
            "displacement_cc": fields.get("engine_displacement_cc"),
            "power_bhp": fields.get("power_bhp"),
        },
    }


@router.get("/{inspection_id}")
def get_inspection_results(inspection_id: str):
    if inspection_id not in inspections_db:
        raise HTTPException(status_code=404, detail="Inspection not found")
    ins = inspections_db[inspection_id]
    document_results = ins.get("document_results")
    strip = lambda items: [{k: v for k, v in i.items() if k != "contents"} for i in items]  # noqa: E731

    return {
        "schema_version": "1.0",
        "vehicle_id": inspection_id,
        "vehicle": _vehicle_summary(document_results),
        "input_files": {"images": strip(ins["images"]), "documents": strip(ins["documents"])},
        "vision": ins.get("vision_results"),
        "documents": document_results,
        "vehicle_history": {},
        "valuation": VALUATION_STUB,
        "discrepancies": [],
        "knowledge_retrieval": {"status": "pending"},
        "risk_assessment": {"status": "pending"},
        "engine_assessment": build_engine_assessment(ins),
        "llm_synthesis": {"status": "pending"},
        "final_report": {"status": "pending"},
        "pipeline_status": {
            "images_processed": len(ins["images"]) > 0,
            "documents_processed": len(ins["documents"]) > 0,
            "vision_completed": ins.get("vision_results") is not None,
            "document_ai_completed": document_results is not None,
            "valuation_completed": False,
            "discrepancy_completed": False,
            "rag_completed": False,
            "llm_completed": False,
            "report_completed": False,
            "diagnostics_confirmed": any(e.get("ocr_status") == "confirmed" for e in ins.get("diagnostics", [])),
        },
    }


@router.get("/{inspection_id}/report")
def get_final_report(inspection_id: str):
    if inspection_id not in inspections_db:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return {"inspection_id": inspection_id, "status": "pending",
            "message": "Final report generation available in Review 4"}
