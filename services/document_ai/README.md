# Document AI Service

**Owner**: Member 2 - Document AI

## Overview
Convert vehicle documents into structured information using OCR and extraction.

## Review 2 Objectives
- [ ] Collect/sample RC, insurance, and service-bill documents
- [ ] Build OCR pipeline
- [ ] Extract key fields:
  - Registration Number
  - Owner Name
  - Vehicle Model & Year
  - Mileage
  - Insurance Claims
  - Service History & Dates
  - Repair Information
- [ ] Define common document JSON schema
- [ ] Create document extraction API: `POST /documents/extract`
- [ ] Return structured vehicle/document information

## Expected Review 2 Demo
Upload a document → extracted vehicle information is displayed on the dashboard.

## API Contract

### POST /documents/extract

Extract information from a vehicle document.

**Request:**
```json
{
  "document_path": "path/to/document.pdf",
  "document_type": "rc"  // Options: "rc", "insurance", "service_bill"
}
```

**Response (RC):**
```json
{
  "document_type": "rc",
  "extracted": true,
  "confidence": 0.92,
  "fields": {
    "registration_number": "DL-01-AB-1234",
    "owner": "John Doe",
    "model": "Maruti Swift",
    "manufacturing_year": 2015,
    "registration_year": 2015,
    "fuel_type": "petrol",
    "engine_displacement_cc": 1200,
    "transmission": "manual"
  }
}
```

**Response (Insurance):**
```json
{
  "document_type": "insurance",
  "extracted": true,
  "confidence": 0.88,
  "fields": {
    "policy_number": "POL-123456789",
    "valid_from": "2023-01-01",
    "valid_until": "2024-12-31",
    "claims": [
      {
        "claim_id": "CLM-001",
        "date": "2023-06-15",
        "amount": 50000,
        "description": "Accident damage"
      }
    ]
  }
}
```

**Response (Service Bill):**
```json
{
  "document_type": "service_bill",
  "extracted": true,
  "confidence": 0.85,
  "fields": {
    "service_date": "2023-03-20",
    "mileage_km": 45000,
    "service_center": "ABC Service Center",
    "work_done": ["Oil change", "Filter replacement"],
    "parts_replaced": ["Air filter", "Oil filter"],
    "total_cost": 2500
  }
}
```

## Document Types Supported
1. **RC** - Registration Certificate
2. **Insurance** - Insurance Policy Document
3. **Service Bills** - Service maintenance records

## Later Extensions (Review 3+)
- Multi-document linking
- Mileage history extraction
- Ownership chain tracking
- Historical claim analysis
- Advanced document validation

## Integration Notes
- FastAPI backend will call this service at `DOCUMENT_AI_SERVICE_URL`
- Results are stored in the common Vehicle JSON structure
- Maintain source document IDs for traceability
- Confidence scores help identify uncertain extractions
