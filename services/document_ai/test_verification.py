"""
Test script for field verification system
Tests if extracted text contains user-entered field values
"""

import pytesseract
from PIL import Image
import io

# Test with sample image
def test_field_verification():
    """Test field verification logic"""
    
    # Simulate extracted text from a document
    sample_extracted_text = """
    INSURANCE POLICY DOCUMENT
    
    Policy Number: POL-12345
    Policyholder Name: John Doe
    Valid From: 01/01/2024
    Valid Until: 31/12/2025
    Insurance Company: HDFC Insurance
    
    Coverage Amount: 50,00,000
    Premium: 15,000 per year
    """
    
    # User-entered fields to verify
    user_fields = {
        "policy_number": "POL-12345",
        "owner_name": "John Doe",
        "valid_from": "01/01/2024",
        "valid_until": "31/12/2025"
    }
    
    # Make text lowercase for case-insensitive matching
    text_lower = sample_extracted_text.lower()
    
    # Verify each field
    results = {}
    all_matched = True
    
    for field_name, field_value in user_fields.items():
        if not field_value:
            results[field_name] = {
                "value": field_value,
                "found": True,
                "message": "Skipped (empty)"
            }
            continue
        
        found = str(field_value).lower() in text_lower
        results[field_name] = {
            "value": field_value,
            "found": found,
            "message": "✅ Found" if found else "❌ Not found"
        }
        
        if not found:
            all_matched = False
    
    print("\n" + "="*60)
    print("FIELD VERIFICATION TEST")
    print("="*60)
    print(f"\nExtracted Text Sample:\n{sample_extracted_text[:200]}...\n")
    print("Verification Results:")
    print("-" * 60)
    
    for field_name, result in results.items():
        status = "✅ PASS" if result["found"] else "❌ FAIL"
        print(f"{status} | {field_name:20} | {result['value']:20} | {result['message']}")
    
    print("-" * 60)
    print(f"\nOverall Result: {'✅ ALL FIELDS VERIFIED' if all_matched else '❌ SOME FIELDS MISMATCH'}\n")
    
    return all_matched

if __name__ == "__main__":
    result = test_field_verification()
    exit(0 if result else 1)
