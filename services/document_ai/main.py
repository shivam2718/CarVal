"""
Document AI Service - FastAPI
Member 2 - Document Extraction and OCR
Extracts structured information from RC, insurance, and service documents
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import pytesseract
from PIL import Image
import io
import json
import uuid
from datetime import datetime
import os

app = FastAPI(
    title="CarVal Document AI Service",
    description="OCR and document extraction for vehicle documents",
    version="0.1.0"
)


class DocumentField(BaseModel):
    """Extracted field from document"""
    name: str
    value: Optional[Any] = None
    confidence: float = 0.0


class RCResponse(BaseModel):
    """Registration Certificate extraction response"""
    document_type: str = "rc"
    extracted: bool
    confidence: float
    fields: Dict[str, Any]
    source_document_id: Optional[str] = None


class InsuranceResponse(BaseModel):
    """Insurance document extraction response"""
    document_type: str = "insurance"
    extracted: bool
    confidence: float
    fields: Dict[str, Any]
    source_document_id: Optional[str] = None


class ServiceBillResponse(BaseModel):
    """Service bill extraction response"""
    document_type: str = "service_bill"
    extracted: bool
    confidence: float
    fields: Dict[str, Any]
    source_document_id: Optional[str] = None


class DocumentExtractor:
    """
    OCR-based document extraction
    Uses Tesseract for text recognition and regex/pattern matching for field extraction
    """
    
    def __init__(self):
        self.base_confidence = 0.75  # Base confidence for extraction
    
    def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from image using Tesseract OCR"""
        try:
            print(f"[OCR] Opening image: {image_path}")
            image = Image.open(image_path)
            print(f"[OCR] Image size: {image.size}, mode: {image.mode}")
            
            # Preprocess image for better OCR
            text = pytesseract.image_to_string(image, config='--psm 6')
            print(f"[OCR] Extracted text length: {len(text)}")
            print(f"[OCR] Text preview: {text[:200]}")
            return text
        except Exception as e:
            print(f"[ERROR] Error extracting text: {e}")
            return ""
    
    def extract_rc_info(self, text: str) -> Dict[str, Any]:
        """
        Extract Registration Certificate fields from OCR text
        Uses multi-pattern matching for different state formats
        Returns per-field confidence scores (0.0-1.0)
        """
        import re
        
        # Initialize with None and confidence tracking
        fields = {
            "registration_number": None,
            "owner": None,
            "model": None,
            "manufacturing_year": None,
            "registration_year": None,
            "fuel_type": None,
            "engine_displacement_cc": None,
            "power_bhp": None,
            "transmission": None,
            "vin": None
        }
        
        field_confidence = {key: 0.0 for key in fields.keys()}
        
        # ========== REGISTRATION NUMBER ==========
        # Try multiple state formats (TN, DL, KA, MH, etc.)
        reg_patterns = [
            r'(?:Reg\.?\s*No\.?|Registration|Reg)[:\s]*([A-Z]{2}\s*[-]?\d{2}\s*[-]?[A-Z]{2}\s*[-]?\d{4})',
            r'\b([A-Z]{2})\s*[-]?\s*(\d{2})\s*[-]?\s*([A-Z]{2})\s*[-]?\s*(\d{4})\b',
            r'\b([A-Z]{2}\d{2}[A-Z]{2}\d{4})\b',  # Compact format
        ]
        
        for pattern in reg_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Extract registration number, cleaning up spaces/hyphens
                reg_num = match.group(1) if match.lastindex and match.lastindex >= 1 else match.group(0)
                reg_num = ''.join(reg_num.split())  # Remove spaces
                if re.match(r'^[A-Z]{2}\d{2}[A-Z]{2}\d{4}$', reg_num):
                    fields["registration_number"] = reg_num
                    field_confidence["registration_number"] = 0.95
                    break
        
        # ========== VIN/CHASSIS NUMBER ==========
        # Try different VIN patterns
        vin_patterns = [
            r'(?:Chassis|VIN|Chassis\s*No\.?)[:\s]*([A-HJ-NPR-Z0-9]{17})',
            r'\b([A-HJ-NPR-Z0-9]{17})\b',
        ]
        
        for pattern in vin_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                vin = match.group(1) if match.lastindex else match.group(0)
                if len(vin) == 17:
                    fields["vin"] = vin
                    field_confidence["vin"] = 0.90
                    break
        
        # ========== MANUFACTURING & REGISTRATION YEAR ==========
        # Look for year patterns (1900-2099)
        year_pattern = r'\b(1[89]\d{2}|20\d{2})\b'
        year_matches = re.findall(year_pattern, text)
        
        if year_matches:
            years = [int(y) for y in year_matches if 1900 <= int(y) <= 2050]
            years = list(dict.fromkeys(years))  # Remove duplicates, preserve order
            
            if len(years) >= 1:
                # First year is likely manufacturing year
                fields["manufacturing_year"] = years[0]
                field_confidence["manufacturing_year"] = 0.85
            
            if len(years) >= 2:
                # Second year is likely registration year
                fields["registration_year"] = years[1]
                field_confidence["registration_year"] = 0.80
        
        # ========== FUEL TYPE ==========
        fuel_keywords = {
            "petrol": [r'\bpetrol\b', r'\bbenzine\b', r'\bPETROL\b'],
            "diesel": [r'\bdiesel\b'],
            "cng": [r'\bCNG\b', r'\bcompressed\s+natural\s+gas\b'],
            "lpg": [r'\bLPG\b', r'\bliquified\s+petroleum\b'],
            "electric": [r'\belectric\b', r'\bEV\b'],
            "hybrid": [r'\bhybrid\b'],
        }
        
        for fuel_type, patterns in fuel_keywords.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    fields["fuel_type"] = fuel_type
                    field_confidence["fuel_type"] = 0.88
                    break
            if fields["fuel_type"]:
                break
        
        # ========== ENGINE DISPLACEMENT ==========
        engine_patterns = [
            r'(?:Engine|Displacement|cc)[:\s]*(\d{3,4})\s*cc',
            r'(\d{3,4})\s*(?:cc|CC)',
        ]
        
        for pattern in engine_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                cc = int(match.group(1))
                if 500 <= cc <= 7000:  # Reasonable range for cars
                    fields["engine_displacement_cc"] = cc
                    field_confidence["engine_displacement_cc"] = 0.92
                    break
        
        # ========== POWER (BHP) ==========
        power_patterns = [
            r'(?:Power|BHP|bhp)[:\s]*(\d{1,3})\s*(?:bhp|BHP)',
            r'(\d{1,3})\s*(?:bhp|BHP)',
        ]
        
        for pattern in power_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                bhp = int(match.group(1))
                if 40 <= bhp <= 400:  # Reasonable range
                    fields["power_bhp"] = bhp
                    field_confidence["power_bhp"] = 0.90
                    break
        
        # ========== TRANSMISSION ==========
        if re.search(r'\bautomatic\b|\bauto\b', text, re.IGNORECASE):
            fields["transmission"] = "automatic"
            field_confidence["transmission"] = 0.85
        elif re.search(r'\bmanual\b', text, re.IGNORECASE):
            fields["transmission"] = "manual"
            field_confidence["transmission"] = 0.85
        
        # ========== VEHICLE MODEL ==========
        # Comprehensive list of Indian car models
        model_keywords = {
            'swift': 0.95,
            'alto': 0.95,
            'celerio': 0.95,
            'baleno': 0.95,
            'brezza': 0.90,
            'vitara': 0.90,
            'ertiga': 0.90,
            'ciaz': 0.90,
            'fortuner': 0.95,
            'innova': 0.95,
            'city': 0.95,
            'accord': 0.90,
            'civic': 0.90,
            'amaze': 0.90,
            'figo': 0.95,
            'aspire': 0.90,
            'polo': 0.95,
            'vento': 0.90,
            'jetta': 0.90,
            'skoda': 0.85,
            'tata': 0.80,
            'xuv': 0.85,
            'nexon': 0.90,
            'harrier': 0.90,
            'bolero': 0.90,
            'mahindra': 0.80,
            'scorpio': 0.90,
            'xylo': 0.85,
            'hyundai': 0.80,
            'i20': 0.90,
            'creta': 0.90,
            'verna': 0.90,
            'kia': 0.80,
            'seltos': 0.85,
            'renault': 0.80,
            'duster': 0.85,
            'kwid': 0.85,
            'nissan': 0.80,
            'datsun': 0.80,
            'mg': 0.80,
            'hector': 0.85,
            'bmw': 0.85,
            'audi': 0.85,
            'mercedes': 0.85,
            'toyota': 0.80,
            'etios': 0.85,
            'maruti': 0.75,
            'pulsar': 0.85,
            'bajaj': 0.80,
        }
        
        for keyword, confidence in sorted(model_keywords.items(), key=lambda x: -x[1]):
            if keyword.lower() in text.lower():
                fields["model"] = keyword.title()
                field_confidence["model"] = confidence
                break
        
        # ========== OWNER NAME ==========
        # Try multiple owner patterns (different document formats)
        owner_patterns = [
            r'(?:Owner|Registered to|Proprietor|Owner\s*Name)[:\s]+([A-Z][A-Za-z\s\.,]+?)(?:\n|$)',
            r'(?:Name)[:\s]+([A-Z][A-Za-z\s\.,]+?)(?:\n|$)',
        ]
        
        for pattern in owner_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                owner = match.group(1).strip()
                # Filter out common non-name strings
                if len(owner) > 2 and not re.search(r'(?:Government|Authority|Department)', owner, re.IGNORECASE):
                    fields["owner"] = owner
                    field_confidence["owner"] = 0.80
                    break
        
        return {
            "extracted_fields": fields,
            "field_confidence": field_confidence,
            "overall_confidence": sum(field_confidence.values()) / len(field_confidence) if field_confidence else 0.0
        }
    
    def extract_insurance_info(self, text: str) -> Dict[str, Any]:
        """Extract Insurance policy fields from OCR text"""
        import re
        
        fields = {
            "policy_number": None,
            "valid_from": None,
            "valid_until": None,
            "insurer_name": None,
            "claims": []
        }
        
        # Policy number (alphanumeric, usually 10-20 chars)
        policy_pattern = r'policy\s*(?:number|no\.?)[:\s]+([A-Z0-9\-]{8,20})'
        policy_match = re.search(policy_pattern, text, re.IGNORECASE)
        if policy_match:
            fields["policy_number"] = policy_match.group(1).strip()
        
        # Valid dates (DD-MM-YYYY or YYYY-MM-DD)
        date_pattern = r'(\d{1,4}[-/]\d{1,2}[-/]\d{2,4})'
        date_matches = re.findall(date_pattern, text)
        if len(date_matches) >= 1:
            fields["valid_from"] = date_matches[0]
        if len(date_matches) >= 2:
            fields["valid_until"] = date_matches[1]
        
        # Insurer names
        insurers = ['bajaj', 'hdfc', 'icici', 'tata', 'reliance', 'iffco', 
                   'national', 'united', 'oriental', 'edelweiss']
        for insurer in insurers:
            if insurer.lower() in text.lower():
                fields["insurer_name"] = insurer.title()
                break
        
        # Claims (look for claim amount patterns)
        claim_pattern = r'claim[:\s]+₹?(\d+(?:,\d+)*)'
        claim_matches = re.findall(claim_pattern, text, re.IGNORECASE)
        if claim_matches:
            for amount_str in claim_matches:
                amount = int(amount_str.replace(',', ''))
                fields["claims"].append({
                    "claim_id": f"CLM-{str(uuid.uuid4())[:8].upper()}",
                    "amount": amount,
                    "description": "Claim amount found in document"
                })
        
        return fields
    
    def extract_service_history(self, text: str) -> List[Dict[str, Any]]:
        """Extract service bill information from OCR text"""
        import re
        
        service_records = []
        
        # Service date pattern
        date_pattern = r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
        date_matches = re.findall(date_pattern, text)
        
        # Mileage pattern (e.g., 45000 km)
        mileage_pattern = r'(\d{4,6})\s*km'
        mileage_matches = re.findall(mileage_pattern, text, re.IGNORECASE)
        
        # Service center (look for common patterns)
        service_center_pattern = r'service\s*(?:center|centre)[:\s]+([^\n]{1,50})'
        service_center_match = re.search(service_center_pattern, text, re.IGNORECASE)
        
        # Cost pattern (e.g., ₹2500 or Rs. 2500 or Total Cost: 1400)
        cost_pattern = r'(?:₹|rs\.?|total\s*cost?)[:\s]*₹?(\d+(?:,\d+)*)'
        cost_matches = re.findall(cost_pattern, text, re.IGNORECASE)
        # Take the highest cost value (usually the total)
        final_cost = None
        if cost_matches:
            costs = [int(m.replace(',', '')) for m in cost_matches]
            final_cost = max(costs) if costs else None
        
        # Work done keywords
        work_keywords = ['oil change', 'filter replacement', 'battery', 'spark plug',
                        'coolant', 'brake fluid', 'tire rotation', 'alignment',
                        'service', 'maintenance', 'inspection', 'replacement']
        
        work_done = []
        for keyword in work_keywords:
            if keyword.lower() in text.lower():
                work_done.append(keyword.title())
        
        # Create service record
        if date_matches or mileage_matches or service_center_match or cost_matches:
            service_record = {
                "service_id": f"SRV-{str(uuid.uuid4())[:8].upper()}",
                "date": date_matches[0] if date_matches else None,
                "mileage_km": int(mileage_matches[0]) if mileage_matches else None,
                "service_center": service_center_match.group(1).strip() if service_center_match else None,
                "work_done": work_done,
                "parts_replaced": [],
                "cost": final_cost,
                "currency": "INR"
            }
            service_records.append(service_record)
        
        return service_records


