# Quick Start - Full System Test

Run all services and test document upload end-to-end.

## Step 1: Start Document AI Service (Member 2)

```bash
cd services/document_ai
python main.py
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8002
INFO:     Application startup complete.
```

Keep this running (open in a new terminal).

---

## Step 2: Start Backend (FastAPI - Member 3)

Open a NEW terminal:

```bash
cd backend
pip install -r requirements.txt

python -m uvicorn app.main:app --reload --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

Keep this running (open in a new terminal).

---

## Step 3: Start Frontend (Next.js - Member 3)

Open a NEW terminal:

```bash
cd frontend
npm install

npm run dev
```

Expected output:
```
 Ready in 2.5s
 Local:        http://localhost:3000
```

---

## Step 4: Test the Full Flow

### Option A: Via Web Dashboard (Easiest)

1. **Open Dashboard**
   - Go to: http://localhost:3000
   - You'll see the CarVal home page

2. **Create Inspection**
   - Click "Start Inspection"
   - You'll get an inspection ID (e.g., `INS-A1B2C3D4`)

3. **Upload Documents**
   - Sample documents in: `sample_data/`
   - Or use your own: RC, insurance, service bill (JPG, PNG, PDF)

4. **Run Analysis**
   - Click "Analyze"
   - Backend calls Document AI Service
   - Results display on page

---

### Option B: Via API (For testing)

**Test Document AI directly:**

```bash
# Extract RC
curl -X POST "http://localhost:8002/extract/rc" \
  -F "file=@sample_data/rc_sample.jpg"

# Extract Insurance
curl -X POST "http://localhost:8002/extract/insurance" \
  -F "file=@sample_data/insurance_sample.jpg"

# Extract Service Bill
curl -X POST "http://localhost:8002/extract/service" \
  -F "file=@sample_data/service_bill_sample.jpg"
```

**Test Backend Integration:**

```bash
# Create inspection
curl -X POST "http://localhost:8000/inspection"

# Create inspection returns:
# {"inspection_id": "INS-XXXX", "status": "created"}

# Upload documents
curl -X POST "http://localhost:8000/inspection/INS-XXXX/documents" \
  -F "files=@sample_data/rc_sample.jpg" \
  -F "files=@sample_data/insurance_sample.jpg"

# Extract documents
curl -X POST "http://localhost:8000/inspection/INS-XXXX/documents/extract"

# View results
curl "http://localhost:8000/inspection/INS-XXXX"
```

---

## Troubleshooting

### Services won't start

**Document AI (Port 8002):**
```bash
# Check if port is in use
netstat -ano | findstr :8002

# Kill process if needed
taskkill /PID <PID> /F
```

**Backend (Port 8000):**
```bash
# Check if port is in use
netstat -ano | findstr :8000

# Kill process if needed
taskkill /PID <PID> /F
```

**Frontend (Port 3000):**
```bash
# Check if port is in use
netstat -ano | findstr :3000

# Kill process if needed
taskkill /PID <PID> /F
```

### Dependencies missing

```bash
# Backend dependencies
cd backend
pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm install
```

### Tesseract not found

If you see: `pytesseract.TesseractNotFoundError`

**Install Tesseract:**
- Windows: https://github.com/UB-Mannheim/tesseract/wiki
- macOS: `brew install tesseract`
- Linux: `sudo apt-get install tesseract-ocr`

---

## API Endpoints

### Health Checks
```
GET http://localhost:8000/health               (Backend)
GET http://localhost:8002/health               (Document AI)
```

### Inspection Flow
```
POST   http://localhost:8000/inspection                           (Create)
POST   http://localhost:8000/inspection/{id}/images               (Upload images)
POST   http://localhost:8000/inspection/{id}/documents            (Upload documents)
POST   http://localhost:8000/inspection/{id}/documents/extract    (Extract)
GET    http://localhost:8000/inspection/{id}                      (View results)
```

### Document AI
```
POST   http://localhost:8002/extract/rc                    (Extract RC)
POST   http://localhost:8002/extract/insurance             (Extract Insurance)
POST   http://localhost:8002/extract/service               (Extract Service Bill)
```

---

## Expected Results

After uploading a document and clicking "Analyze":

```json
{
  "schema_version": "1.0",
  "vehicle_id": "INS-A1B2C3D4",
  "documents": {
    "rc": {
      "extracted": true,
      "fields": {
        "registration_number": "DL-01-AB-1234",
        "owner": "John Doe",
        "model": "Swift",
        "manufacturing_year": 2015,
        "fuel_type": "petrol"
      },
      "confidence": 0.92
    },
    "insurance": {
      "extracted": true,
      "policy_number": "POL-123456789",
      "valid_from": "2024-01-01",
      "claims": [...]
    }
  },
  "pipeline_status": {
    "documents_processed": true,
    "document_ai_completed": true
  }
}
```

---

## Demo Flow

Perfect for showing the panel:

1. Open http://localhost:3000 (Dashboard)
2. Click "Start Inspection" → Get inspection ID
3. Upload sample documents (RC, insurance, service bill)
4. Click "Analyze" → Processing...
5. See extracted vehicle information
6. Show Vehicle JSON with all extracted data
7. "This is the common data contract used across all services"

---

## Vision Service (Member 1)

The Vision Service runs on port 8001 (see `services/vision/README.md`):
```bash
cd services/vision && source .venv/bin/activate && python main.py
```
- Try it on its own at `http://localhost:8001/demo`
- Add `VISION_SERVICE_URL=http://localhost:8001` to `.env`
- Backend integration is pending; results will appear in the "vision" section of Vehicle JSON

---

## Files You Have

```
CarVal/
├── frontend/          (Next.js Dashboard)
├── backend/           (FastAPI Orchestrator)
├── services/
│   └── document_ai/   (OCR Document Extraction) ✅ RUNNING
├── .env.example
└── QUICK_START.md     (This file)
```

Ready to go! 🚀
