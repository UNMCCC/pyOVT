# OHDSI Vocabulary Tool - Test Suite Summary

## Overview

A comprehensive test suite has been created for the OHDSI Vocabulary Tool FastAPI application with **57 tests** using **live database testing** against a real PostgreSQL database with OHDSI CDM vocabulary data.

## Testing Approach

### Live Database Testing

The test suite has been **refactored from mocked database sessions to live database testing**:

- **Real Database Queries**: Tests query actual OHDSI vocabulary data from PostgreSQL
- **Transaction Rollback**: Each test runs in an isolated transaction that is rolled back after completion
- **No Data Modification**: All tests are read-only and safe to run against production databases
- **Dynamic Test Data**: Fixtures query the database for valid test data, ensuring tests work with any OHDSI CDM instance

### Key Advantages

1. **Realistic Testing**: Tests verify actual database queries and real data scenarios
2. **Database Safety**: Transaction rollback ensures no permanent changes
3. **Flexibility**: Tests adapt to different OHDSI vocabulary database instances
4. **Test Isolation**: Each test starts with a clean transaction state
5. **Performance**: Session-scoped fixtures minimize redundant database queries

## Test Results

```
================================ test session starts ================================
57 total tests

Test Distribution:
- Search endpoint:  20 tests
- Concept endpoint: 20 tests
- Index endpoint:   17 tests
```

## Test Coverage by Module

| Test File           | Tests | Description                                    |
|---------------------|-------|------------------------------------------------|
| test_search.py      | 20    | Search endpoint with fuzzy matching & filters  |
| test_concept.py     | 20    | Concept detail with hierarchy & relationships  |
| test_main.py        | 17    | Index page with vocabularies & domains         |
| **TOTAL**           | **57**| **Complete endpoint coverage**                 |

## Files Modified/Created

### Core Test Files

1. **tests/conftest.py** (263 lines)
   - Removed all mock fixtures
   - Added real database session fixtures with transaction rollback
   - Created dynamic fixtures that query database for valid test data
   - Session-scoped fixtures for performance optimization

2. **tests/test_search.py** (447 lines)
   - Refactored from 15 to 20 tests
   - Uses live database with actual search queries
   - Tests fuzzy matching with pg_trgm against real data
   - Flexible assertions that work with any database content

3. **tests/test_concept.py** (505 lines)
   - Refactored from 14 to 20 tests
   - Queries real concepts, ancestors, descendants, and relationships
   - Tests hierarchy display with actual database data
   - Performance testing with real database queries

4. **tests/test_main.py** (442 lines)
   - Refactored from 13 to 17 tests
   - Queries actual vocabularies and domains from database
   - Tests display of real reference data
   - Graceful handling of variable database content

### Documentation

5. **tests/README.md** (528 lines)
   - Completely rewritten for live database testing approach
   - Comprehensive guide on running tests with real database
   - Database requirements and configuration
   - Troubleshooting guide for common issues
   - CI/CD integration examples

6. **TEST_SUMMARY.md** (This file)
   - Updated to reflect live database testing approach
   - New test breakdown and coverage metrics
   - Migration guide from mocked to live testing

## Test Breakdown

### Search Endpoint Tests (20 tests)

#### Basic Functionality
- Basic search with JSON response
- Search with HTMX header (HTML response)
- Response model field validation
- Valid concept IDs returned

#### Filtering & Parameters
- Vocabulary filter
- Domain filter
- Combined filters (vocabulary + domain)
- Custom limit parameter
- Default limit behavior (50)
- Limit boundary testing

#### Search Behavior
- Similarity-based ordering (pg_trgm)
- Case insensitivity
- Special characters handling
- Very short term search (single character)
- Numeric query search

#### Error Handling
- Empty query validation error (422)
- Missing query parameter validation (422)
- No results scenario

### Concept Detail Endpoint Tests (20 tests)

#### Basic Retrieval
- Successful concept retrieval
- HTMX request handling
- Display basic concept information
- HTML structure validation
- Template response (not JSON)

#### Error Handling
- 404 for non-existent concepts
- Invalid ID type validation (422)
- Zero ID handling (404)
- Negative ID handling (404)

#### Hierarchy & Relationships
- Concept with hierarchy (ancestors/descendants)
- Ancestors query functionality
- Descendants query functionality (direct children)
- Complete hierarchy display
- Concepts with relationships

