#!/usr/bin/env python3
"""
Test smart date matching functionality
"""

from app.services.date_matcher import DateMatcher

def test_date_parsing():
    """Test date parsing in various formats"""
    print("\n" + "="*60)
    print("🧪 Testing Date Parsing")
    print("="*60)
    
    test_cases = [
        ("2024-01-15", ("15", "01", "2024")),
        ("15-01-2024", ("15", "01", "2024")),
        ("15/01/2024", ("15", "01", "2024")),
        ("15-jan-2024", ("15", "01", "2024")),
        ("15-JAN-2024", ("15", "01", "2024")),
        ("jan-15-2024", ("15", "01", "2024")),
        ("15 january 2024", ("15", "01", "2024")),
        ("january 15 2024", ("15", "01", "2024")),
        ("2024 january 15", ("15", "01", "2024")),
        ("01-01-2024", ("01", "01", "2024")),
        ("2024-01-01", ("01", "01", "2024")),
    ]
    
    for input_date, expected in test_cases:
        result = DateMatcher.normalize_date(input_date)
        status = "✓" if result == expected else "✗"
        print(f"{status} {input_date:25} -> {result} (expected {expected})")

def test_date_representation_generation():
    """Test generation of all possible date representations"""
    print("\n" + "="*60)
    print("🧪 Testing Date Representation Generation")
    print("="*60)
    
    reps = DateMatcher.generate_date_representations("15", "01", "2024")
    print(f"\nGenerating representations for 15-01-2024:")
    print(f"Total representations: {len(reps)}")
    for i, rep in enumerate(reps, 1):
        print(f"  {i:2}. {rep}")

def test_date_matching_in_text():
    """Test date matching in real document text"""
    print("\n" + "="*60)
    print("🧪 Testing Date Matching in Text")
    print("="*60)
    
    test_scenarios = [
        # (date_input, document_text, expected_found)
        ("2024-01-15", "Valid from 15-jan-2024 to 15-01-2025", True),
        ("2024-01-15", "Valid from January 15, 2024 to January 15, 2025", True),
        ("15-01-2024", "The policy is valid from 15/01/2024", True),
        ("2024-01-15", "Effective Date: 15 JAN 2024", True),
        ("2024-12-31", "Expires 31 December 2024", True),
        ("2024-01-15", "Valid from 2024-01-15 to 2025-01-14", True),
        ("2024-06-30", "Your policy does not mention this date", False),
        ("01-01-2024", "Valid 01-01-2024 through 12-31-2024", True),
    ]
    
    for date_input, doc_text, expected in test_scenarios:
        result = DateMatcher.date_exists_in_text(date_input, doc_text)
        status = "✓" if result == expected else "✗"
        found_text = "Found" if result else "Not found"
        print(f"{status} Date '{date_input}' in document:")
        print(f"   Document: {doc_text[:60]}...")
        print(f"   Result: {found_text} (expected: {'Found' if expected else 'Not found'})\n")

def test_month_name_mapping():
    """Test month name to number mapping"""
    print("\n" + "="*60)
    print("🧪 Testing Month Name Mapping")
    print("="*60)
    
    print("\nMonth mappings:")
    for month_name, month_num in sorted(DateMatcher.MONTH_NAMES.items()):
        print(f"  {month_name:10} -> {month_num}")

if __name__ == "__main__":
    test_date_parsing()
    test_month_name_mapping()
    test_date_representation_generation()
    test_date_matching_in_text()
    
    print("\n" + "="*60)
    print("✅ All date matcher tests completed")
    print("="*60 + "\n")
