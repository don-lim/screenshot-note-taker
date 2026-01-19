-- Screenshot Note Taker Database Schema
-- PostgreSQL database with pgvector extension for semantic search
-- Updated: 2026-01-17
-- Features: EasyOCR + bge-m3 (1024-dim embeddings)

-- Connect to the database
\c image_search_db;

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- TABLES
-- ============================================================================

-- Images table: Stores screenshot metadata
CREATE TABLE IF NOT EXISTS images (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL UNIQUE,  -- Unique to prevent duplicates
    timestamp TIMESTAMP NOT NULL,    -- File modification time
    inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ai_description TEXT,             -- Vision LLM generated description
    model_name TEXT,                 -- Model used for description
    
    -- Indexes for faster queries
    CONSTRAINT images_filepath_key UNIQUE (filepath)
);

-- Create index on timestamp for date-based queries
CREATE INDEX IF NOT EXISTS idx_images_timestamp ON images(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_images_inserted_at ON images(inserted_at DESC);

-- OCR Results table: Stores extracted text and confidence scores
CREATE TABLE IF NOT EXISTS ocr_results (
    id SERIAL PRIMARY KEY,
    image_id INTEGER NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    confidence FLOAT NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    
    -- One OCR result per image
    CONSTRAINT ocr_results_image_id_key UNIQUE (image_id)
);

-- Create index for text search
CREATE INDEX IF NOT EXISTS idx_ocr_text ON ocr_results USING gin(to_tsvector('english', text));
CREATE INDEX IF NOT EXISTS idx_ocr_image_id ON ocr_results(image_id);

-- Text Embeddings table: Stores bge-m3 embeddings (1024-dimensional)
CREATE TABLE IF NOT EXISTS text_embedding (
    id SERIAL PRIMARY KEY,
    image_id INTEGER NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    embedding VECTOR(1024) NOT NULL,  -- bge-m3 generates 1024-dim vectors
    chunk_index INTEGER NOT NULL DEFAULT 0,
    
    -- Allow multiple chunks per image
    CONSTRAINT text_embedding_image_chunk_key UNIQUE (image_id, chunk_index)
);

-- Create vector index for fast similarity search
-- Using ivfflat for approximate nearest neighbor search
CREATE INDEX IF NOT EXISTS idx_embedding_vector ON text_embedding 
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);  -- Tune based on dataset size

CREATE INDEX IF NOT EXISTS idx_embedding_image_id ON text_embedding(image_id);

-- ============================================================================
-- PERMISSIONS
-- ============================================================================

-- Grant all privileges to the application user
GRANT ALL PRIVILEGES ON TABLE images TO screuser235;
GRANT ALL PRIVILEGES ON TABLE ocr_results TO screuser235;
GRANT ALL PRIVILEGES ON TABLE text_embedding TO screuser235;

-- Grant sequence permissions for auto-increment IDs
GRANT ALL PRIVILEGES ON SEQUENCE images_id_seq TO screuser235;
GRANT ALL PRIVILEGES ON SEQUENCE ocr_results_id_seq TO screuser235;
GRANT ALL PRIVILEGES ON SEQUENCE text_embedding_id_seq TO screuser235;

-- ============================================================================
-- USEFUL VIEWS (Optional)
-- ============================================================================

-- View: Complete image data with OCR and embedding count
CREATE OR REPLACE VIEW v_image_summary AS
SELECT 
    i.id,
    i.filename,
    i.filepath,
    i.timestamp,
    i.inserted_at,
    i.ai_description,
    i.model_name,
    o.text,
    o.confidence,
    LENGTH(o.text) as text_length,
    COUNT(te.id) as embedding_count
FROM images i
LEFT JOIN ocr_results o ON i.id = o.image_id
LEFT JOIN text_embedding te ON i.id = te.image_id
GROUP BY i.id, i.filename, i.filepath, i.timestamp, i.inserted_at, i.ai_description, i.model_name, o.text, o.confidence;

GRANT SELECT ON v_image_summary TO screuser235;

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function: Search images by text similarity
CREATE OR REPLACE FUNCTION search_by_embedding(
    query_embedding VECTOR(1024),
    result_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    image_id INTEGER,
    filename TEXT,
    filepath TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        i.id,
        i.filename,
        i.filepath,
        1 - (te.embedding <=> query_embedding) as similarity
    FROM images i
    JOIN text_embedding te ON i.id = te.image_id
    ORDER BY te.embedding <=> query_embedding
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION search_by_embedding TO screuser235;

-- ============================================================================
-- STATISTICS
-- ============================================================================

-- Display table statistics
DO $$
DECLARE
    img_count INTEGER;
    ocr_count INTEGER;
    emb_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO img_count FROM images;
    SELECT COUNT(*) INTO ocr_count FROM ocr_results;
    SELECT COUNT(*) INTO emb_count FROM text_embedding;
    
    RAISE NOTICE 'Database Statistics:';
    RAISE NOTICE '  Images: %', img_count;
    RAISE NOTICE '  OCR Results: %', ocr_count;
    RAISE NOTICE '  Embeddings: %', emb_count;
    RAISE NOTICE 'Schema setup complete!';
END $$;
