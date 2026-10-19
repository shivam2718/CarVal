# Run Everything - Full End-to-End Test

Complete guide to run all services and test document upload.

## Prerequisites

- Python 3.9+ installed
- Node.js 18+ installed
- Tesseract OCR installed (for Document AI)

---

## Installation (Do This ONCE)

### 1. Install Tesseract OCR

**Windows:**
- Download: https://github.com/UB-Mannheim/tesseract/wiki
- Run installer
- OR use Chocolatey: `choco install tesseract`

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

---

### 2. Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### 3. Setup Document AI Service

```bash
cd services/document_ai

# Create virtual environment (or reuse backend's)
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### 4. Setup Frontend

```bash
cd frontend

# Install Node dependencies
npm install
```

---

## Quick Start (Run These EVERY TIME)

Open 3 terminal windows and run these commands:

### Terminal 1: Document AI Service (Member 2)

```bash
cd services/document_ai
# Activate venv if needed
python main.py
```

Wait for:
```
INFO:     Uvicorn running on http://0.0.0.0:8002
INFO:     Application startup complete.
```

✅ Document AI running on: **http://localhost:8002**

---

### Terminal 2: Backend API (Member 3)

```bash
cd backend
# Activate venv if needed
python -m uvicorn app.main:app --reload --port 8000
```

Wait for:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

✅ Backend running on: **http://localhost:8000**

---

### Terminal 3: Frontend Dashboard (Member 3)

```bash
cd frontend

npm run dev
```

Wait for:
```
Ready in X.XXs
Local:        http://localhost:3000
```

✅ Frontend running on: **http://localhost:3000**

---

## Testing

### Option 1: Web Dashboard (Best for Demo)

1. **Open Dashboard**
   ```
   http://localhost:3000
   ```

2. **Create Inspection**
   - Click "Start Inspection"
   - Note the inspection ID (e.g., `INS-A1B2C3D4`)

3. **Upload Documents**
   - Sample docs available in `sample_data/`
   - Upload RC, Insurance, or Service Bill
   - Formats: JPG, PNG, PDF

4. **Click "Analyze"**
   - Backend forwards to Document AI Service
   - Results extracted and displayed

5. **View Results**
   - See extracted vehicle information
   - View complete Vehicle JSON
   - All data in common schema format

---

### Option 2: API Testing (via cURL)

**Step 1: Create Inspection**
```bash
curl -X POST "http://localhost:8000/inspection"

# Response:
# {"inspection_id": "INS-XXXX", "status": "created", "created_at": "..."}
# Copy the inspection_id
```

**Step 2: Upload Documents**
```bash
# Create sample document first
# Or use existing file

curl -X POST "http://localhost:8000/inspection/INS-XXXX/documents" \
  -F "files=@your_document.jpg"
```

**Step 3: Extract Information**
```bash
curl -X POST "http://localhost:8000/inspection/INS-XXXX/documents/extract"
```

**Step 4: View Results**
```bash
curl "http://localhost:8000/inspection/INS-XXXX"

# See extracted data in Vehicle JSON format
```

---

## Creating Test Documents

### Quick Method: Use Python

```bash
cd sample_data

python -c "
from PIL import Image, ImageDraw

# Create simple RC test image
img = Image.new('RGB', (600, 400), color='white')
d = ImageDraw.Draw(img)

text = '''
REGISTRATION CERTIFICATE

Registration: DL-01-AB-1234
Owner: John Doe
Model: Swift
Year: 2015
Fuel: Petrol
Mileage: 50000 km
'''

d.text((20, 20), text, fill='black')
img.save('rc_sample.jpg')

