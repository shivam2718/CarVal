"""
Inspection Endpoints
Member 3 - Backend Integration
Orchestrates Vision Service and Document AI
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import json
import uuid
from datetime import datetime
import asyncio
import logging
from app.services.document_client import DocumentAIClient
from app.services.date_matcher import DateMatcher

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/inspection",
    tags=["inspection"]
)

# Temporary in-memory storage for Review 2 (replace with DB in Review 3)
inspections_db = {}
document_client = DocumentAIClient()


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
    """
    Upload car images for inspection
    POST /inspection/{inspection_id}/images
    
    Args:
        inspection_id: Inspection ID from create_inspection
        files: Car images (JPG, PNG)
    """
    if inspection_id not in inspections_db:
        raise HTTPException(status_code=404, detail="Inspection not found")
    
    uploaded = []
    for file in files:
        file_id = f"IMG-{str(uuid.uuid4())[:8].upper()}"
        uploaded.append({
            "file_id": file_id,
            "filename": file.filename,
            "size": file.size,
            "content_type": file.content_type
        })
    
    inspections_db[inspection_id]["images"].extend(uploaded)
    
    return {
        "inspection_id": inspection_id,
        "uploaded_images": len(uploaded),
        "files": uploaded
    }


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
        # Read file contents into memory
        file_contents = await file.read()
        
        uploaded.append({
            "file_id": file_id,
            "filename": file.filename,
            "size": file.size,
            "content_type": file.content_type,
            "contents": file_contents  # Store actual file bytes
        })
    
    inspections_db[inspection_id]["documents"].extend(uploaded)
    
    return {
        "inspection_id": inspection_id,
        "uploaded_documents": len(uploaded),
        "files": [
            {
                "file_id": f["file_id"],
                "filename": f["filename"],
                "size": f["size"]
            }
            for f in uploaded
        ]
    }


@router.post("/{inspection_id}/vision")
def run_vision_analysis(inspection_id: str):
    """
    Run Vision Service for damage detection
    POST /inspection/{inspection_id}/vision
    
    Triggered by Member 3 backend to call Member 1's Vision Service
    """
    if inspection_id not in inspections_db:
        raise HTTPException(status_code=404, detail="Inspection not found")
    
    # TODO: Integration with Member 1's Vision Service
    # Call: POST to vision service with images
    # Parse response and store in inspections_db[inspection_id]["vision_results"]
    
    return {
        "inspection_id": inspection_id,
        "status": "vision_analysis_started",
        "message": "Vision analysis queued - Member 1 service integration pending"
    }


@router.post("/{inspection_id}/documents/extract")
async def extract_documents(inspection_id: str):
    """
    Run Document AI for information extraction
    POST /inspection/{inspection_id}/documents/extract
    
    Triggered by Member 3 backend to call Member 2's Document AI Service
    Processes all uploaded documents and extracts structured data
    """
    if inspection_id not in inspections_db:
        raise HTTPException(status_code=404, detail="Inspection not found")
    
    documents = inspections_db[inspection_id]["documents"]
    
    if not documents:
        raise HTTPException(status_code=400, detail="No documents uploaded for extraction")
    
    # Initialize results structure
    extraction_results = {
        "rc": None,
        "insurance": None,
        "service": None,
        "extracted_documents": []
    }
    
    # Process each document
    for doc in documents:
        filename_lower = doc["filename"].lower()
        file_contents = doc["contents"]
        
        logger.info(f"Processing document: {doc['filename']}")
        
        # Identify document type based on filename
        doc_type = "unknown"
        if "rc" in filename_lower or "registration" in filename_lower:
            doc_type = "rc"
        elif "insurance" in filename_lower or "policy" in filename_lower:
            doc_type = "insurance"
        elif "service" in filename_lower or "bill" in filename_lower:
            doc_type = "service"
        
        logger.info(f"Identified document type: {doc_type}")
        
        # Extract based on identified type
        if doc_type == "rc":
            try:
                logger.info(f"Extracting RC from {doc['filename']}")
                result = await document_client.extract_rc_info(doc["filename"], file_contents)
                logger.info(f"RC extraction result - extracted: {result.get('extracted')}, fields count: {len(result.get('fields', {}))}")
                # Store result regardless of extraction flag for debugging
                extraction_results["rc"] = {
                    "extracted": result.get("extracted", False),
                    "fields": result.get("fields", {}),
                    "field_confidence": result.get("field_confidence", {}),
                    "confidence": result.get("confidence", 0.0)
                }
                logger.info(f"RC extraction result stored")
            except Exception as e:
                logger.error(f"Error extracting RC: {e}", exc_info=True)
        
        elif doc_type == "insurance":
            try:
                logger.info(f"Extracting insurance from {doc['filename']}")
                result = await document_client.extract_insurance_info(doc["filename"], file_contents)
                logger.info(f"Insurance extraction result - extracted: {result.get('extracted')}")
                logger.info(f"Full insurance result: {json.dumps(result, default=str)}")
                # Store result - force extracted to True for testing
                extraction_results["insurance"] = {
                    "extracted": True,  # Force True for testing
                    "policy_number": result.get("policy_number"),
                    "valid_from": result.get("valid_from"),
                    "valid_until": result.get("valid_until"),
                    "claims": result.get("claims", []),
                    "confidence": result.get("confidence", 0.0),
                    "raw_text": result.get("raw_text", "")  # Include raw OCR text
                }
                logger.info(f"Insurance extraction result stored (forced extracted=True)")
            except Exception as e:
                logger.error(f"Error extracting insurance: {e}", exc_info=True)
        
        elif doc_type == "service":
            try:
                logger.info(f"Extracting service from {doc['filename']}")
                result = await document_client.extract_service_info(doc["filename"], file_contents)
                logger.info(f"Service extraction result - extracted: {result.get('extracted')}, records: {len(result.get('service_records', []))}")
                # Store result regardless of extraction flag for debugging
                extraction_results["service"] = {
                    "extracted": result.get("extracted", True),
                    "service_records": result.get("service_records", []),
                    "confidence": result.get("confidence", 0.0)
                }
                logger.info(f"Service extraction result stored")
            except Exception as e:
                logger.error(f"Error extracting service: {e}", exc_info=True)
        
        else:
            logger.warning(f"Unknown document type for {doc['filename']}, skipping")
    
    # Store results in database
    inspections_db[inspection_id]["document_results"] = extraction_results
    
    logger.info(f"Final extraction results for {inspection_id}: {json.dumps(extraction_results, default=str, indent=2)}")
    
    return {
        "inspection_id": inspection_id,
        "status": "document_extraction_completed",
        "documents_processed": len(documents),
        "results": extraction_results
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
    document_results = inspections_db[inspection_id].get("document_results")
    
    vehicle_record = {
        "schema_version": "1.0",
        "vehicle_id": inspection_id,
        "vehicle": {},
        "input_files": {
            "images": [
                {k: v for k, v in img.items() if k != "contents"}
                for img in inspections_db[inspection_id]["images"]
            ],
            "documents": [
                {k: v for k, v in doc.items() if k != "contents"}
                for doc in inspections_db[inspection_id]["documents"]
            ]
        },
        "vision": inspections_db[inspection_id].get("vision_results"),
        "documents": document_results,
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
            "document_ai_completed": document_results is not None,
            "valuation_completed": False,
            "discrepancy_completed": False,
            "rag_completed": False,
            "llm_completed": False,
            "report_completed": False
        }
    }
    
    return vehicle_record


@router.post("/{inspection_id}/verify-fields")
async def verify_fields(inspection_id: str, user_fields: dict):
    """
    Verify that user-entered field values exist in uploaded documents
    POST /inspection/{inspection_id}/verify-fields
    
    user_fields = {
        "policy_number": "POL-12345",
        "owner_name": "John Doe",
        "registration_number": "DL-01-AB-1234"
    }
    
    Returns verification results for each field
    """
    if inspection_id not in inspections_db:
        raise HTTPException(status_code=404, detail="Inspection not found")
    
    documents = inspections_db[inspection_id]["documents"]
    
    if not documents:
        raise HTTPException(status_code=400, detail="No documents uploaded")
    
    logger.info(f"Verifying {len(user_fields)} fields against {len(documents)} documents")
    
    # Extract text from all documents using Tesseract
    all_extracted_text = ""
    for doc in documents:
        try:
            import pytesseract
            from PIL import Image
            import io
            
            logger.info(f"Extracting text from {doc['filename']}")
            image = Image.open(io.BytesIO(doc["contents"]))
            extracted_text = pytesseract.image_to_string(image)
            all_extracted_text += " " + extracted_text
            logger.info(f"Extracted {len(extracted_text)} characters")
        except Exception as e:
            logger.error(f"Error extracting text from {doc['filename']}: {e}")
    
    # Make case-insensitive for matching
    all_extracted_text_lower = all_extracted_text.lower()
    
    logger.info(f"Total extracted text length: {len(all_extracted_text)} characters")
    
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
            # Use simple case-insensitive string matching for non-date fields
            found = str(field_value).lower() in all_extracted_text_lower
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
        "extracted_text_preview": all_extracted_text[:500]  # Store first 500 chars for debug
    }
    
    logger.info(f"Verification complete: all_matched={all_matched}")
    
    return {
        "status": "completed",
        "all_matched": all_matched,
        "verification_results": verification_results,
        "message": "✅ All fields found in document!" if all_matched else "⚠️ Some fields not found. Please upload a clearer image."
    }


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
