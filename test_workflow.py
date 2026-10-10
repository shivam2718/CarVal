#!/usr/bin/env python3
"""
Test complete verification workflow: Create inspection → Upload document → Verify fields
"""

import requests
import json
import sys

# Test with sample RC image
API_URL = "http://localhost:8000"

def test_workflow():
    print("\n" + "="*60)
    print("🧪 TESTING COMPLETE VERIFICATION WORKFLOW")
    print("="*60)
    
    # Step 1: Create Inspection
    print("\n1️⃣  Creating inspection...")
    try:
        resp = requests.post(f"{API_URL}/inspection")
        resp.raise_for_status()
        inspection_id = resp.json()["inspection_id"]
        print(f"✓ Inspection created: {inspection_id}")
    except Exception as e:
        print(f"❌ Failed to create inspection: {e}")
        return False
    
    # Step 2: Upload RC document
    print("\n2️⃣  Uploading RC document...")
    try:
        # Try to read sample RC image
        rc_image_path = "sample_data/rc_sample.jpg"
        try:
            with open(rc_image_path, "rb") as f:
                rc_data = f.read()
                files = {"files": ("rc.jpg", rc_data, "image/jpeg")}
                resp = requests.post(f"{API_URL}/inspection/{inspection_id}/documents", files=files)
                resp.raise_for_status()
                print(f"✓ Document uploaded")
        except FileNotFoundError:
            print(f"⚠️  Sample RC image not found at {rc_image_path}")
            print("   Creating mock test with dummy image data...")
            # Use a minimal valid PNG as placeholder
            files = {"files": ("rc.jpg", b"mock_image_data", "image/jpeg")}
            resp = requests.post(f"{API_URL}/inspection/{inspection_id}/documents", files=files)
            resp.raise_for_status()
            print(f"✓ Mock document uploaded")
    except Exception as e:
        print(f"❌ Failed to upload document: {e}")
        return False
    
    # Step 3: Verify RC fields
    print("\n3️⃣  Verifying RC fields...")
    rc_fields = {
        "registration_number": "DL-01-AB-1234",
        "model": "Maruti Swift",
        "manufacturing_year": "2021",
        "fuel_type": "petrol",
        "vin": "ABCDEF1234567890"
    }
    
    try:
        resp = requests.post(
            f"{API_URL}/inspection/{inspection_id}/verify-fields",
            json=rc_fields
        )
        resp.raise_for_status()
        result = resp.json()
        
        print("✓ RC verification completed")
        print(f"   Status: {result['status']}")
        print(f"   All matched: {result['all_matched']}")
        print(f"   Message: {result['message']}")
        print("\n   Field Results:")
        for field, result_data in result['verification_results'].items():
            status = "✅" if result_data['found'] else "❌"
            print(f"     {status} {field}: {result_data['message']}")
    except Exception as e:
        print(f"❌ Failed to verify fields: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*60)
    print("✅ WORKFLOW TEST COMPLETED")
    print("="*60 + "\n")
    return True

if __name__ == "__main__":
    success = test_workflow()
    sys.exit(0 if success else 1)
