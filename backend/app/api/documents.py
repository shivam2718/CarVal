"""
Documents module (RC, insurance, service bills, odometer photo)

POST /inspection/{id}/documents            upload documents, each tagged with doc_type
POST /inspection/{id}/documents/extract    run Document AI on the uploaded documents
POST /inspection/{id}/documents/verify     check user-entered values against the documents
GET  /inspection/{id}/documents            uploaded files + extraction results
"""

import json
import logging
import re
import uuid
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.config import settings
from app.core.store import inspections_db
from app.services.date_matcher import DateMatcher
from app.services.document_client import DocumentAIClient, DocumentAIError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inspection/{inspection_id}/documents", tags=["documents"])

document_client = DocumentAIClient()

DOC_TYPES = ("rc", "insurance", "service", "odometer")
DOC_EXTS = (".pdf", ".jpg", ".jpeg", ".png")


def _get_inspection(inspection_id: str) -> dict:
    if inspection_id not in inspections_db:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return inspections_db[inspection_id]


def _guess_doc_type(filename: str) -> str:
    """Only used when the client did not say what the document is."""
    name = filename.lower()
    if "odometer" in name:
        return "odometer"
    if "insurance" in name or "policy" in name:
        return "insurance"
    if "service" in name or "bill" in name or "invoice" in name:
        return "service"
    if re.search(r"(^|[^a-z])rc([^a-z]|$)", name) or "registration" in name:
        return "rc"
    return "unknown"


@router.post("")
async def upload_documents(
    inspection_id: str,
    files: List[UploadFile] = File(...),
    doc_type: Optional[str] = Form(None),
    replace: bool = Form(False),
):
    """
    Upload documents. `doc_type` (rc | insurance | service | odometer) says what they are.
    `replace=true` first removes earlier uploads of the same doc_type (re-uploading a corrected file).
    """
    inspection = _get_inspection(inspection_id)
    if doc_type is not None and doc_type not in DOC_TYPES:
        raise HTTPException(status_code=400, detail=f"doc_type must be one of: {', '.join(DOC_TYPES)}")

    max_bytes = settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024
    uploaded = []
    for file in files:
        name = file.filename or "document"
        if not name.lower().endswith(DOC_EXTS):
            raise HTTPException(status_code=400, detail=f"{name}: only .pdf, .jpg, .jpeg, .png are accepted")
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail=f"{name}: file is empty")
        if len(contents) > max_bytes:
            raise HTTPException(status_code=400, detail=f"{name}: exceeds {settings.MAX_DOCUMENT_SIZE_MB} MB limit")
        uploaded.append({
            "file_id": f"DOC-{str(uuid.uuid4())[:8].upper()}",
            "filename": name,
            "size": len(contents),
            "content_type": file.content_type,
            "doc_type": doc_type or _guess_doc_type(name),
            "contents": contents,
        })

    if replace and doc_type:
        inspection["documents"] = [d for d in inspection["documents"] if d.get("doc_type") != doc_type]
    inspection["documents"].extend(uploaded)
    return {
        "inspection_id": inspection_id,
        "uploaded_documents": len(uploaded),
        "files": [{k: v for k, v in f.items() if k != "contents"} for f in uploaded],
    }


@router.get("")
def get_documents(inspection_id: str):
    inspection = _get_inspection(inspection_id)
    return {
        "inspection_id": inspection_id,
        "files": [{k: v for k, v in d.items() if k != "contents"} for d in inspection["documents"]],
        "results": inspection.get("document_results"),
    }


