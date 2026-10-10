"""
Test script for Document AI extraction
Member 2 can use this to test their implementations
"""

import json
from main import DocumentExtractor

# Sample OCR text from RC document
SAMPLE_RC_TEXT = """
FORM 1-A
REGISTRATION CERTIFICATE
Registration Number: DL-01-AB-1234
Vehicle Identification Number: 1HGBH41JXMN109186

VEHICLE DETAILS
Make: Maruti
Model: Swift
Variant: VXi
Manufacturing Year: 2015
Registration Year: 2015
Body Type: Car
Fuel Type: PETROL
Seating Capacity: 5
Engine Displacement: 1200 cc
Power: 82 bhp
Transmission: MANUAL

OWNER DETAILS
Owner Name: John Doe
Father Name: James Doe
Address: 123 Main Street, New Delhi 110001

Date of Registration: 15-03-2015
"""

SAMPLE_INSURANCE_TEXT = """
MOTOR INSURANCE POLICY DOCUMENT

Policy Number: POL-123456789
Insurer Name: HDFC ERGO
Vehicle Registration: DL-01-AB-1234

PERIOD OF INSURANCE
Valid From: 01-01-2024
Valid Until: 31-12-2024

COVERAGE
Third Party Liability: Covered
Own Damage: Covered
Personal Accident: Covered

CLAIMS HISTORY
Claim 1: Amount ₹50000 - Date: 15-06-2023 - Accident Damage
Claim 2: Amount ₹15000 - Date: 22-08-2022 - Minor Collision

Policy Status: Active
"""

SAMPLE_SERVICE_TEXT = """
SERVICE BILL

Service Center: ABC Service Center, Delhi
Service Date: 20-03-2023
Mileage: 45000 km

SERVICES PERFORMED
1. Oil Change - ₹500
2. Filter Replacement - ₹300
3. Spark Plug Replacement - ₹400
4. Battery Check - Free
5. Tire Rotation - ₹200

Parts Replaced:
- Air Filter
- Oil Filter
- Spark Plug

Total Cost: ₹1400
Payment Status: Paid

Service Advisor: Ram Kumar
"""


def test_rc_extraction():
    """Test RC extraction"""
    print("=" * 60)
    print("Testing RC Extraction")
    print("=" * 60)
    
    extractor = DocumentExtractor()
    fields = extractor.extract_rc_info(SAMPLE_RC_TEXT)
    
    print(json.dumps(fields, indent=2))
    
    # Verify extracted fields
    assert fields["registration_number"] == "DL-01-AB-1234", "RC number mismatch"
    assert fields["model"] is not None, "Model not extracted"
    assert fields["manufacturing_year"] == 2015, "Year mismatch"
    assert fields["fuel_type"] == "petrol", "Fuel type mismatch"
    assert fields["transmission"] == "manual", "Transmission mismatch"
    
    print("\n✅ RC Extraction Test PASSED\n")


def test_insurance_extraction():
    """Test Insurance extraction"""
    print("=" * 60)
    print("Testing Insurance Extraction")
    print("=" * 60)
    
    extractor = DocumentExtractor()
    fields = extractor.extract_insurance_info(SAMPLE_INSURANCE_TEXT)
    
    print(json.dumps(fields, indent=2))
    
    # Verify extracted fields
    assert fields["policy_number"] == "POL-123456789", "Policy number mismatch"
    assert fields["insurer_name"] == "Hdfc", "Insurer name mismatch"
    assert len(fields["claims"]) > 0, "No claims extracted"
    
    print("\n✅ Insurance Extraction Test PASSED\n")


def test_service_extraction():
    """Test Service Bill extraction"""
    print("=" * 60)
    print("Testing Service Bill Extraction")
    print("=" * 60)
    
    extractor = DocumentExtractor()
    service_records = extractor.extract_service_history(SAMPLE_SERVICE_TEXT)
    
    print(json.dumps(service_records, indent=2, default=str))
    
    # Verify extracted fields
    assert len(service_records) > 0, "No service records extracted"
    assert service_records[0]["mileage_km"] == 45000, "Mileage mismatch"
    assert service_records[0]["cost"] == 1400, "Cost mismatch"
    
    print("\n✅ Service Bill Extraction Test PASSED\n")


def test_all():
    """Run all tests"""
    print("\n")
    print("🧪 Running Document AI Extraction Tests")
    print("=" * 60)
    
    try:
        test_rc_extraction()
        test_insurance_extraction()
        test_service_extraction()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
    
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = test_all()
    exit(0 if success else 1)
