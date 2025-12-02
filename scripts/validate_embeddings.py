#!/usr/bin/env python3
"""
Validate vector embeddings for semantic search quality.

This script performs quality checks on generated embeddings:
1. Coverage validation (all standard concepts have embeddings)
2. Dimensionality checks (all vectors are 384-dimensional)
3. Normalization verification (vectors are L2-normalized)
4. Semantic quality tests (similar concepts have high cosine similarity)

Usage:
    python scripts/validate_embeddings.py
"""

import os
import sys
import psycopg2
import numpy as np
from typing import List, Tuple

# Configuration from environment
DB_USER = os.getenv("DB_USER", "smathias")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "cdm")
DB_PORT = os.getenv("DB_PORT", "5432")

EXPECTED_DIMENSION = 384
EXPECTED_MODEL = "all-MiniLM-L6-v2"


def get_db_connection():
    """Create database connection"""
    if DB_PASSWORD:
        conn_string = f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} host={DB_HOST} port={DB_PORT}"
    else:
        conn_string = f"dbname={DB_NAME} user={DB_USER} host={DB_HOST} port={DB_PORT}"

    return psycopg2.connect(conn_string)


def validate_coverage(conn) -> bool:
    """Check that all standard concepts have embeddings"""
    print("\n=== Coverage Validation ===")

    with conn.cursor() as cur:
        # Count total standard concepts
        cur.execute("""
            SELECT COUNT(*)
            FROM concept
            WHERE standard_concept = 'S'
              AND concept_name IS NOT NULL
              AND concept_name != ''
        """)
        total_concepts = cur.fetchone()[0]

        # Count embedded concepts
        cur.execute("SELECT COUNT(*) FROM concept_embedding")
        embedded_count = cur.fetchone()[0]

        # Find missing concepts (if any)
        cur.execute("""
            SELECT c.concept_id, c.concept_name, c.domain_id, c.vocabulary_id
            FROM concept c
            LEFT JOIN concept_embedding ce ON c.concept_id = ce.concept_id
            WHERE c.standard_concept = 'S'
              AND c.concept_name IS NOT NULL
              AND c.concept_name != ''
              AND ce.concept_id IS NULL
            LIMIT 10
        """)
        missing = cur.fetchall()

    coverage_pct = (embedded_count / total_concepts * 100) if total_concepts > 0 else 0

    print(f"Total standard concepts: {total_concepts:,}")
    print(f"Embedded concepts: {embedded_count:,}")
    print(f"Coverage: {coverage_pct:.2f}%")

    if missing:
        print(f"\n⚠️  Warning: {len(missing)} concepts without embeddings (showing first 10):")
        for concept_id, name, domain, vocab in missing[:10]:
            print(f"  - {concept_id}: {name} ({domain}, {vocab})")
        return False
    else:
        print("✓ All standard concepts have embeddings")
        return True


def validate_dimensionality(conn) -> bool:
    """Check that all embeddings have correct dimensionality"""
    print("\n=== Dimensionality Validation ===")

    with conn.cursor() as cur:
        # Check vector dimensions
        cur.execute("""
            SELECT
                concept_id,
                vector_dims(embedding) as dims
            FROM concept_embedding
            WHERE vector_dims(embedding) != %s
            LIMIT 10
        """, (EXPECTED_DIMENSION,))

        invalid = cur.fetchall()

    if invalid:
        print(f"⚠️  Warning: {len(invalid)} embeddings have incorrect dimensions:")
        for concept_id, dims in invalid:
            print(f"  - Concept {concept_id}: {dims} dimensions (expected {EXPECTED_DIMENSION})")
        return False
    else:
        print(f"✓ All embeddings are {EXPECTED_DIMENSION}-dimensional")
        return True


def validate_normalization(conn) -> bool:
    """Check that embeddings are L2-normalized (length ≈ 1.0)"""
    print("\n=== Normalization Validation ===")

    with conn.cursor() as cur:
        # Sample 1000 random embeddings and check their L2 norm
        cur.execute("""
            SELECT
                concept_id,
                embedding::text
            FROM concept_embedding
            ORDER BY RANDOM()
            LIMIT 1000
        """)

        samples = cur.fetchall()

    if not samples:
        print("⚠️  No embeddings found to validate")
        return False

    invalid_count = 0
    for concept_id, embedding_str in samples:
        # Parse the vector string to numpy array
        # Remove brackets and split by comma
        embedding_str = embedding_str.strip('[]')
        embedding = np.array([float(x) for x in embedding_str.split(',')])

        # Calculate L2 norm (should be ≈ 1.0 for normalized vectors)
        norm = np.linalg.norm(embedding)
        if abs(norm - 1.0) > 0.01:  # Allow 1% tolerance
            invalid_count += 1
            if invalid_count <= 5:  # Show first 5
                print(f"  - Concept {concept_id}: norm = {norm:.4f}")

    if invalid_count > 0:
        print(f"⚠️  Warning: {invalid_count}/1000 sampled embeddings are not normalized")
        return False
    else:
        print("✓ All sampled embeddings are L2-normalized")
        return True


