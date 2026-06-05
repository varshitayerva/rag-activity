-- Database schema with pgvector for HNSW vector search
-- Production-ready RAG system with semantic + full-text search

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255),
    api_key VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(50) DEFAULT 'user',
    department VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL UNIQUE,
    content_type VARCHAR(50),
    file_size INTEGER,
    department VARCHAR(100),
    category VARCHAR(100),
    chunking_strategy VARCHAR(20) DEFAULT 'semantic' CHECK (chunking_strategy IN ('semantic', 'fixed')),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chunks table with pgvector embeddings
CREATE TABLE IF NOT EXISTS chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER,
    text TEXT NOT NULL,
    section VARCHAR(255),
    page_number INTEGER,
    embedding vector(1536),
    department VARCHAR(100),
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Metrics table
CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    metric_type VARCHAR(50),
    value FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Search queries table (for analytics)
CREATE TABLE IF NOT EXISTS search_queries (
    id SERIAL PRIMARY KEY,
    query TEXT,
    results_count INTEGER,
    latency_ms INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_api_key ON users(api_key);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_documents_filename ON documents(filename);
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_section ON chunks(section);
CREATE INDEX IF NOT EXISTS idx_chunks_department ON chunks(department);
CREATE INDEX IF NOT EXISTS idx_chunks_category ON chunks(category);
CREATE INDEX IF NOT EXISTS idx_chunks_created_at ON chunks(created_at);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_search_queries_timestamp ON search_queries(timestamp);

-- HNSW index for vector similarity search (cosine distance)
-- This enables fast approximate nearest neighbor search
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw ON chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Chunk metadata table for tracking chunking strategy and other attributes
CREATE TABLE IF NOT EXISTS chunk_metadata (
    id SERIAL PRIMARY KEY,
    chunk_id INTEGER NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunking_strategy VARCHAR(20),
    sentence_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chunk_metadata_chunk_id ON chunk_metadata(chunk_id);
CREATE INDEX IF NOT EXISTS idx_chunk_metadata_strategy ON chunk_metadata(chunking_strategy);

-- Document summaries table for hierarchical indexing
CREATE TABLE IF NOT EXISTS document_summaries (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL UNIQUE REFERENCES documents(id) ON DELETE CASCADE,
    summary TEXT NOT NULL,
    embedding vector(1536),
    chunk_count INTEGER,
    key_topics VARCHAR(500),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_document_summaries_doc_id ON document_summaries(document_id);
CREATE INDEX IF NOT EXISTS idx_document_summaries_embedding_hnsw ON document_summaries
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 8, ef_construction = 32);

-- User feedback table for confidence and answer quality tracking
CREATE TABLE IF NOT EXISTS query_feedback (
    id SERIAL PRIMARY KEY,
    query_id INTEGER REFERENCES search_queries(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    answer TEXT,
    confidence_score FLOAT,
    rating INTEGER CHECK (rating IN (-1, 0, 1)),
    feedback_text TEXT,
    chunks_used TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_query_feedback_query_id ON query_feedback(query_id);
CREATE INDEX IF NOT EXISTS idx_query_feedback_rating ON query_feedback(rating);
CREATE INDEX IF NOT EXISTS idx_query_feedback_created_at ON query_feedback(created_at);
