# Document AI Service - Setup Instructions

## Prerequisites

- Python 3.9+
- Tesseract OCR installed on system
- pip package manager

## Installation

### 1. Install Tesseract OCR

**Windows:**
```bash
# Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
# Or use Chocolatey
choco install tesseract
```

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr
```

### 2. Setup Python Environment

```bash
cd services/document_ai

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env (optional)
# - Adjust OCR_BACKEND if using AWS Textract, Google Vision, etc.
# - Set TESSERACT_PATH if not in system PATH
```

### 4. Run Service

```bash
# Development (with reload)
python main.py

# Production (with uvicorn)
uvicorn main:app --host 0.0.0.0 --port 8002 --workers 4
```

Service runs at: `http://localhost:8002`

Health check: `http://localhost:8002/health`

## API Endpoints

### Health Check
```bash
GET /health
```

### Extract Any Document
```bash
POST /extract
Form data:
  - file: <pdf/image file>
  - document_type: "rc" | "insurance" | "service_bill"
```

### Extract RC Certificate
```bash
POST /extract/rc
Form data:
  - file: <RC document>
```

### Extract Insurance
```bash
POST /extract/insurance
Form data:
  - file: <Insurance document>
```

### Extract Service Bill
```bash
POST /extract/service
Form data:
  - file: <Service bill document>
```

## Example Usage

### Using cURL

```bash
# Extract RC document
curl -X POST "http://localhost:8002/extract/rc" \
  -F "file=@/path/to/rc.jpg"

# Extract Insurance document
curl -X POST "http://localhost:8002/extract/insurance" \
  -F "file=@/path/to/insurance.pdf"

# Extract Service Bill
curl -X POST "http://localhost:8002/extract/service" \
  -F "file=@/path/to/service_bill.jpg"
```

### Using Python

```python
import requests

files = {'file': open('/path/to/rc.jpg', 'rb')}
response = requests.post(
    'http://localhost:8002/extract/rc',
    files=files
)
print(response.json())
```

## Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=. tests/
```

## Troubleshooting

### Tesseract not found
- Verify Tesseract is installed: `tesseract --version`
- On Windows, add Tesseract to PATH or set `TESSERACT_PATH` in .env
- Example: `TESSERACT_PATH=C:\\Program Files\\Tesseract-OCR\\tesseract.exe`

### Poor OCR accuracy
- Ensure document images are clear and well-lit
- Try pre-processing images (contrast, brightness)
- Provide high-resolution images (300+ DPI)

### PDF extraction not working
- Install pdf2image: `pip install pdf2image`
- Also requires Poppler: 
  - Windows: `choco install poppler`
  - macOS: `brew install poppler`
  - Linux: `sudo apt-get install poppler-utils`

## Performance

- Single document extraction: ~500ms - 2s (depends on image quality)
- Confidence score: 0.6 - 0.95 (based on document clarity and OCR accuracy)
- Batch processing: Supports multiple files sequentially

## Future Improvements

- Add cloud OCR providers (Google Vision, AWS Textract)
- Implement batch processing endpoint
- Add document validation (completeness checks)
- Support more document types (pollution certificate, etc.)
- Implement caching for duplicate documents
- Add confidence score explanation

## Support

For issues or questions, contact Member 2 (Document AI owner)
