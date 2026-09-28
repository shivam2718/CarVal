# Sample Data

Test cases and demo data for CarVal Review 2.

## Folder Structure

```
sample_data/
├── test_cases/          # Test case sets
│   ├── test_case_1/
│   │   ├── images/
│   │   ├── documents/
│   │   └── expected_output.json
│   ├── test_case_2/
│   ├── test_case_3/
│   ├── test_case_4/
│   └── test_case_5/
├── mock_responses/      # Mock API responses for frontend development
│   ├── vision_response.json
│   ├── document_response.json
│   └── combined_result.json
├── datasets/            # Training datasets (large files, not in git)
│   └── .gitkeep
└── trained_models/      # Trained model weights (not in git)
    └── .gitkeep
```

## Test Cases (Member 4 - Testing & Support)

Each test case should contain:
- **images/**: 3-5 car images showing different damage scenarios
- **documents/**: Sample RC, insurance, and service documents
- **expected_output.json**: Expected results structure

## Mock Responses

Use these for frontend development before backend services are ready:

- `vision_response.json` - Sample vision service output
- `document_response.json` - Sample document AI output
- `combined_result.json` - Complete Vehicle JSON with results

## Demo Data

- **Test Case 1**: Sedan with minor dent and scratch
- **Test Case 2**: SUV with glass damage (windshield)
- **Test Case 3**: Hatchback with tire damage
- **Test Case 4**: Sedan with lamp damage
- **Test Case 5**: Vehicle with multiple damage types

## Usage

```bash
# Frontend Development
# Copy mock responses to frontend

# Backend Testing
# Point to test_case_X directories

# Integration Testing
# Run full pipeline with all test cases
```
