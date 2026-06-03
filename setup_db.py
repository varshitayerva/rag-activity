#!/usr/bin/env python
"""
PostgreSQL database setup script for RAG system.
Creates tables, enables pgvector extension, and initializes schema.
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()

def get_connection(database=None):
    """Get PostgreSQL connection."""
    conn_params = {
        "host": os.getenv("DB_HOST", "localhost"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "postgres"),
        "port": os.getenv("DB_PORT", "5432"),
    }
    if database:
        conn_params["database"] = database

    return psycopg2.connect(**conn_params)

def create_database():
    """Create database if it doesn't exist."""
    db_name = os.getenv("DB_NAME", "fde_rag")

    print(f"[1] Checking database '{db_name}'...")
    conn = get_connection()
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        if not cursor.fetchone():
            print(f"  Creating database '{db_name}'...")
            cursor.execute(f"CREATE DATABASE {db_name}")
            print(f"  ✓ Database created")
        else:
            print(f"  ✓ Database already exists")
    finally:
        cursor.close()
        conn.close()

def enable_pgvector():
    """Enable pgvector extension."""
    print("\n[2] Enabling pgvector extension...")
    conn = get_connection(os.getenv("DB_NAME", "fde_rag"))
    cursor = conn.cursor()

    try:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.commit()
        print("  ✓ pgvector extension enabled")
    except Exception as e:
        print(f"  ⚠ pgvector extension issue: {e}")
        print("  Install pgvector: https://github.com/pgvector/pgvector")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def create_tables():
    """Create database tables."""
    print("\n[3] Creating tables...")
    conn = get_connection(os.getenv("DB_NAME", "fde_rag"))
    cursor = conn.cursor()

    try:
        # Documents table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id VARCHAR(255) PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            file_type VARCHAR(50),
            department VARCHAR(100),
            category VARCHAR(100),
            page_count INTEGER,
            total_tokens INTEGER,
            chunks_created INTEGER,
            chunking_strategy VARCHAR(50),
            doc_metadata JSONB,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("  ✓ documents table created")

        # Chunks table with vector column
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id VARCHAR(255) PRIMARY KEY,
            chunk_id VARCHAR(255) UNIQUE NOT NULL,
            document_id VARCHAR(255) REFERENCES documents(id) ON DELETE CASCADE,
            text TEXT NOT NULL,
            chunk_index INTEGER,
            section VARCHAR(255),
            page_number INTEGER,
            token_count INTEGER,
            filename VARCHAR(255),
            doc_id VARCHAR(255),
            department VARCHAR(100),
            category VARCHAR(100),
            embedding BYTEA,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("  ✓ chunks table created")

        # Create indices for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_department ON chunks(department)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_category ON chunks(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_text ON chunks USING gin(to_tsvector('english', text))")
        print("  ✓ indices created")

        conn.commit()

    except Exception as e:
        print(f"  ✗ Error creating tables: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def verify_connection():
    """Verify database connection works."""
    print("\n[4] Verifying connection...")
    try:
        conn = get_connection(os.getenv("DB_NAME", "fde_rag"))
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"  ✓ Connected to: {version[:80]}...")

        # Check pgvector
        cursor.execute("SELECT 1 FROM pg_extension WHERE extname='vector'")
        if cursor.fetchone():
            print("  ✓ pgvector is available")
        else:
            print("  ⚠ pgvector not found (optional, but needed for vector search)")

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        return False

def main():
    print("=" * 70)
    print("PostgreSQL + pgvector Database Setup")
    print("=" * 70)

    # Load environment
    db_name = os.getenv("DB_NAME", "fde_rag")
    db_host = os.getenv("DB_HOST", "localhost")
    db_user = os.getenv("DB_USER", "postgres")
    db_port = os.getenv("DB_PORT", "5432")

    print(f"\nConnection details:")
    print(f"  Host: {db_host}:{db_port}")
    print(f"  User: {db_user}")
    print(f"  Database: {db_name}")

    try:
        create_database()
        enable_pgvector()
        create_tables()
        if verify_connection():
            print("\n" + "=" * 70)
            print("✅ DATABASE SETUP COMPLETE")
            print("=" * 70)
            print("\nYou can now use the RAG system with PostgreSQL!")
            print("\nUpdate your .env file with:")
            print(f"  DATABASE_URL=postgresql://{db_user}:PASSWORD@{db_host}:{db_port}/{db_name}")
            return 0
        else:
            print("\n❌ Setup complete but connection verification failed")
            return 1
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
