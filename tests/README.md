# OHDSI Vocabulary Tool - Test Suite

Comprehensive test suite for the OHDSI Vocabulary Tool FastAPI application using a live PostgreSQL database.

## Overview

This test suite provides comprehensive coverage for all FastAPI endpoints in the application using **live database testing** against a real PostgreSQL database with OHDSI CDM vocabulary data.

- **Search endpoint** (`/search/`) - Tests for fuzzy search functionality with filters
- **Concept detail endpoint** (`/concept/{concept_id}`) - Tests for concept hierarchy and relationships
- **Index endpoint** (`/`) - Tests for the main landing page with vocabularies and domains

## Key Features

- **Live Database Testing**: Tests query actual OHDSI vocabulary data
- **Transaction Rollback**: Each test runs in a transaction that is rolled back, ensuring no data modification
- **Flexible Assertions**: Tests work with any OHDSI vocabulary database instance
- **Dynamic Test Data**: Fixtures query the database for valid test data
- **Type Safety**: Full type hints throughout test suite

## Test Structure

```
tests/
├── __init__.py           # Package marker
├── conftest.py           # Shared pytest fixtures and database session setup
├── test_search.py        # Tests for search endpoint (20 tests)
├── test_concept.py       # Tests for concept detail endpoint (20 tests)
├── test_main.py          # Tests for index endpoint (17 tests)
└── README.md            # This file
```

## Prerequisites

### Database Requirements

Tests require a live PostgreSQL database with OHDSI CDM vocabulary data:

1. **PostgreSQL Database**: Running instance with OHDSI CDM schema
2. **Vocabulary Tables**: Standard OHDSI vocabulary tables populated with data:
   - `concept`
   - `vocabulary`
   - `domain`
   - `concept_class`
   - `concept_ancestor`
   - `concept_relationship`
   - `relationship`

3. **Database Access**: Connection configured via environment variables or defaults:
   - Default database: `cdm`
   - Default user: `smathias`
   - Default host: `localhost`
   - Default port: `5432`

### Install Test Dependencies

```bash
pip install -r requirements.txt
# or if you have separate test requirements:
pip install pytest pytest-cov httpx
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Files

```bash
# Search endpoint tests
pytest tests/test_search.py

# Concept endpoint tests
pytest tests/test_concept.py

# Index endpoint tests
pytest tests/test_main.py
```

### Run Specific Test Classes or Functions

```bash
# Run a specific test class
pytest tests/test_search.py::TestSearchEndpoint

# Run a specific test function
pytest tests/test_search.py::TestSearchEndpoint::test_search_basic_query_json_response
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Coverage Report

```bash
# Terminal coverage report
pytest --cov=app --cov-report=term-missing

# HTML coverage report
pytest --cov=app --cov-report=html
# Then open htmlcov/index.html in a browser
```

### Skip Slow Tests

```bash
pytest -m "not slow"
```

### Run Tests with Output

```bash
# Show print statements
pytest -s

# Show detailed output
pytest -vv
```

## Test Coverage

### Search Endpoint (`/search/`) - 20 Tests

- Basic search with JSON response
- Search with HTMX header (HTML response)
- Vocabulary filter
- Domain filter
- Combined filters (vocabulary + domain)
- Custom limit parameter
- Default limit behavior (50)
- Empty query validation error
- Missing query parameter validation
- No results scenario
- Similarity-based ordering (pg_trgm)
- Special characters handling
- Case insensitivity
- Response model field validation
- Valid concept IDs returned
- Very short term search
- Numeric query search
- Limit boundary testing

### Concept Detail Endpoint (`/concept/{concept_id}`) - 20 Tests

