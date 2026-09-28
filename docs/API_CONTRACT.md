# CarVal API Contract

Reference for backend, frontend, and member services. **All changes to this contract must be discussed with the team.**

## Base URL
- **Development**: `http://localhost:8000`
- **Production**: TBD

## Authentication
Review 2: No authentication. Add in Review 3.

## Common Response Format

```json
{
  "status": "success" | "error",
  "data": { /* endpoint-specific */ },
  "message": "Optional message",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Health & Status

### GET /health

Check backend and service status.

**Response:**
```json
{
  "status": "healthy",
  "backend": "operational",
  "vision_service": "operational" | "pending" | "error",
  "document_ai_service": "operational" | "pending" | "error"
}
```

---

## Inspection Endpoints

### POST /inspection

Create a new vehicle inspection.

**Response:**
```json
{
  "inspection_id": "INS-A1B2C3D4",
  "status": "created",
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### POST /inspection/{inspection_id}/images

Upload car images.

**Request:**
- Content-Type: `multipart/form-data`
- Form field: `files` (multiple file upload)
- Accepted: `.jpg`, `.jpeg`, `.png`
- Max size: 10 MB per image

**Response:**
```json
{
  "inspection_id": "INS-A1B2C3D4",
  "uploaded_images": 3,
  "files": [
    {
      "file_id": "IMG-001",
      "filename": "front_view.jpg",
      "size": 2048576,
      "content_type": "image/jpeg"
    }
  ]
}
```

---

### POST /inspection/{inspection_id}/documents

Upload vehicle documents (RC, Insurance, Service Bills).

**Request:**
- Content-Type: `multipart/form-data`
- Form field: `files` (multiple file upload)
- Accepted: `.pdf`, `.jpg`, `.jpeg`, `.png`
- Max size: 20 MB per document

**Response:**
```json
{
  "inspection_id": "INS-A1B2C3D4",
  "uploaded_documents": 2,
  "files": [
    {
      "file_id": "DOC-001",
      "filename": "rc_certificate.pdf",
      "size": 1024000,
      "content_type": "application/pdf"
    }
  ]
}
```

---

### POST /inspection/{inspection_id}/vision

Trigger Vision Service for damage detection on uploaded images.

**Response:**
```json
{
  "inspection_id": "INS-A1B2C3D4",
  "status": "vision_analysis_started",
  "queued_at": "2024-01-15T10:35:00Z"
}
```

**Backend Behavior:**
1. Calls Member 1's Vision Service with uploaded image IDs
2. Receives damage detection results
3. Stores results in inspection record
4. Updates `pipeline_status.vision_completed = true`

---

### POST /inspection/{inspection_id}/documents/extract

Trigger Document AI for information extraction.

**Response:**
```json
{
  "inspection_id": "INS-A1B2C3D4",
  "status": "document_extraction_started",
  "queued_at": "2024-01-15T10:36:00Z"
}
```

**Backend Behavior:**
1. Calls Member 2's Document AI Service with document IDs
2. Receives extracted information (RC, insurance, service history)
3. Stores results in inspection record
4. Updates `pipeline_status.document_ai_completed = true`

---

### GET /inspection/{inspection_id}

Retrieve current inspection results (combined Vehicle JSON).

**Response:** Complete Vehicle JSON matching `vehicle_schema_v1.json`

```json
{
  "schema_version": "1.0",
  "vehicle_id": "INS-A1B2C3D4",
  "vehicle": {},
  "input_files": {
    "images": [
      {
        "file_id": "IMG-001",
        "filename": "front_view.jpg"
      }
    ],
    "documents": [
      {
        "file_id": "DOC-001",
        "filename": "rc_certificate.pdf"
      }
    ]
  },
  "vision": {
    "damage_detection": {
      "model": "YOLOv8-damage-detection-v1",
      "image_results": [
        {
          "image_id": "IMG-001",
          "damages": [
            {
              "damage_id": "DMG-001",
              "type": "dent",
              "confidence": 0.95,
              "bbox": {
                "x1": 100,
                "y1": 100,
                "x2": 200,
                "y2": 200
              },
              "severity": "medium",
              "affected_part": "door"
            }
          ]
        }
      ]
    }
  },
  "documents": {
    "rc": {
      "extracted": true,
      "fields": {
        "registration_number": "DL-01-AB-1234",
        "owner": "John Doe",
        "model": "Maruti Swift",
        "manufacturing_year": 2015
      },
      "confidence": 0.92
    }
  },
  "pipeline_status": {
    "images_processed": true,
    "documents_processed": true,
    "vision_completed": true,
    "document_ai_completed": true
  }
}
```

---

### GET /inspection/{inspection_id}/report

Retrieve final evidence-backed report (Review 4).

**Response:** Final report with all analysis, valuation, and recommendations.

**Status in Review 2:** Returns `{"status": "pending", "message": "Available in Review 4"}`

---

## Error Responses

### 404 Not Found
```json
{
  "status": "error",
  "detail": "Inspection not found",
  "inspection_id": "INS-INVALID"
}
```

### 400 Bad Request
```json
{
  "status": "error",
  "detail": "File size exceeds maximum allowed (10 MB)",
  "field": "files"
}
```

### 500 Server Error
```json
{
  "status": "error",
  "detail": "Internal server error",
  "timestamp": "2024-01-15T10:40:00Z"
}
```

---

## Service-to-Backend Integration

### Vision Service Interface (Member 1)
**Hosted at**: `{VISION_SERVICE_URL}` (default: `http://localhost:8001`)

**Backend calls:**
```
POST {VISION_SERVICE_URL}/analyze
Body: { "image_paths": ["IMG-001", "IMG-002"] }
Response: { "image_results": [...], "model": "..." }
```

### Document AI Service Interface (Member 2)
**Hosted at**: `{DOCUMENT_AI_SERVICE_URL}` (default: `http://localhost:8002`)

**Backend calls:**
```
POST {DOCUMENT_AI_SERVICE_URL}/extract/rc
Body: { "document_paths": ["DOC-001"] }
Response: { "extracted": true, "fields": {...} }
```

---

## Backward Compatibility Rules

1. **Never remove** or rename existing fields
2. **Always add** new fields with `null` default
3. **Version the schema** when major structure changes (`schema_version`)
4. **Use `pending` status** for features not yet implemented
5. **Maintain evidence links** - every finding must reference source data

---

## Review 2 Status

✅ Health Check
✅ Inspection CRUD
✅ Image Upload
✅ Document Upload
✅ Vision Integration (placeholder)
✅ Document AI Integration (placeholder)
✅ Combined Results

⏳ Authentication
⏳ Rate Limiting
⏳ Caching
⏳ Pagination