print('✅ Created rc_sample.jpg')
"
```

---

## Expected Output

After uploading a document and analyzing:

```json
{
  "schema_version": "1.0",
  "vehicle_id": "INS-ABC123",
  "documents": {
    "rc": {
      "extracted": true,
      "confidence": 0.92,
      "fields": {
        "registration_number": "DL-01-AB-1234",
        "owner": "John Doe",
        "model": "Swift",
        "manufacturing_year": 2015,
        "fuel_type": "petrol"
      }
    }
  },
  "pipeline_status": {
    "documents_processed": true,
    "document_ai_completed": true
  }
}
```

---

## Health Checks

Verify all services are running:

```bash
# Document AI Service
curl http://localhost:8002/health
# Expected: {"status": "healthy", "service": "Document AI"}

# Backend
curl http://localhost:8000/health
# Expected: {"status": "healthy"}

# Frontend
curl http://localhost:3000
# Expected: HTML dashboard page
```

---

## Troubleshooting

### Services won't start

**Check ports:**
```bash
# Find what's using the ports
# Windows:
netstat -ano | findstr :8000
netstat -ano | findstr :8002
netstat -ano | findstr :3000

# macOS/Linux:
lsof -i :8000
lsof -i :8002
lsof -i :3000
```

**Kill processes:**
```bash
# Windows:
taskkill /PID <PID> /F

# macOS/Linux:
kill -9 <PID>
```

### Document AI crashes

**Error: pytesseract.TesseractNotFoundError**
- Install Tesseract OCR (see Prerequisites above)

**Error: Python version**
- Use Python 3.9 or newer: `python --version`

### Backend won't connect to Document AI

**Check:**
1. Document AI service is running on port 8002
2. Backend can see it: `curl http://localhost:8002/health`
3. `.env` has correct `DOCUMENT_AI_SERVICE_URL`

### Frontend won't load

**Check:**
1. Backend is running on port 8000
2. No port conflicts: `netstat -ano | findstr :3000`
3. Clear npm cache: `npm cache clean --force`

---

## For Review 2 Demo

Perfect walkthrough for the panel:

1. **Open Dashboard** → http://localhost:3000
2. **Show Services Running**
   - Backend: http://localhost:8000/health
   - Document AI: http://localhost:8002/health
3. **Create Inspection** → Click button, get ID
4. **Upload Sample Documents** → RC, insurance, service bill
5. **Run Analysis** → Click "Analyze"
6. **Show Results** → Extracted vehicle information
7. **Show JSON** → Complete Vehicle schema with extracted data
8. **Explain Integration** → "All services use this common data format"

---

## API Endpoints Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Service health check |
| `/inspection` | POST | Create new inspection |
| `/inspection/{id}` | GET | Get inspection results |
| `/inspection/{id}/documents` | POST | Upload documents |
| `/inspection/{id}/documents/extract` | POST | Extract from documents |

---

## File Structure

```
CarVal/
├── backend/                    ✅ FastAPI orchestrator
│   └── app/
│       ├── main.py             (Entry point)
│       ├── api/inspection.py   (Endpoints)
│       └── services/           (Service clients)
│
├── services/document_ai/       ✅ OCR extraction (Member 2)
│   ├── main.py                 (FastAPI service)
│   └── test_extraction.py      (Tests)
│
├── frontend/                   ✅ Next.js dashboard
│   ├── app/page.tsx            (Home)
│   ├── app/inspection/page.tsx (Upload)
│   └── app/results/[id]/page.tsx (Results)
│
├── sample_data/                (Test documents)
└── QUICK_START.md              (Setup guide)
```

---

## Next Steps

1. ✅ Run all services (Document AI already running)
2. ✅ Test via web dashboard
3. ⏳ Member 1 creates Vision Service (damage detection)
4. ⏳ Integrate Vision Service into backend
5. ⏳ Show full flow in Review 2 demo

---

## Support

**Document AI Issues?** → Check `services/document_ai/SETUP.md`
**Backend Issues?** → Check `backend/` README
**Frontend Issues?** → Check `frontend/` README

---

**Ready to go! Start with the three terminal commands above.** 🚀
