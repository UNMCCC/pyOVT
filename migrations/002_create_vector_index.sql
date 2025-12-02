-- Phase 3: Semantic Search - Vector Similarity Index
-- This creates an ivfflat index for fast cosine similarity search
-- IMPORTANT: Run this AFTER embeddings are loaded

-- Calculate optimal lists parameter
-- Formula: sqrt(row_count) rounded to nearest hundred
-- For 2.76M rows: sqrt(2760000) ≈ 1661 → use 1700

CREATE INDEX IF NOT EXISTS idx_concept_embedding_vector ON concept_embedding
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 1700);

-- Set recommended query parameter for accuracy/speed balance
-- This affects all vector similarity queries
-- Higher probes = more accurate but slower
-- Range: 1-100, recommended: 10-50 for medical terminology
ALTER DATABASE cdm SET ivfflat.probes = 20;

COMMENT ON INDEX idx_concept_embedding_vector IS
'IVFFlat index for fast cosine similarity search on embeddings. Probes set to 20 for accuracy/speed balance.';
