# OHDSI Vocabulary Tool

A full-stack web application to browse and search the OHDSI standardized vocabulary. Built with FastAPI, HTMX, PostgreSQL, and powered by semantic search with vector embeddings.

## Features

### Search Capabilities
- **Semantic Search** (Phase 3): Find medical concepts using natural language and colloquial terms
  - Vector embeddings with sentence-transformers (all-MiniLM-L6-v2)
  - 2.76M concepts with 384-dimensional embeddings
  - pgvector for fast similarity search
  - Example: "sugar disease" → finds "Diabetes mellitus"
- **Fuzzy Search** (Phase 1): Finds concepts even with typos (using `pg_trgm`)
- **Exact/Partial Search**: Traditional substring matching (ILIKE)
- **Multi-Field Search** (Phase 2): Search both concept names and concept codes

### Advanced Features
- **Relationship Navigation** (Phase 2): Explore concept hierarchies
  - View ancestors (parent concepts)
  - View descendants (child concepts)
  - See all concept relationships (Maps to, Subsumes, etc.)
- **Smart Filters**: Filter by Vocabulary, Domain, and Standard Concepts
- **All filters work with all search modes** (exact, fuzzy, and semantic)

### User Interface
- **Modern Dark-Mode Design**: Premium UI with HTMX for smooth interactions
- **Search Mode Indicators**: Clear visual feedback showing which search mode is active
- **Interactive Exploration**: Click through concept relationships and hierarchies

### API
- **Full REST API**: Complete API documentation with interactive testing
- **JSON Responses**: All endpoints support JSON for programmatic access

## Prerequisites

- Python 3.8+
- PostgreSQL 16+ with OHDSI CDM database
- **Required PostgreSQL Extensions**:
  - `pg_trgm` - for fuzzy search
  - `pgvector` - for semantic search (v0.8.0+)

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd pyOVT
```

### 2. Set Up Python Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Set Up PostgreSQL Extensions

**Install pgvector** (if not already installed):
```bash
# macOS with Homebrew
brew install postgresql@16

# Compile pgvector from source
cd /tmp
git clone --branch v0.8.1 https://github.com/pgvector/pgvector.git
cd pgvector
export PG_CONFIG=/opt/homebrew/opt/postgresql@16/bin/pg_config
make
make install
```

**Enable extensions in your database**:
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS vector;
```

### 4. Run Database Migrations
```bash
# Create concept_embedding table
psql -U smathias -d cdm -f migrations/001_create_concept_embedding.sql
```

### 5. Generate Embeddings (One-Time Setup)

**Note**: This is required for semantic search functionality.

```bash
# Test run (dry-run mode)
python scripts/generate_embeddings.py --dry-run

# Full generation (takes ~1-1.5 hours for 2.76M concepts)
python scripts/generate_embeddings.py --batch-size 1000

# Resume after interruption
python scripts/generate_embeddings.py --resume --batch-size 1000

# Monitor progress
python scripts/check_embedding_progress.py
```

### 6. Create Vector Index (After Embeddings Complete)
```bash
psql -U smathias -d cdm -f migrations/002_create_vector_index.sql
```

### 7. Validate Installation (Optional)
```bash
python scripts/validate_embeddings.py
```

## Configuration

Configure database connection via environment variables:

- `DB_USER` (default: `smathias`)
- `DB_PASSWORD` (default: empty)
- `DB_HOST` (default: `localhost`)
- `DB_NAME` (default: `cdm`)
- `DB_PORT` (default: `5432`)

## Running the Application

```bash
# Activate virtual environment
source .venv/bin/activate

# Start the server
uvicorn app.main:app --reload

# Open browser
open http://localhost:8000
```

## Usage Examples

### Search Modes

**Semantic Search** - Find concepts by meaning:
```
Query: "sugar disease"
Results: Diabetes, Diabetes mellitus, Disorder of glucose regulation

Query: "heart attack"
Results: Myocardial infarction, Acute myocardial infarction, ...
```

