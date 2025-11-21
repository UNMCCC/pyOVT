# OHDSI Vocabulary Tool

A full-stack web application to browse and search the OHDSI standardized vocabulary. Built with FastAPI, HTMX, and PostgreSQL.

## Features

- **Fuzzy Search**: Finds concepts even with typos (using `pg_trgm`).
- **Filters**: Filter by Vocabulary and Domain.
- **Concept Details**: View relationships, ancestors, and descendants.
- **Premium UI**: Modern, dark-mode design.
- **API**: Full REST API documentation available.

## Prerequisites

- Python 3.8+
- PostgreSQL with `cdm` database.
- `pg_trgm` extension enabled in PostgreSQL.

## Installation

1. Clone the repository.
2. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: `requirements.txt` content listed below)*

## Configuration

The application connects to the `cdm` database on `localhost` by default. You can configure connection details via environment variables:

- `DB_USER` (default: `smathias`)
- `DB_PASSWORD` (default: empty)
- `DB_HOST` (default: `localhost`)
- `DB_NAME` (default: `cdm`)
- `DB_PORT` (default: `5432`)

## Running the Application

1. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```
2. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```
3. Open your browser and navigate to:
   [http://localhost:8000](http://localhost:8000)

## API Documentation

Interactive API documentation is available at:
[http://localhost:8000/docs](http://localhost:8000/docs)

## Dependencies

- fastapi
- uvicorn
- sqlalchemy
- psycopg2-binary
- jinja2
- python-multipart
- requests
