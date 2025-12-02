-- Phase 3: Semantic Search - Embedding Storage Table
-- This migration adds the concept_embedding table for storing vector embeddings

-- Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create embedding storage table
CREATE TABLE IF NOT EXISTS concept_embedding (
    concept_id INTEGER PRIMARY KEY,
    embedding vector(384),  -- 384 dimensions for all-MiniLM-L6-v2
    model_name VARCHAR(100) NOT NULL DEFAULT 'all-MiniLM-L6-v2',
    model_version VARCHAR(50) NOT NULL DEFAULT 'v1',
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_concept_embedding_concept_id
        FOREIGN KEY (concept_id)
        REFERENCES concept(concept_id)
        ON DELETE CASCADE
);

-- Add table and column comments for documentation
COMMENT ON TABLE concept_embedding IS
'Vector embeddings for semantic search. Contains embeddings for standard concepts only.';

COMMENT ON COLUMN concept_embedding.concept_id IS
'Foreign key to concept.concept_id';

COMMENT ON COLUMN concept_embedding.embedding IS
'384-dimensional vector embedding of concept_name generated using sentence-transformers';

COMMENT ON COLUMN concept_embedding.model_name IS
'Name of the embedding model used (e.g., all-MiniLM-L6-v2, biobert-base)';

COMMENT ON COLUMN concept_embedding.model_version IS
'Version identifier for the embedding model';

COMMENT ON COLUMN concept_embedding.generated_at IS
'Timestamp when the embedding was generated';