def validate_semantic_quality(conn) -> bool:
    """Test semantic quality with known similar concepts"""
    print("\n=== Semantic Quality Validation ===")

    # Test cases: pairs of concepts that should be semantically similar
    test_cases = [
        ("diabetes mellitus", "sugar disease"),
        ("myocardial infarction", "heart attack"),
        ("hypertension", "high blood pressure"),
        ("pneumonia", "lung infection"),
    ]

    all_passed = True

    with conn.cursor() as cur:
        for term1, term2 in test_cases:
            # Find embedding for term1
            cur.execute("""
                SELECT c.concept_id, c.concept_name, ce.embedding::text
                FROM concept c
                JOIN concept_embedding ce ON c.concept_id = ce.concept_id
                WHERE LOWER(c.concept_name) LIKE %s
                  AND c.standard_concept = 'S'
                LIMIT 1
            """, (f"%{term1.lower()}%",))

            result1 = cur.fetchone()
            if not result1:
                print(f"⚠️  Could not find concept for '{term1}'")
                all_passed = False
                continue

            concept_id1, name1, embedding1_str = result1
            # Parse embedding
            embedding1_str = embedding1_str.strip('[]')
            embedding1 = [float(x) for x in embedding1_str.split(',')]

            # Find most similar concepts using cosine similarity
            # Convert embedding list to proper format for pgvector
            embedding_str = '[' + ','.join(map(str, embedding1)) + ']'
            cur.execute("""
                SELECT
                    c.concept_id,
                    c.concept_name,
                    1 - (ce.embedding <=> %s::vector) as similarity
                FROM concept c
                JOIN concept_embedding ce ON c.concept_id = ce.concept_id
                WHERE c.concept_id != %s
                ORDER BY ce.embedding <=> %s::vector
                LIMIT 10
            """, (embedding_str, concept_id1, embedding_str))

            similar = cur.fetchall()

            # Check if term2 appears in top similar concepts
            found = False
            for sim_id, sim_name, similarity in similar:
                if term2.lower() in sim_name.lower():
                    print(f"✓ '{term1}' → '{sim_name}' (similarity: {similarity:.3f})")
                    found = True
                    break

            if not found:
                print(f"⚠️  '{term1}' → did not find '{term2}' in top 10 similar")
                print(f"   Top matches:")
                for sim_id, sim_name, similarity in similar[:3]:
                    print(f"     - {sim_name} (similarity: {similarity:.3f})")
                all_passed = False

    return all_passed


def validate_model_consistency(conn) -> bool:
    """Check that all embeddings use the expected model"""
    print("\n=== Model Consistency Validation ===")

    with conn.cursor() as cur:
        # Check for different models
        cur.execute("""
            SELECT
                model_name,
                model_version,
                COUNT(*) as count
            FROM concept_embedding
            GROUP BY model_name, model_version
        """)

        models = cur.fetchall()

    print(f"Found {len(models)} model version(s):")
    for model_name, model_version, count in models:
        print(f"  - {model_name} ({model_version}): {count:,} embeddings")

    if len(models) != 1:
        print(f"⚠️  Warning: Multiple models detected (expected only {EXPECTED_MODEL})")
        return False

    model_name, model_version, count = models[0]
    if model_name != EXPECTED_MODEL:
        print(f"⚠️  Warning: Unexpected model '{model_name}' (expected {EXPECTED_MODEL})")
        return False

    print(f"✓ All embeddings use {EXPECTED_MODEL}")
    return True


def main():
    print("=" * 60)
    print("Embedding Validation Report")
    print("=" * 60)

    try:
        conn = get_db_connection()
        print("✓ Database connection established")

        # Run all validation checks
        results = {
            "Coverage": validate_coverage(conn),
            "Dimensionality": validate_dimensionality(conn),
            "Normalization": validate_normalization(conn),
            "Model Consistency": validate_model_consistency(conn),
            "Semantic Quality": validate_semantic_quality(conn),
        }

        # Summary
        print("\n" + "=" * 60)
        print("Validation Summary")
        print("=" * 60)

        passed = sum(results.values())
        total = len(results)

        for check, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{check:.<30} {status}")

        print("=" * 60)
        print(f"Overall: {passed}/{total} checks passed")

        conn.close()

        if passed == total:
            print("\n✓ All validation checks passed!")
            return 0
        else:
            print(f"\n⚠️  {total - passed} validation check(s) failed")
            return 1

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