**Fuzzy Search** - Typo-tolerant:
```
Query: "diabetis" (typo)
Results: Diabetes mellitus, Diabetic, ...
```

**Exact Search** - Traditional substring matching:
```
Query: "type 2"
Results: Type 2 diabetes mellitus, ...
```

**Multi-Field Search** - Search names and codes:
```
Query: "73211009" (SNOMED code)
Results: Diabetes mellitus [73211009]
```

### Using Filters

All search modes support:
- **Vocabulary Filter**: SNOMED, ICD10CM, RxNorm, LOINC, etc.
- **Domain Filter**: Condition, Drug, Procedure, etc.
- **Standard Concepts Only**: Filter to standard concepts (standard_concept='S')

## API Documentation

Interactive API documentation available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### API Examples

```bash
# Semantic search
curl "http://localhost:8000/search/?q=sugar disease&semantic=true&limit=10"

# Fuzzy search with filters
curl "http://localhost:8000/search/?q=diabetis&fuzzy=true&vocabulary_id=SNOMED&standard_only=true"

# Get concept details with relationships
curl "http://localhost:8000/concept/201820"
```

## Testing

```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/test_search.py::TestSemanticSearch -v
pytest tests/test_search.py::TestSearchEndpoint -v
pytest tests/test_concept.py -v

# Run with coverage
pytest --cov=app --cov-report=term-missing
```

## Project Structure

```
pyOVT/
├── app/
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database connection
│   ├── models.py            # SQLAlchemy models (including ConceptEmbedding)
│   ├── schemas.py           # Pydantic schemas
│   ├── routers/
│   │   ├── search.py        # Search endpoint (exact/fuzzy/semantic)
│   │   └── concept.py       # Concept detail endpoint
│   ├── templates/           # Jinja2 templates
│   │   ├── base.html
│   │   ├── index.html       # Search interface
│   │   ├── search_results.html
│   │   └── concept_detail.html
│   └── static/
│       └── style.css        # Custom styling
├── migrations/
│   ├── 001_create_concept_embedding.sql
│   └── 002_create_vector_index.sql
├── scripts/
│   ├── generate_embeddings.py    # Generate vector embeddings
│   ├── validate_embeddings.py    # Validate embedding quality
│   └── check_embedding_progress.py
├── tests/
│   ├── conftest.py
│   ├── test_search.py       # Search endpoint tests
│   └── test_concept.py      # Concept detail tests
└── requirements.txt
```

## Dependencies

### Core Framework
- fastapi
- uvicorn
- sqlalchemy
- psycopg2-binary
- jinja2
- pydantic
- python-dotenv

### Semantic Search (Phase 3)
- sentence-transformers>=2.2.0
- torch>=2.0.0
- pgvector>=0.2.0
- tqdm>=4.65.0
- tenacity>=8.2.0

## Performance

- **Embedding Generation**: ~1000 concepts/second (Apple Silicon MPS)
- **Search Performance**: <100ms for semantic search (with IVFFlat index)
- **Database Size**: ~2.76M standard concepts with embeddings
- **Index Parameters**:
  - IVFFlat lists: 1700
  - Probes: 20

## Development Roadmap

### Completed
- ✅ Phase 1: Multi-field search (names + codes)
- ✅ Phase 2: Relationship-powered navigation
- ✅ Phase 3: Semantic search with vector embeddings

### Future Enhancements
- 🔄 BioBERT model upgrade for medical domain specialization
- 🔄 Concept set management
- 🔄 Export functionality
- 🔄 Search history and favorites

## Contributing

Contributions welcome! Please ensure:
1. All tests pass (`pytest`)
2. Code follows existing style
3. New features include tests
4. Documentation is updated

## License

[Your License Here]

## Acknowledgments

- **OHDSI Community**: For the standardized vocabulary
- **pgvector**: Fast vector similarity search
- **sentence-transformers**: High-quality embeddings
