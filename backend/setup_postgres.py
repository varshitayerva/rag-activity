#!/usr/bin/env python3
"""
Setup PostgreSQL database with pgvector extension.
Run this once to initialize the database.
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def setup_database():
    """Create database and enable pgvector extension."""

    # Connection to default postgres database
    conn = psycopg2.connect(
        host="localhost",
        user="postgres",
        password="1234",
        database="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    print("Setting up PostgreSQL database...")

    # Check if database exists
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'fde_rag'")
    exists = cursor.fetchone()

    if not exists:
        print("Creating database 'fde_rag'...")
        cursor.execute("CREATE DATABASE fde_rag")
        print("Database created")
    else:
        print("Database 'fde_rag' already exists")

    cursor.close()
    conn.close()

    # Connect to the new database
    conn = psycopg2.connect(
        host="localhost",
        user="postgres",
        password="1234",
        database="fde_rag"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    # Enable pgvector extension
    print("Enabling pgvector extension...")
    try:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
        print("pgvector extension enabled")
    except Exception as e:
        print(f"Note: pgvector might not be installed in PostgreSQL. Error: {e}")
        print("You may need to install pgvector extension")

    # Create chunks table (using BYTEA for embeddings if pgvector not available)
    print("Creating chunks table...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chunks (
        id SERIAL PRIMARY KEY,
        chunk_id VARCHAR(255) UNIQUE NOT NULL,
        text TEXT NOT NULL,
        doc_id VARCHAR(255),
        filename VARCHAR(255),
        section VARCHAR(255),
        page INTEGER,
        department VARCHAR(255),
        category VARCHAR(255),
        embedding BYTEA,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("Chunks table created")

    # Create simple index on chunk_id
    print("Creating indexes...")
    try:
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS chunks_chunk_id_idx ON chunks (chunk_id)
        """)
        print("Index created on chunk_id")
    except Exception as e:
        print(f"Note: Index creation skipped. Error: {e}")

    # Create text search index
    print("Creating text search index...")
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS chunks_text_idx ON chunks
    USING gin(to_tsvector('english', text))
    """)
    print("Text search index created")

    cursor.close()
    conn.close()

    print("\n" + "=" * 80)
    print("DATABASE SETUP COMPLETE!")
    print("=" * 80)
    print("Database: fde_rag")
    print("Host: localhost")
    print("Port: 5432")
    print("User: postgres")
    print("\n")

if __name__ == "__main__":
    try:
        setup_database()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