#### Data Variety
- Standard vs non-standard concepts
- Concepts from different vocabularies
- Concepts from different domains
- Special characters in concept names

#### Performance
- Performance testing (< 5 seconds)

### Index Endpoint Tests (17 tests)

#### Basic Functionality
- Successful page load
- HTML structure validation
- Template response (not JSON)
- HTMX compatibility

#### Content Display
- Vocabularies display
- Domains display
- Multiple vocabularies rendering
- Multiple domains rendering
- Vocabulary details display
- Domain details display

#### Data Ordering
- Vocabularies ordering
- Domains ordering

#### Edge Cases
- Empty database graceful handling
- Search form presence

#### Data Validation
- Vocabulary count validation
- Domain count validation

#### Performance
- Performance testing (< 3 seconds)

## Database Transaction Strategy

### Implementation

```python
@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a database session with transaction rollback for test isolation."""
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

- **No Permanent Changes**: All database modifications are rolled back
- **Test Isolation**: Each test operates in a clean transaction
- **Production Safe**: Can run against live databases without risk
- **Fast Cleanup**: No need to manually reset database state

## Dynamic Test Fixtures

### Session-Scoped Fixtures

These fixtures query the database once per test session for optimal performance:

| Fixture                  | Purpose                                           |
|--------------------------|---------------------------------------------------|
| `db_engine`              | Database engine (reused across all tests)         |
| `sample_concept_id`      | A valid concept ID from the database              |
| `sample_vocabulary_id`   | A valid vocabulary ID from the database           |
| `sample_domain_id`       | A valid domain ID from the database               |
| `concept_with_hierarchy` | A concept with both ancestors and descendants     |
| `searchable_term`        | A search term that returns results                |

### Function-Scoped Fixtures

| Fixture      | Purpose                                              |
|--------------|------------------------------------------------------|
| `db_session` | Database session with transaction rollback           |
| `client`     | TestClient with real database dependency override    |

## Migration from Mocked to Live Testing

### What Changed

**Before (Mocked Testing):**
```python
def test_search(client, mock_db, sample_concepts_list, mock_query_chain):
    # Setup mock
    mock_query_chain.all.return_value = sample_concepts_list
    mock_db.query.return_value = mock_query_chain

    response = client.get("/search/?q=hypertension")
    assert response.status_code == 200
    assert len(response.json()) == 3  # Fixed number
```

**After (Live Database Testing):**
```python
def test_search(client, searchable_term):
    # Query real database
    response = client.get(f"/search/?q={searchable_term}")

    assert response.status_code == 200
    assert len(response.json()) > 0  # Flexible assertion
```

### Key Differences

1. **No More Mocks**: Removed all mock_db, mock_query_chain fixtures
2. **Real Queries**: Tests execute actual SQL queries against PostgreSQL
3. **Flexible Assertions**: Tests adapt to variable database content
4. **Dynamic Data**: Fixtures query database for valid test data
5. **Transaction Safety**: Rollback ensures no permanent changes

## Database Requirements

### Required Tables

- `concept` - OHDSI vocabulary concepts
- `vocabulary` - Vocabulary reference data
- `domain` - Domain reference data
- `concept_class` - Concept class reference data
- `concept_ancestor` - Concept hierarchy relationships
- `concept_relationship` - Concept relationships
- `relationship` - Relationship types

### Required Extensions

- `pg_trgm` - PostgreSQL trigram extension for fuzzy search

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

### Database Configuration

Default connection (can be overridden via environment variables):

```python
DB_USER = "smathias"
DB_HOST = "localhost"
DB_NAME = "cdm"
DB_PORT = "5432"
```

## Running the Tests

### Basic Usage

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_search.py

# Run with coverage
pytest --cov=app --cov-report=term-missing
```

### Prerequisites

1. PostgreSQL database with OHDSI CDM vocabulary data
2. Database connection configured (default: localhost/cdm)
3. Required Python packages installed

```bash
pip install pytest pytest-cov httpx
```

## Test Isolation & Safety

### Read-Only Operations

- Tests only perform SELECT queries
- No INSERT, UPDATE, or DELETE operations
- Safe to run against production databases

### Transaction Rollback

- Each test runs in an isolated transaction
- All changes are rolled back automatically
- No cleanup code required

### Concurrent Testing