@router.post("/extract")
async def extract_documents(inspection_id: str):
    """Run Document AI on every uploaded RC / insurance / service document."""
    inspection = _get_inspection(inspection_id)
    documents = [d for d in inspection["documents"] if d.get("doc_type") != "odometer"]
    if not documents:
        raise HTTPException(status_code=400, detail="No RC, insurance or service documents uploaded")

    results = {"rc": None, "insurance": None, "service": None, "errors": [], "extracted_documents": []}
    service_records: list = []
    service_confidences: list = []
    service_sources: list = []

    for doc in documents:
        doc_type, name = doc["doc_type"], doc["filename"]
        if doc_type not in ("rc", "insurance", "service"):
            results["errors"].append({"file_id": doc["file_id"], "filename": name,
                                      "error": "Document type is unknown - upload it under RC, Insurance or Service bill"})
            continue
        try:
            if doc_type == "rc":
                r = await document_client.extract_rc_info(name, doc["contents"])
                candidate = {k: r[k] for k in ("extracted", "fields", "field_confidence", "confidence")}
                candidate["source_document_ids"] = [doc["file_id"]]
                # several RC files: keep the one that gave the best result
                if results["rc"] is None or candidate["confidence"] > results["rc"]["confidence"]:
                    results["rc"] = candidate
            elif doc_type == "insurance":
                r = await document_client.extract_insurance_info(name, doc["contents"])
                candidate = {k: r[k] for k in ("extracted", "policy_number", "valid_from", "valid_until",
                                               "insurer_name", "insured_name", "registration_number", "idv", "claims",
                                               "confidence", "raw_text")}
                candidate["source_document_ids"] = [doc["file_id"]]
                if results["insurance"] is None or candidate["confidence"] > results["insurance"]["confidence"]:
                    results["insurance"] = candidate
            else:
                r = await document_client.extract_service_info(name, doc["contents"])
                for rec in r["service_records"]:
                    service_records.append({**rec, "source_document_ids": [doc["file_id"]]})
                service_confidences.append(r["confidence"])
                service_sources.append(doc["file_id"])
            results["extracted_documents"].append({"file_id": doc["file_id"], "filename": name,
                                                   "doc_type": doc_type, "extracted": bool(r["extracted"])})
        except DocumentAIError as e:
            logger.error("Document AI failed for %s: %s", name, e)
            results["errors"].append({"file_id": doc["file_id"], "filename": name, "error": str(e)})

    if service_sources:
        results["service"] = {
            "extracted": len(service_records) > 0,
            "service_records": service_records,
            "confidence": sum(service_confidences) / len(service_confidences),
            "source_document_ids": service_sources,
        }

    if not results["extracted_documents"]:
        # every document failed: surface the reason instead of pretending it worked
        raise HTTPException(status_code=502, detail="; ".join(e["error"] for e in results["errors"]))

    inspection["document_results"] = results
    return {
        "inspection_id": inspection_id,
        "status": "document_extraction_completed",
        "documents_processed": len(results["extracted_documents"]),
        "results": results,
    }