# Initialize extractor
extractor = DocumentExtractor()


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Document AI",
        "version": "0.1.0"
    }


@app.post("/extract", response_model=Dict[str, Any])
async def extract_document(file: UploadFile = File(...), document_type: str = "rc"):
    """
    Extract information from uploaded document
    
    Args:
        file: PDF or image file
        document_type: "rc", "insurance", or "service_bill"
    
    Returns:
        Extracted fields with confidence scores
    """
    try:
        # Save uploaded file
        import tempfile
        doc_id = f"DOC-{str(uuid.uuid4())[:8].upper()}"
        
        # Handle different file types
        if file.filename.lower().endswith('.pdf'):
            # Convert PDF to image (simplified - would need pdf2image)
            # For now, return mock response
            extracted_text = f"[PDF Document: {file.filename}]"
        else:
            # Save image file to temp directory
            content = await file.read()
            image = Image.open(io.BytesIO(content))
            
            # Use system temp directory (Windows/Linux compatible)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                temp_path = tmp_file.name
                image.save(temp_path)
            
            extracted_text = extractor.extract_text_from_image(temp_path)
            
            # Clean up temp file
            import os
            try:
                os.remove(temp_path)
            except:
                pass
        
        # Extract based on document type
        if document_type.lower() == "rc":
            print(f"\n[EXTRACT RC] File: {file.filename}")
            print(f"[EXTRACT RC] Extracted text length: {len(extracted_text)}")
            print(f"[EXTRACT RC] Text preview: {extracted_text[:300]}\n")
            
            extraction_result = extractor.extract_rc_info(extracted_text)
            fields = extraction_result["extracted_fields"]
            field_confidence = extraction_result["field_confidence"]
            overall_confidence = extraction_result["overall_confidence"]
            
            print(f"[EXTRACT RC] Fields: {fields}")
            print(f"[EXTRACT RC] Overall confidence: {overall_confidence}\n")
            
            response = {
                "document_type": "rc",
                "extracted": any(v is not None for v in fields.values()),
                "confidence": overall_confidence,
                "fields": fields,
                "field_confidence": field_confidence,  # Per-field confidence scores
                "source_document_id": doc_id
            }
        
        elif document_type.lower() == "insurance":
            fields = extractor.extract_insurance_info(extracted_text)
            confidence = 0.88
            response = {
                "document_type": "insurance",
                "extracted": True,
                "confidence": confidence,
                "fields": fields,
                "raw_text": extracted_text,  # Always include raw text for debugging
                "source_document_id": doc_id
            }
        
        elif document_type.lower() == "service_bill":
            fields = extractor.extract_service_history(extracted_text)
            confidence = 0.85
            response = {
                "document_type": "service_bill",
                "extracted": True,
                "confidence": confidence,
                "fields": {
                    "service_records": fields,
                    "raw_text": extracted_text[:500]  # First 500 chars for verification
                },
                "source_document_id": doc_id
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown document type: {document_type}")
        
        return response
    
    except Exception as e:
        import traceback
        print(f"\n[ERROR] Exception in extract_document:")
        print(f"[ERROR] Type: {type(e).__name__}")
        print(f"[ERROR] Message: {str(e)}")
        print(f"[ERROR] Traceback:\n{traceback.format_exc()}\n")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@app.post("/extract/rc")
async def extract_rc(file: UploadFile = File(...)):
    """Extract RC (Registration Certificate) document"""
    return await extract_document(file, "rc")


@app.post("/extract/insurance")
async def extract_insurance(file: UploadFile = File(...)):
    """Extract Insurance document"""
    return await extract_document(file, "insurance")


@app.post("/extract/service")
async def extract_service_bill(file: UploadFile = File(...)):
    """Extract Service Bill document"""
    return await extract_document(file, "service_bill")


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "CarVal Document AI",
        "version": "0.1.0",
        "endpoints": {
            "health": "/health",
            "extract": "/extract",
            "extract_rc": "/extract/rc",
            "extract_insurance": "/extract/insurance",
            "extract_service": "/extract/service"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True
    )
