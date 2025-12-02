#!/usr/bin/env python3
"""Check embedding generation progress."""
import os
import psycopg2

DB_USER = os.getenv("DB_USER", "smathias")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "cdm")
DB_PORT = os.getenv("DB_PORT", "5432")

try:
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, host=DB_HOST, port=DB_PORT)

    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE ce.concept_id IS NOT NULL) as embedded_count,
                COUNT(*) as total_standard_concepts,
                ROUND(100.0 * COUNT(*) FILTER (WHERE ce.concept_id IS NOT NULL) / COUNT(*), 2) as percent_complete
            FROM concept c
            LEFT JOIN concept_embedding ce ON c.concept_id = ce.concept_id
            WHERE c.standard_concept = 'S'
              AND c.concept_name IS NOT NULL
              AND c.concept_name != ''
        """)
        stats = cur.fetchone()

        print(f"Embedding Generation Progress")
        print(f"=" * 50)
        print(f"Embedded: {stats[0]:,} / {stats[1]:,}")
        print(f"Progress: {stats[2]}%")
        print(f"Remaining: {stats[1] - stats[0]:,}")

    conn.close()
except Exception as e:
    print(f"Error: {e}")