- Successful concept retrieval
- HTMX request handling
- 404 for non-existent concepts
- Concept with hierarchy (ancestors/descendants)
- Invalid ID type validation (422 error)
- Zero ID handling (404)
- Negative ID handling (404)
- Display basic concept information
- Concepts with relationships
- Standard vs non-standard concepts
- Concepts from different vocabularies
- Concepts from different domains
- Ancestors query functionality
- Descendants query functionality (direct children)
- Complete hierarchy display
- HTML structure validation
- Template response (not JSON)
- Performance testing
- Special characters in concept names

### Index Endpoint (`/`) - 17 Tests

- Successful page load
- Vocabularies display
- Domains display
- Multiple vocabularies rendering
- Multiple domains rendering
- Vocabularies ordering
- Domains ordering
- HTML structure validation
- HTMX compatibility
- Template response (not JSON)
- Vocabulary details display
- Domain details display
- Empty database graceful handling
- Search form presence
- Performance testing
- Vocabulary count validation
- Domain count validation

## Database Transaction Strategy

### Test Isolation

Tests use **transaction rollback** to ensure database safety:

```python
@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    # Create a connection and begin a transaction
    connection = db_engine.connect()
    transaction = connection.begin()

    # Create a session bound to this connection
    session = SessionLocal(bind=connection)

    try:
        yield session
    finally:
        # Rollback the transaction to undo any changes
        session.close()
        transaction.rollback()
        connection.close()
```

### Benefits

1. **No Data Modification**: All database changes are rolled back
2. **Test Isolation**: Each test starts with a clean state
3. **Safe Execution**: Can run against production databases
4. **Fast Execution**: No need to reset database between tests

## Dynamic Test Fixtures

### Session-Scoped Fixtures

These fixtures query the database once per test session to find valid test data:

- **`sample_concept_id`**: A valid concept ID (preferably SNOMED standard concept)
- **`sample_vocabulary_id`**: A valid vocabulary ID from the database
- **`sample_domain_id`**: A valid domain ID from the database
- **`concept_with_hierarchy`**: A concept with both ancestors and descendants
- **`searchable_term`**: A search term that returns results

### Example Usage

```python
def test_get_concept_success(
    self,
    client: TestClient,
    sample_concept_id: int,
) -> None:
    response = client.get(f"/concept/{sample_concept_id}")
    assert response.status_code == 200
```

## Configuration

### Database Connection

Tests use the same database connection as the application (configured in `app/database.py`):

```python
# Environment variables (optional)
DB_USER = os.getenv("DB_USER", "smathias")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "cdm")
DB_PORT = os.getenv("DB_PORT", "5432")
```

### Override Database for Testing

If you need to use a different database for testing, set environment variables before running tests:

```bash
export DB_NAME=cdm_test
export DB_HOST=localhost
pytest
```

## Writing New Tests

### Test Function Template

```python
def test_new_feature(
    self,
    client: TestClient,
    db_session: Session,
    sample_concept_id: int,
) -> None:
    """
    Test description here.

    Args:
        client: FastAPI test client
        db_session: Database session
        sample_concept_id: A valid concept ID from the database
    """
    # Arrange: Get data from database if needed
    from app.models import Concept
    concept = db_session.query(Concept).filter(
        Concept.concept_id == sample_concept_id
    ).first()

    # Act: Make the request
    response = client.get(f"/concept/{sample_concept_id}")

    # Assert: Verify expectations
    assert response.status_code == 200
    assert concept.concept_name in response.text
```

### Best Practices

1. **Use Fixtures**: Leverage existing fixtures for test data
2. **Flexible Assertions**: Don't hardcode specific values from your database
3. **Handle Missing Data**: Use `pytest.skip()` if required data isn't available
4. **Test Real Scenarios**: Query actual database for realistic test data
5. **Type Hints**: Include type annotations for all parameters
6. **Docstrings**: Document what each test validates
7. **AAA Pattern**: Arrange, Act, Assert

### Handling Variable Data

Since tests run against live data, assertions should be flexible:

