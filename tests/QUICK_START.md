# Quick Start - Running Tests

## Installation

```bash
# Install test dependencies
pip install -r requirements-test.txt
```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run with Verbose Output
```bash
pytest -v
```

### Run with Coverage
```bash
pytest --cov=app --cov-report=term-missing
```

### Run Specific Test File
```bash
pytest tests/test_search.py      # Search endpoint tests
pytest tests/test_concept.py     # Concept endpoint tests
pytest tests/test_main.py        # Index endpoint tests
```

### Run Specific Test
```bash
pytest tests/test_search.py::TestSearchEndpoint::test_search_basic_query_json_response
```

### Run Tests Matching Pattern
```bash
pytest -k "search"        # Run all tests with 'search' in name
pytest -k "htmx"          # Run all HTMX-related tests
pytest -k "not slow"      # Exclude slow tests
```

## Expected Output

```
================================ test session starts ================================
collected 42 items

tests/test_concept.py::TestConceptDetailEndpoint ........ [33%]
tests/test_main.py::TestIndexEndpoint ............. [64%]
tests/test_search.py::TestSearchEndpoint ............... [100%]

================================ 42 passed in 0.39s =================================
```

## Coverage Report

```
Name                     Stmts   Miss  Cover
--------------------------------------------
app/main.py                17      0   100%
app/models.py              62      0   100%
app/routers/concept.py     23      0   100%
app/routers/search.py      23      0   100%
app/schemas.py             35      0   100%
--------------------------------------------
TOTAL                     180      5    97%
```

## Test Organization

- `tests/test_search.py` - 15 tests for `/search/` endpoint
- `tests/test_concept.py` - 14 tests for `/concept/{id}` endpoint
- `tests/test_main.py` - 13 tests for `/` endpoint
- `tests/conftest.py` - Shared fixtures

## Common Issues

### Import Errors
Make sure you're running pytest from the project root:
```bash
cd /Users/smathias/pyOVT
pytest
```

### Missing Dependencies
Install test requirements:
```bash
pip install pytest pytest-cov httpx
```

## What's Tested

- All FastAPI endpoints
- HTMX request handling
- Query parameters and filters
- Error cases (404, 422)
- Database query mocking
- Response formats (JSON, HTML)
- Edge cases and validation

## Next Steps

See `tests/README.md` for comprehensive documentation.