- Tests can run in parallel (with appropriate pytest plugins)
- Each test has its own database session
- No test interference or race conditions

## Performance Metrics

### Expected Test Execution Times

- **Full Suite**: 2-10 seconds (depending on database size/location)
- **Single Test**: 50-500ms (varies by database query complexity)
- **Session Fixtures**: One-time cost at session start

### Optimization Strategies

1. **Session Fixtures**: Expensive queries cached for session
2. **Local Database**: Run against local PostgreSQL for best performance
3. **Proper Indexes**: Ensure database has standard OHDSI indexes
4. **Limited Queries**: Session fixtures query once, tests reuse data

## Common Testing Patterns

### Flexible Assertions

```python
# Good: Works with any database
if len(results) > 0:
    assert results[0]["concept_id"] > 0

# Avoid: Hardcoded values specific to your database
assert results[0]["concept_id"] == 192671
```

### Handling Missing Data

```python
# Skip test if required data doesn't exist
if not relationship:
    pytest.skip("No concept relationships found in database")
```

### Querying Real Data

```python
# Get actual concept from database
concept = db_session.query(Concept).filter(
    Concept.concept_id == sample_concept_id
).first()

# Verify endpoint displays this concept
response = client.get(f"/concept/{sample_concept_id}")
assert concept.concept_name in response.text
```

## Troubleshooting

### Database Connection Issues

1. Verify PostgreSQL is running: `pg_isready`
2. Check database exists: `psql -l | grep cdm`
3. Test connection: `psql -U smathias -d cdm`

### Missing Test Data

1. Verify OHDSI tables are populated
2. Check pg_trgm extension is installed
3. Ensure at least some standard concepts exist

### Slow Test Execution

1. Run tests against local database
2. Verify database has proper indexes
3. Check database query performance

## Continuous Integration

Tests can be integrated into CI/CD pipelines with a PostgreSQL service:

```yaml
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_DB: cdm
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_pass
```

See `tests/README.md` for complete GitHub Actions example.

## Best Practices Demonstrated

1. **Transaction Isolation**: Rollback ensures clean state
2. **Dynamic Fixtures**: Adapt to any OHDSI database
3. **Type Safety**: Full type hints throughout
4. **Documentation**: Comprehensive docstrings
5. **Flexible Assertions**: Work with variable data
6. **Performance**: Session-scoped fixtures optimize queries
7. **Error Handling**: Graceful skips for missing data
8. **Realistic Testing**: Actual database queries

## Code Quality

- **PEP 8 Compliant**: Follows Python style guidelines
- **Type Checked**: All functions have type hints
- **Well Documented**: Docstrings for all test functions
- **Organized**: Logical test class structure
- **Consistent**: Uniform coding patterns

## Future Enhancements

Potential additions to the test suite:

1. **Parallel Testing**: pytest-xdist for faster execution
2. **API Contract Tests**: Schema validation
3. **Load Testing**: Performance under concurrent requests
4. **Integration Tests**: End-to-end user workflows
5. **Mutation Testing**: Code coverage quality validation

## Dependencies

The test suite requires:

- pytest >= 7.4.0
- pytest-cov >= 4.1.0 (optional, for coverage)
- httpx >= 0.24.0 (for TestClient)
- SQLAlchemy >= 2.0.0
- PostgreSQL with OHDSI CDM data

## Conclusion

This comprehensive test suite provides robust coverage of the OHDSI Vocabulary Tool using **live database testing**. The refactoring from mocked to live database testing offers:

- **Higher Confidence**: Tests verify actual database behavior
- **Better Coverage**: Real queries against real data
- **Production Safety**: Transaction rollback prevents data modification
- **Flexibility**: Works with any OHDSI vocabulary database
- **Maintainability**: No mock setup/teardown code
- **Realistic Testing**: True integration testing

All endpoints are thoroughly tested with both success and error scenarios, real database queries, flexible assertions, and comprehensive documentation.

## Summary Statistics

- **Total Tests**: 57
- **Test Files**: 3
- **Fixtures**: 8 (6 session-scoped, 2 function-scoped)
- **Lines of Test Code**: ~1,400
- **Documentation**: 528 lines (README.md)
- **Testing Approach**: Live database with transaction rollback
- **Expected Execution Time**: 2-10 seconds
- **Database Safety**: Read-only with automatic rollback
