#!/usr/bin/env python3
"""Verify pgvector extension is available and install if needed."""
import psycopg2
import os
import sys

DB_USER = os.getenv("DB_USER", "smathias")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "cdm")
DB_PORT = os.getenv("DB_PORT", "5432")

try:
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, host=DB_HOST, port=DB_PORT)

    with conn.cursor() as cur:
        # Check if extension is available
        cur.execute("SELECT EXISTS(SELECT 1 FROM pg_available_extensions WHERE name = 'vector')")
        available = cur.fetchone()[0]

        if not available:
            print("ERROR: pgvector extension not available")
            print("Installation required: https://github.com/pgvector/pgvector")
            sys.exit(1)

        # Check if installed
        cur.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
        installed = cur.fetchone()[0]

        if not installed:
            print("pgvector available but not installed. Installing...")
            cur.execute("CREATE EXTENSION vector")
            conn.commit()
            print("SUCCESS: pgvector extension installed")
        else:
            cur.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            version = cur.fetchone()[0]
            print(f"SUCCESS: pgvector v{version} already installed")

    conn.close()
except Exception as e:
    print(f"ERROR: Failed to check pgvector: {e}")
    sys.exit(1)