@router.post("/verify")
async def verify_fields(inspection_id: str, user_fields: dict):
    """
    Verify that user-entered field values exist in uploaded documents
    POST /inspection/{inspection_id}/documents/verify
    
    user_fields = {
        "policy_number": "POL-12345",
        "owner_name": "John Doe",
        "registration_number": "DL-01-AB-1234"
    }
    
    Returns verification results for each field
    """
    _get_inspection(inspection_id)

    # Accept both the original flat fields object and a scoped payload from the UI.
    document_ids = user_fields.get("document_ids") if isinstance(user_fields, dict) else None
    if isinstance(user_fields, dict) and isinstance(user_fields.get("fields"), dict):
        user_fields = user_fields["fields"]
    else:
        user_fields = {k: v for k, v in user_fields.items() if k != "document_ids"}

    documents = inspections_db[inspection_id]["documents"]
    if document_ids:
        selected_ids = set(document_ids)
        documents = [doc for doc in documents if doc["file_id"] in selected_ids]
    
    if not documents:
        raise HTTPException(status_code=400, detail="No documents uploaded")
    
    logger.info(f"Verifying {len(user_fields)} fields against {len(documents)} documents")
    
    # Use the same Document AI OCR pipeline as document extraction so PDF/image
    # handling stays consistent and OCR failures are visible to the caller.
    all_extracted_text = ""
    extraction_errors = []
    odometer_candidates = []
    odometer_ocr_confidence = None
    odometer_ocr_engines = []
    is_odometer_verification = any("odometer" in str(name).lower() for name in user_fields)
    for doc in documents:
        try:
            logger.info(f"Extracting text from {doc['filename']} via Document AI")
            if is_odometer_verification:
                result = await document_client.extract_odometer(doc["filename"], doc["contents"])
            else:
                result = await document_client.extract_text(doc["filename"], doc["contents"])
            text = result.get("raw_text", "")
            if is_odometer_verification:
                odometer_candidates.extend(result.get("reading_candidates", []))
                odometer_ocr_confidence = result.get("ocr_confidence", result.get("confidence", 0.0))
                odometer_ocr_engines.extend(result.get("ocr_engines", []))
            if not text.strip():
                extraction_errors.append({"filename": doc["filename"], "error": result.get("error", "No text recognized")})
            all_extracted_text += "\n" + text
            logger.info("Extracted %s characters", len(text))
        except Exception as e:
            logger.error(f"Error extracting text from {doc['filename']}: {e}")
            extraction_errors.append({"filename": doc["filename"], "error": str(e)})

    if not all_extracted_text.strip() and not is_odometer_verification:
        raise HTTPException(
            status_code=503,
            detail={"message": "Document text could not be extracted", "errors": extraction_errors},
        )
    
    # Make case-insensitive for matching
    all_extracted_text_lower = all_extracted_text.lower()
    
    logger.info(f"Total extracted text length: {len(all_extracted_text)} characters")
    logger.info(f"Extracted text preview (first 500 chars):\n{all_extracted_text[:500]}")
    logger.info(f"Extracted text preview (last 500 chars):\n{all_extracted_text[-500:]}")
    
    # Verify each field
    verification_results = {}
    all_matched = True
    
    for field_name, field_value in user_fields.items():
        # Skip empty fields
        if field_value is None or field_value == "":
            verification_results[field_name] = {
                "value": field_value,
                "found": True,
                "message": "Skipped (empty)"
            }
            logger.info(f"Field {field_name}: Skipped (empty)")
            continue
        
        # Check if it's a date field and use smart date matching
        is_date_field = any(date_keyword in field_name.lower() for date_keyword in ['date', 'valid', 'from', 'until'])
        
        if is_date_field:
            # Use smart date matcher for date fields
            found = DateMatcher.date_exists_in_text(str(field_value), all_extracted_text)
            logger.info(f"Field {field_name} (DATE) = '{field_value}': {'FOUND' if found else 'NOT FOUND'}")
        else:
            # Use flexible fuzzy matching for non-date fields
            field_value_str = str(field_value).lower()
            
            # Remove special characters and extra spaces for comparison
            import re
            
            # Ignore formatting punctuation while keeping the full value intact.
            normalized_field = re.sub(r'[^a-z0-9]', '', field_value_str)
            normalized_text = re.sub(r'[^a-z0-9]', '', all_extracted_text_lower)
            
            if "odometer" in field_name.lower():
                # Only accept an exact, complete OCR reading from this image.
                expected_reading = ''.join(re.findall(r'\d+', field_value_str))
                text_readings = {re.sub(r'\D', '', str(item.get("value", ""))) for item in odometer_candidates}
                found = bool(expected_reading) and expected_reading in text_readings
            else:
                # Try exact match first, then match without punctuation/spacing.
                found = field_value_str in all_extracted_text_lower
                if not found and len(normalized_field) > 3:
                    found = normalized_field in normalized_text
            
            # Numeric fields must match a complete numeric token; substring
            # matches can incorrectly accept values such as 15 inside 2015.
            if not found and "odometer" not in field_name.lower() and any(num_field in field_name.lower() for num_field in ['year', 'cc', 'bhp', 'mileage']):
                field_numbers = re.findall(r'\d+', field_value_str)
                if field_numbers:
                    text_numbers = re.findall(r'\d+', all_extracted_text_lower)
                    found = all(number in text_numbers for number in field_numbers)
            
            logger.info(f"Field {field_name} = '{field_value}': {'FOUND' if found else 'NOT FOUND'}")
        
        verification_results[field_name] = {
            "value": field_value,
            "found": found,
            "message": "✅ Found in document" if found else "❌ Not found in document"
        }
        
        if not found:
            all_matched = False
    
    # Store results
    inspections_db[inspection_id]["field_verification"] = {
        "user_fields": user_fields,
        "verification_results": verification_results,
        "all_matched": all_matched,
        "extracted_text_preview": all_extracted_text[:500],
        "extraction_errors": extraction_errors,
    }
    
    logger.info(f"Verification complete: all_matched={all_matched}")
    
    return {
        "status": "completed",
        "all_matched": all_matched,
        "verification_results": verification_results,
        "extracted_text_preview": all_extracted_text[:500],
        "recognized_readings": list(dict.fromkeys(str(item.get("value", "")) for item in odometer_candidates if item.get("value"))),
        "ocr_confidence": odometer_ocr_confidence,
        "ocr_engines": list(dict.fromkeys(odometer_ocr_engines)),
        "extraction_errors": extraction_errors,
        "message": (
            "✅ Odometer reading verified!" if all_matched and is_odometer_verification
            else "❌ No matching odometer reading was recognized in the image." if is_odometer_verification
            else "✅ All fields found in document!" if all_matched
            else "⚠️ Some fields not found. Please upload a clearer image."
        )
    }
