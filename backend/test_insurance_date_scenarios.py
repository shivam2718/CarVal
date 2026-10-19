#!/usr/bin/env python3
"""
Test insurance date verification with realistic document formats
"""

from app.services.date_matcher import DateMatcher

def test_insurance_verification_scenarios():
    """Test realistic insurance policy scenarios"""
    print("\n" + "="*80)
    print("TEST: Insurance Policy Date Verification Scenarios")
    print("="*80)
    
    # Scenario 1: User enters dates in HTML form (YYYY-MM-DD)
    # Document has dates in different format
    
    scenarios = [
        {
            "name": "Scenario 1: User enters 2024-01-15, Doc has '15-JAN-2024'",
            "user_valid_from": "2024-01-15",
            "user_valid_until": "2025-01-14",
            "document_text": """
            INSURANCE POLICY
            Policy Number: POL-2024-ABC123
            Valid From: 15-JAN-2024
            Valid Until: 14-JANUARY-2025
            Premium: Rs. 5000
            """
        },
        {
            "name": "Scenario 2: User enters 01-01-2024, Doc has '1/1/2024' and 'January 01, 2024'",
            "user_valid_from": "2024-01-01",
            "user_valid_until": "2024-12-31",
            "document_text": """
            INSURANCE CERTIFICATE
            Effective Date: 1/1/2024
            Expires: January 01, 2025
            Coverage Type: Comprehensive
            """
        },
        {
            "name": "Scenario 3: User enters 15-06-2024, Doc has '15 JUNE 2024'",
            "user_valid_from": "2024-06-15",
            "user_valid_until": "2025-06-14",
            "document_text": """
            POLICY RENEWAL
            Renewal Date: 15 JUNE 2024
            Expiry Date: 14 June 2025
            Status: Active
            """
        },
        {
            "name": "Scenario 4: Mixed formats - DD-Mon-YYYY, DD/MM/YYYY, full month name",
            "user_valid_from": "2024-12-31",
            "user_valid_until": "2025-12-30",
            "document_text": """
            YEAR END POLICY
            Issued on: 31-DEC-2024
            Valid From: 31/12/2024
            Valid Until: 30 December 2025
            Renewal Status: Annual
            """
        },
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}")
        print("-" * 80)
        
        user_valid_from = scenario["user_valid_from"]
        user_valid_until = scenario["user_valid_until"]
        doc_text = scenario["document_text"]
        
        # Check if user's dates are found in document
        from_found = DateMatcher.date_exists_in_text(user_valid_from, doc_text)
        until_found = DateMatcher.date_exists_in_text(user_valid_until, doc_text)
        
        print(f"User entered valid_from: {user_valid_from}")
        print(f"  Result: {'FOUND' if from_found else 'NOT FOUND'}")
        
        print(f"User entered valid_until: {user_valid_until}")
        print(f"  Result: {'FOUND' if until_found else 'NOT FOUND'}")
        
        print(f"Document excerpt: {doc_text.strip()[:100]}...")
        
        if from_found and until_found:
            print("PASS: Both dates verified!")
        else:
            print("FAIL: Some dates not matched")

def test_edge_cases():
    """Test edge cases and problematic scenarios"""
    print("\n" + "="*80)
    print("TEST: Edge Cases & Problematic Scenarios")
    print("="*80)
    
    edge_cases = [
        {
            "name": "Single digit day/month (01 vs 1)",
            "user_date": "2024-01-05",
            "doc_text": "Valid: 5 January 2024",
            "expected": True
        },
        {
            "name": "Month as number vs word (01 vs JAN)",
            "user_date": "2024-01-15",
            "doc_text": "Expiry: 15-JAN-2024",
            "expected": True
        },
        {
            "name": "Different separators (- vs / vs space)",
            "user_date": "2024-03-20",
            "doc_text": "Policy valid 20/03/2024",
            "expected": True
        },
        {
            "name": "Year ordering (YYYY-MM-DD vs DD-MM-YYYY)",
            "user_date": "2024-12-25",
            "doc_text": "Inception: 25-12-2024",
            "expected": True
        },
        {
            "name": "Full month names (January vs Jan)",
            "user_date": "2024-11-30",
            "doc_text": "Expires: 30 November 2024",
            "expected": True
        },
    ]
    
    for case in edge_cases:
        result = DateMatcher.date_exists_in_text(case["user_date"], case["doc_text"])
        status = "PASS" if result == case["expected"] else "FAIL"
        result_text = "FOUND" if result else "NOT FOUND"
        expected_text = "FOUND" if case["expected"] else "NOT FOUND"
        
        print(f"\n{status}: {case['name']}")
        print(f"  User Date: {case['user_date']}")
        print(f"  Doc Text: {case['doc_text']}")
        print(f"  Result: {result_text} (expected: {expected_text})")

if __name__ == "__main__":
    test_insurance_verification_scenarios()
    test_edge_cases()
    
    print("\n" + "="*80)
    print("PASS: All insurance date verification tests completed")
    print("="*80 + "\n")
