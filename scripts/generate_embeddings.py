#!/usr/bin/env python3
"""
Generate vector embeddings for OHDSI concept names using sentence-transformers.

This script processes standard concepts only to reduce scope.
Embeddings are stored in the concept_embedding table for semantic search.

Usage:
    python scripts/generate_embeddings.py [--dry-run] [--batch-size 1000] [--resume]

Examples:
    # Test run without database writes
    python scripts/generate_embeddings.py --dry-run

    # Generate all embeddings
    python scripts/generate_embeddings.py

    # Resume after interruption
    python scripts/generate_embeddings.py --resume

    # Use smaller batches (if running out of memory)
    python scripts/generate_embeddings.py --batch-size 500
"""

import argparse
import logging
import os
import sys
from typing import List, Tuple
from datetime import datetime

import psycopg2
from psycopg2.extras import execute_batch
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from tenacity import retry, stop_after_attempt, wait_exponential

# Configuration from environment
DB_USER = os.getenv("DB_USER", "smathias")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "cdm")
DB_PORT = os.getenv("DB_PORT", "5432")

MODEL_NAME = "all-MiniLM-L6-v2"
MODEL_VERSION = "v1"

def setup_logging(log_file: str = "embedding_generation.log"):
    """Configure logging to file and console"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def get_db_connection():
    """Create database connection"""
    if DB_PASSWORD:
        conn_string = f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} host={DB_HOST} port={DB_PORT}"
    else:
        conn_string = f"dbname={DB_NAME} user={DB_USER} host={DB_HOST} port={DB_PORT}"

    return psycopg2.connect(conn_string)

def check_pgvector_available(conn):
    """Verify pgvector extension is installed"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS(
                SELECT 1 FROM pg_extension WHERE extname = 'vector'
            )
        """)
        available = cur.fetchone()[0]
        if not available:
            raise RuntimeError(
                "pgvector extension not installed. "
                "Run: CREATE EXTENSION vector; "
                "Or see: https://github.com/pgvector/pgvector"
            )
    logging.info("pgvector extension verified")

def check_concept_embedding_table_exists(conn):
    """Verify concept_embedding table exists"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'concept_embedding'
            )
        """)
        exists = cur.fetchone()[0]
        if not exists:
            raise RuntimeError(
                "concept_embedding table does not exist. "
                "Run migration: migrations/001_create_concept_embedding.sql"
            )
    logging.info("concept_embedding table verified")

def get_concepts_to_embed(conn, resume: bool = False) -> List[Tuple[int, str]]:
    """
    Get list of (concept_id, concept_name) tuples that need embeddings.

    Args:
        conn: Database connection
        resume: If True, only get concepts without embeddings

    Returns:
        List of (concept_id, concept_name) tuples
    """
    with conn.cursor() as cur:
        if resume:
            # Only concepts without embeddings (for resuming interrupted runs)
            logging.info("Resume mode: fetching concepts without embeddings")
            cur.execute("""
                SELECT c.concept_id, c.concept_name
                FROM concept c
                LEFT JOIN concept_embedding ce ON c.concept_id = ce.concept_id
                WHERE c.standard_concept = 'S'
                  AND c.concept_name IS NOT NULL
                  AND c.concept_name != ''
                  AND ce.concept_id IS NULL
                ORDER BY c.concept_id
            """)
        else:
            # All standard concepts
            logging.info("Full mode: fetching all standard concepts")
            cur.execute("""
                SELECT concept_id, concept_name
                FROM concept
                WHERE standard_concept = 'S'
                  AND concept_name IS NOT NULL
                  AND concept_name != ''
                ORDER BY concept_id
            """)

        concepts = cur.fetchall()
        logging.info(f"Found {len(concepts)} concepts to process")
        return concepts

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def generate_embeddings_batch(model: SentenceTransformer, concept_names: List[str]):
    """
    Generate embeddings for a batch of concept names.
    Includes retry logic for transient failures.

    Args:
        model: Loaded SentenceTransformer model
        concept_names: List of concept names to embed

    Returns:
        numpy array of embeddings
    """
    try:
        embeddings = model.encode(
            concept_names,
            batch_size=32,  # Internal model batch size
            show_progress_bar=False,  # We have our own progress bar
            convert_to_numpy=True,
            normalize_embeddings=True  # Normalize for cosine similarity
        )
        return embeddings
    except Exception as e:
        logging.error(f"Error generating embeddings: {e}")
        raise

def insert_embeddings_batch(
    conn,
    concept_ids: List[int],
    embeddings,
    dry_run: bool = False
):
    """
    Insert batch of embeddings into database.

    Args:
        conn: Database connection
        concept_ids: List of concept IDs
        embeddings: numpy array of embeddings
        dry_run: If True, don't actually insert
    """
    if dry_run:
        logging.info(f"DRY RUN: Would insert {len(concept_ids)} embeddings")
        return

    with conn.cursor() as cur:
        # Prepare data for batch insert
        data = [
            (int(cid), emb.tolist(), MODEL_NAME, MODEL_VERSION)
            for cid, emb in zip(concept_ids, embeddings)
        ]

        # Use execute_batch for efficiency
        # page_size=100 is a good balance between memory and performance
        execute_batch(
            cur,
            """
            INSERT INTO concept_embedding (concept_id, embedding, model_name, model_version)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (concept_id) DO UPDATE
            SET embedding = EXCLUDED.embedding,
                model_name = EXCLUDED.model_name,
                model_version = EXCLUDED.model_version,
                generated_at = CURRENT_TIMESTAMP
            """,
            data,
            page_size=100
        )

    conn.commit()
    logging.info(f"Inserted {len(concept_ids)} embeddings")

def get_embedding_stats(conn):
    """Get statistics about embedding coverage"""
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
        return {
            'embedded': stats[0],
            'total': stats[1],
            'percent': stats[2]
        }

def main():
    parser = argparse.ArgumentParser(
        description='Generate vector embeddings for OHDSI concepts'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without inserting to database (for testing)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=1000,
        help='Number of concepts to process per batch (default: 1000)'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from previous run (only process concepts without embeddings)'
    )
    args = parser.parse_args()

    # Setup
    setup_logging()
    logging.info("="*60)
    logging.info("Starting embedding generation")
    logging.info(f"Model: {MODEL_NAME}")
    logging.info(f"Batch size: {args.batch_size}")
    logging.info(f"Dry run: {args.dry_run}")
    logging.info(f"Resume mode: {args.resume}")
    logging.info("="*60)

    # Load model
    logging.info(f"Loading model: {MODEL_NAME}")
    try:
        model = SentenceTransformer(MODEL_NAME)
        logging.info("Model loaded successfully")
    except Exception as e:
        logging.error(f"Failed to load model: {e}")
        sys.exit(1)

    # Connect to database
    logging.info("Connecting to database")
    try:
        conn = get_db_connection()
        logging.info("Database connection established")
    except Exception as e:
        logging.error(f"Failed to connect to database: {e}")
        sys.exit(1)

    try:
        # Verify prerequisites
        check_pgvector_available(conn)
        check_concept_embedding_table_exists(conn)

        # Get initial stats
        if args.resume:
            stats = get_embedding_stats(conn)
            logging.info(f"Current progress: {stats['embedded']}/{stats['total']} ({stats['percent']}%)")

        # Get concepts to process
        concepts = get_concepts_to_embed(conn, resume=args.resume)
        total = len(concepts)

        if total == 0:
            logging.info("No concepts to process. Exiting.")
            return

        logging.info(f"Processing {total:,} concepts")

        # Estimate time (very rough: ~100 concepts/second)
        est_minutes = (total / 100) / 60
        logging.info(f"Estimated time: {est_minutes:.1f} minutes")

        # Process in batches
        batch_size = args.batch_size
        errors = []

        with tqdm(total=total, desc="Generating embeddings", unit="concepts") as pbar:
            for i in range(0, total, batch_size):
                batch = concepts[i:i+batch_size]
                concept_ids = [c[0] for c in batch]
                concept_names = [c[1] for c in batch]

                try:
                    # Generate embeddings
                    embeddings = generate_embeddings_batch(model, concept_names)

                    # Insert into database
                    insert_embeddings_batch(
                        conn, concept_ids, embeddings, dry_run=args.dry_run
                    )

                    pbar.update(len(batch))

                except Exception as e:
                    error_msg = f"Error processing batch {i}-{i+len(batch)}: {e}"
                    logging.error(error_msg)
                    errors.append(error_msg)
                    # Continue with next batch
                    continue

        # Final stats
        if not args.dry_run:
            final_stats = get_embedding_stats(conn)
            logging.info("="*60)
            logging.info("Embedding generation complete")
            logging.info(f"Total embedded: {final_stats['embedded']:,}")
            logging.info(f"Total standard concepts: {final_stats['total']:,}")
            logging.info(f"Coverage: {final_stats['percent']}%")

            if errors:
                logging.warning(f"Encountered {len(errors)} errors during processing")
                logging.warning("Check log file for details")
            logging.info("="*60)
        else:
            logging.info("DRY RUN complete - no data was written")

    finally:
        conn.close()
        logging.info("Database connection closed")

if __name__ == "__main__":
    main()