```python
# Good: Flexible assertion
if len(results) > 0:
    assert results[0]["concept_id"] > 0

# Bad: Hardcoded assertion (will fail on different databases)
assert results[0]["concept_id"] == 192671
```

## Common Patterns

### Testing with Real Database Data

```python
def test_search_returns_results(
    self,
    client: TestClient,
    searchable_term: str,
) -> None:
    response = client.get(f"/search/?q={searchable_term}")

    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0  # Should find at least one result
```

### Testing Against Actual Concepts

```python
def test_concept_display(
    self,
    client: TestClient,
    db_session: Session,
    sample_concept_id: int,
) -> None:
    # Get the actual concept from database
    concept = db_session.query(Concept).filter(
        Concept.concept_id == sample_concept_id
    ).first()

    # Verify the endpoint displays this concept
    response = client.get(f"/concept/{sample_concept_id}")
    assert concept.concept_name in response.text
```

### Skipping Tests When Data is Missing

```python
def test_with_specific_data(
    self,
    client: TestClient,
    db_session: Session,
) -> None:
    # Check if required data exists
    relationship = db_session.query(ConceptRelationship).first()
    if not relationship:
        pytest.skip("No concept relationships found in database")

    # Continue with test...
```

## Troubleshooting

### Database Connection Issues

If tests fail with connection errors:

1. Verify PostgreSQL is running: `pg_isready`
2. Check database exists: `psql -l | grep cdm`
3. Verify connection settings in `app/database.py`
4. Test connection manually: `psql -U smathias -d cdm`

### No Test Data Found

If tests skip due to missing data:

1. Verify OHDSI vocabulary tables are populated
2. Check that pg_trgm extension is installed for search: `CREATE EXTENSION IF NOT EXISTS pg_trgm;`
3. Ensure at least some standard concepts exist

### Tests Running Slowly

Live database tests are slower than mocked tests. To improve performance:

1. Ensure database has proper indexes
2. Run tests on a local database instance
3. Use session-scoped fixtures for expensive queries
4. Consider using a smaller test database

### Import Errors

Ensure you're running pytest from the project root:

```bash
cd /Users/smathias/pyOVT
pytest
```

### Transaction Issues

If you see transaction-related errors:

1. Check that tests don't call `db_session.commit()`
2. Verify rollback is working in conftest.py
3. Ensure no nested transactions are created

## Performance Considerations

- **Session Fixtures**: Use `scope="session"` for fixtures that query static reference data
- **Function Fixtures**: Use `scope="function"` for database sessions (required for transaction rollback)
- **Test Execution Time**: Expect ~2-10 seconds for full test suite (depending on database size)

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: cdm
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Load test data
        run: |
          # Load OHDSI vocabulary data into PostgreSQL
          psql -h localhost -U test_user -d cdm -f test_data.sql
        env:
          PGPASSWORD: test_pass

      - name: Run tests
        run: |
          pytest --cov=app --cov-report=xml
        env:
          DB_USER: test_user
          DB_PASSWORD: test_pass
          DB_HOST: localhost
          DB_NAME: cdm

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Security Notes

- Tests use **read-only** operations with transaction rollback
- Safe to run against production databases (no data modification)
- Ensure database credentials are properly secured in CI/CD
- Consider using read-only database user for tests

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)
- [OHDSI CDM Documentation](https://ohdsi.github.io/CommonDataModel/)

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure all tests pass: `pytest`
3. Check coverage: `pytest --cov=app`
4. Use flexible assertions that work with any OHDSI database
5. Document any specific database requirements

## Summary

This test suite provides comprehensive coverage of the OHDSI Vocabulary Tool using **live database testing**. Tests are:

- **Robust**: Work with any OHDSI vocabulary database
- **Safe**: Use transaction rollback to prevent data modification
- **Flexible**: Dynamic fixtures adapt to available data
- **Fast**: Session-scoped fixtures minimize database queries
- **Well-documented**: Clear docstrings and type hints throughout
