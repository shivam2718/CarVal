# Tests

Testing infrastructure for CarVal Review 2.

## Structure

```
tests/
├── backend/             # FastAPI tests
│   ├── test_health.py
│   ├── test_inspection.py
│   └── conftest.py
├── frontend/            # Next.js tests
│   ├── __tests__/
│   └── jest.config.js
├── integration/         # End-to-end tests
│   ├── test_full_flow.py
│   └── test_api_contract.py
└── test_data.json       # Shared test fixtures
```

## Running Tests

### Backend Tests
```bash
cd backend
pip install pytest pytest-asyncio
pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm run test
```

### Integration Tests
```bash
python tests/integration/test_full_flow.py
```

## Test Coverage

**Review 2 Priorities:**
- [ ] API endpoint availability (health, inspection)
- [ ] File upload handling
- [ ] Vision service integration
- [ ] Document AI integration
- [ ] Combined JSON output format
- [ ] Frontend navigation

## Contribution Guidelines (Member 4)

1. Create test cases for each feature
2. Run tests before PR submission
3. Maintain test data in `sample_data/`
4. Document new test patterns
