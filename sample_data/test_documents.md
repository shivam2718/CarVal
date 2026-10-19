# Sample Test Documents for Document AI

Use these to test your document extraction service.

## Option 1: Create Test Images

You can create simple test images using any image editor or:

### Windows Paint
1. Open Paint
2. Write text similar to what's below
3. Save as JPG or PNG

### Quick Python Script

```python
from PIL import Image, ImageDraw, ImageFont

# Create RC sample
img = Image.new('RGB', (600, 400), color='white')
d = ImageDraw.Draw(img)

rc_text = """
REGISTRATION CERTIFICATE

Registration Number: DL-01-AB-1234
Make: Maruti
Model: Swift
Manufacturing Year: 2015
Registration Year: 2015
Fuel Type: PETROL
Engine: 1200 cc
Power: 82 bhp
Transmission: MANUAL
Owner: John Doe
"""

d.text((50, 50), rc_text, fill='black')
img.save('sample_data/rc_sample.jpg')
```

---

## Option 2: Use Real Documents

Scan or photograph:
- Your vehicle RC (Registration Certificate)
- Insurance policy document
- Service bill from maintenance

---

## Testing Formats

Document AI accepts:
- **JPG** ✅ Recommended (easiest for OCR)
- **PNG** ✅ Works well
- **PDF** ⏳ Supported (needs poppler)

---

## Test via API

```bash
# Test RC extraction
curl -X POST "http://localhost:8002/extract/rc" \
  -F "file=@sample_data/rc_sample.jpg"

# Response should include:
{
  "document_type": "rc",
  "extracted": true,
  "confidence": 0.92,
  "fields": {
    "registration_number": "DL-01-AB-1234",
    "owner": "John Doe",
    "model": "Swift",
    "manufacturing_year": 2015
  }
}
```

---

## Create Sample Documents Programmatically

Run this Python script to generate sample documents:

```python
# Create sample documents
from PIL import Image, ImageDraw

def create_rc_sample():
    img = Image.new('RGB', (800, 600), color='white')
    d = ImageDraw.Draw(img)
    
    text = """
    REGISTRATION CERTIFICATE (FORM 20)
    
    Registration Number: DL-01-AB-1234
    Owner: John Doe
    Address: 123 Main Street, Delhi
    
    Vehicle Details:
    Make: Maruti
    Model: Swift
    Variant: VXi
    Manufacturing Year: 2015
    Registration Year: 2015
    Fuel Type: PETROL
    Transmission: MANUAL
    
    Engine:
    Displacement: 1200 cc
    Power: 82 bhp
    
    VIN: 1HGBH41JXMN109186
    """
    
    d.text((50, 50), text, fill='black')
    img.save('sample_data/rc_sample.jpg')

def create_insurance_sample():
    img = Image.new('RGB', (800, 600), color='white')
    d = ImageDraw.Draw(img)
    
    text = """
    MOTOR INSURANCE POLICY
    
    Policy Number: POL-123456789
    Insurer: HDFC ERGO
    
    Vehicle: DL-01-AB-1234 - Maruti Swift
    
    Coverage Period:
    Valid From: 01-01-2024
    Valid Until: 31-12-2024
    
    Coverage:
    - Third Party Liability: Yes
    - Own Damage: Yes
    - Personal Accident: Yes
    
    Claims History:
    Claim 1: ₹50000 (15-06-2023) - Accident Damage
    Claim 2: ₹15000 (22-08-2022) - Minor Collision
    
    Status: ACTIVE
    """
    
    d.text((50, 50), text, fill='black')
    img.save('sample_data/insurance_sample.jpg')

def create_service_sample():
    img = Image.new('RGB', (800, 600), color='white')
    d = ImageDraw.Draw(img)
    
    text = """
    SERVICE BILL
    
    Service Center: ABC Service Center
    Location: New Delhi
    
    Service Date: 20-03-2023
    Vehicle Mileage: 45000 km
    
    Services Performed:
    1. Oil Change - ₹500
    2. Filter Replacement - ₹300
    3. Spark Plug Replacement - ₹400
    4. Tire Rotation - ₹200
    
    Parts Replaced:
    - Air Filter
    - Oil Filter
    - Spark Plug
    
    Total Cost: ₹1400
    Payment: Paid
    
    Service Advisor: Ram Kumar
    """
    
    d.text((50, 50), text, fill='black')
    img.save('sample_data/service_bill_sample.jpg')

# Create all samples
create_rc_sample()
create_insurance_sample()
create_service_sample()

print("✅ Sample documents created!")
```

Save as `create_samples.py` and run:
```bash
cd sample_data
python create_samples.py
```

---

## Quick Test

After creating samples, test extraction:

```bash
# Test all three
python -c "
from services.document_ai.main import DocumentExtractor

extractor = DocumentExtractor()

# Test RC
rc_text = '''
Registration Number: DL-01-AB-1234
Model: Swift
Manufacturing Year: 2015
Fuel Type: PETROL
Transmission: MANUAL
'''
print('RC:', extractor.extract_rc_info(rc_text))

# Test Insurance
ins_text = '''
Policy Number: POL-123456789
Valid From: 01-01-2024
Valid Until: 31-12-2024
Insurer: HDFC
Claim: ₹50000
'''
print('Insurance:', extractor.extract_insurance_info(ins_text))

# Test Service
svc_text = '''
Service Date: 20-03-2023
Mileage: 45000 km
Service Center: ABC Center
Oil Change
Filter Replacement
Total Cost: ₹1400
'''
print('Service:', extractor.extract_service_history(svc_text))
"
```

---

## Running Full Test

1. **Start Document AI Service**
   ```bash
   cd services/document_ai
   python main.py
   ```

2. **Upload test document**
   ```bash
   curl -X POST "http://localhost:8002/extract/rc" \
     -F "file=@sample_data/rc_sample.jpg"
   ```

3. **See extracted results**
   ```json
   {
     "document_type": "rc",
     "extracted": true,
     "fields": {
       "registration_number": "DL-01-AB-1234",
       "model": "Swift",
       "manufacturing_year": 2015
     }
   }
   ```

---

## For Web Dashboard Test

1. Go to http://localhost:3000
2. Click "Start Inspection"
3. Upload `sample_data/rc_sample.jpg`
4. Click "Analyze"
5. See extracted data displayed

Perfect for Review 2 demo! 🎯
