#!/usr/bin/env python
"""
Test PostgreSQL integration with RAG system.
Verifies database connection, schema, and basic operations.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import numpy as np
import pickle

load_dotenv()

class PostgresIntegrationTest:
    def __init__(self):
        self.conn_params = {
            "host": os.getenv("DB_HOST", "localhost"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "postgres"),
            "port": os.getenv("DB_PORT", "5432"),
            "database": os.getenv("DB_NAME", "fde_rag"),
        }
        self.passed = 0
        self.failed = 0

    def test(self, name: str, fn) -> bool:
        """Run a test and track results."""
        try:
            fn()
            print(f"  [PASS] {name}")
            self.passed += 1
            return True
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            self.failed += 1
            return False

    def connect(self):
        """Test database connection."""
        def check():
            conn = psycopg2.connect(**self.conn_params)
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            assert "PostgreSQL" in version
            cursor.close()
            conn.close()

        self.test("Database connection", check)

    def check_pgvector(self):
        """Test pgvector extension."""
        def check():
            conn = psycopg2.connect(**self.conn_params)
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM pg_extension WHERE extname='vector'")
            assert cursor.fetchone() is not None, "pgvector extension not found"
            cursor.close()
            conn.close()

        self.test("pgvector extension available", check)

    def check_tables(self):
        """Test table existence."""
        def check():
            conn = psycopg2.connect(**self.conn_params)
            cursor = conn.cursor()

            # Check documents table
            cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'documents'
            )
            """)
            assert cursor.fetchone()[0], "documents table not found"

            # Check chunks table
            cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'chunks'
            )
            """)
            assert cursor.fetchone()[0], "chunks table not found"

            cursor.close()
            conn.close()

        self.test("Database tables exist", check)

    def test_document_insert(self):
        """Test inserting a document."""
        def check():
            conn = psycopg2.connect(**self.conn_params)
            cursor = conn.cursor()

            # Insert test document
            cursor.execute("""
            INSERT INTO documents
            (id, filename, file_type, department, category, page_count, total_tokens, chunks_created, chunking_strategy)
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                "test-doc-1",
                "test.pdf",
                "pdf",
                "Engineering",
                "Technical",
                5,
                1000,
                10,
                "semantic"
            ))

            conn.commit()

            # Verify insert
            cursor.execute("SELECT COUNT(*) FROM documents WHERE id='test-doc-1'")
            count = cursor.fetchone()[0]
            assert count == 1, f"Expected 1 document, got {count}"

            # Cleanup
            cursor.execute("DELETE FROM documents WHERE id='test-doc-1'")
            conn.commit()
            cursor.close()
            conn.close()

        self.test("Insert and delete document", check)

    def test_chunk_insert_with_embedding(self):
        """Test inserting chunks with embeddings."""
        def check():
            conn = psycopg2.connect(**self.conn_params)
            cursor = conn.cursor()

            # Create test document first
            cursor.execute("""
            INSERT INTO documents
            (id, filename, file_type, department, category, page_count, total_tokens, chunks_created, chunking_strategy)
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                "test-doc-2",
                "test.pdf",
                "pdf",
                "Engineering",
                "Technical",
                1,
                500,
                5,
                "semantic"
            ))

            # Create mock embedding (1536 dims like OpenAI)
            embedding = np.random.randn(1536).astype(np.float32)
            embedding_bytes = pickle.dumps(embedding)

            # Insert chunk with embedding
            cursor.execute("""
            INSERT INTO chunks
            (id, chunk_id, document_id, text, chunk_index, section, page_number, token_count, department, category, embedding)
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                "chunk-1",
                "chunk-1-uuid",
                "test-doc-2",
                "This is a test chunk about Kubernetes pods and container orchestration.",
                0,
                "Introduction",
                1,
                50,
                "Engineering",
                "Technical",
                embedding_bytes
            ))

            conn.commit()

            # Verify insert
            cursor.execute("SELECT COUNT(*) FROM chunks WHERE chunk_id='chunk-1-uuid'")
            count = cursor.fetchone()[0]
            assert count == 1, f"Expected 1 chunk, got {count}"

            # Verify embedding
            cursor.execute("SELECT embedding FROM chunks WHERE chunk_id='chunk-1-uuid'")
            stored_embedding = cursor.fetchone()[0]
            assert stored_embedding is not None, "Embedding not stored"

            # Cleanup
            cursor.execute("DELETE FROM chunks WHERE document_id='test-doc-2'")
            cursor.execute("DELETE FROM documents WHERE id='test-doc-2'")
            conn.commit()
            cursor.close()
            conn.close()

        self.test("Insert chunk with embedding", check)

    def test_text_search(self):
        """Test full-text search."""
        def check():
            conn = psycopg2.connect(**self.conn_params)
            cursor = conn.cursor()

            # Insert test data
            cursor.execute("""
            INSERT INTO documents
            (id, filename, file_type, department, category, page_count, total_tokens, chunks_created, chunking_strategy)
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, ("test-doc-3", "test.pdf", "pdf", "Eng", "Tech", 1, 500, 1, "semantic"))

            cursor.execute("""
            INSERT INTO chunks
            (id, chunk_id, document_id, text, chunk_index, section, page_number, token_count, department, category)
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                "chunk-2", "chunk-2-uuid", "test-doc-3",
                "Kubernetes is a container orchestration platform for managing microservices.",
                0, "Intro", 1, 50, "Eng", "Tech"
            ))

            conn.commit()

            # Search using full-text search
            cursor.execute("""
            SELECT * FROM chunks
            WHERE to_tsvector('english', text) @@ plainto_tsquery('kubernetes microservices')
            """)
            results = cursor.fetchall()
            assert len(results) > 0, "Full-text search returned no results"

            # Cleanup
            cursor.execute("DELETE FROM chunks WHERE document_id='test-doc-3'")
            cursor.execute("DELETE FROM documents WHERE id='test-doc-3'")
            conn.commit()
            cursor.close()
            conn.close()

        self.test("Full-text search", check)

    def test_metadata_filter(self):
        """Test metadata filtering."""
        def check():
            conn = psycopg2.connect(**self.conn_params)
            cursor = conn.cursor()

            # Insert test documents with different departments
            cursor.execute("""
            INSERT INTO documents
            (id, filename, file_type, department, category, page_count, total_tokens, chunks_created, chunking_strategy)
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, ("test-doc-4a", "test.pdf", "pdf", "Engineering", "Tech", 1, 500, 1, "semantic"))

            cursor.execute("""
            INSERT INTO documents
            (id, filename, file_type, department, category, page_count, total_tokens, chunks_created, chunking_strategy)
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, ("test-doc-4b", "test.pdf", "pdf", "Sales", "Docs", 1, 500, 1, "semantic"))

            cursor.execute("""
            INSERT INTO chunks
            (id, chunk_id, document_id, text, chunk_index, section, page_number, token_count, department, category)
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, ("chunk-4a", "chunk-4a-uuid", "test-doc-4a", "Engineering content here", 0, "Intro", 1, 50, "Engineering", "Tech"))

            cursor.execute("""
            INSERT INTO chunks
            (id, chunk_id, document_id, text, chunk_index, section, page_number, token_count, department, category)
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, ("chunk-4b", "chunk-4b-uuid", "test-doc-4b", "Sales content here", 0, "Intro", 1, 50, "Sales", "Docs"))

            conn.commit()

            # Filter by department
            cursor.execute("SELECT COUNT(*) FROM chunks WHERE department='Engineering'")
            eng_count = cursor.fetchone()[0]
            assert eng_count >= 1, "Engineering filter not working"

            cursor.execute("SELECT COUNT(*) FROM chunks WHERE department='Sales'")
            sales_count = cursor.fetchone()[0]
            assert sales_count >= 1, "Sales filter not working"

            # Cleanup
            cursor.execute("DELETE FROM chunks WHERE document_id IN ('test-doc-4a', 'test-doc-4b')")
            cursor.execute("DELETE FROM documents WHERE id IN ('test-doc-4a', 'test-doc-4b')")
            conn.commit()
            cursor.close()
            conn.close()

        self.test("Metadata filtering", check)

    def run_all(self):
        """Run all tests."""
        print("\n" + "=" * 70)
        print("PostgreSQL Integration Tests")
        print("=" * 70 + "\n")

        print(f"Testing database: {self.conn_params['database']}@{self.conn_params['host']}:{self.conn_params['port']}\n")

        self.connect()
        self.check_pgvector()
        self.check_tables()
        self.test_document_insert()
        self.test_chunk_insert_with_embedding()
        self.test_text_search()
        self.test_metadata_filter()

        print("\n" + "=" * 70)
        print(f"Results: {self.passed} passed, {self.failed} failed")
        print("=" * 70)

        if self.failed == 0:
            print("\n✅ All tests passed! PostgreSQL is ready for RAG system.")
            return 0
        else:
            print(f"\n⚠️  {self.failed} test(s) failed. Check PostgreSQL setup.")
            return 1

if __name__ == "__main__":
    tester = PostgresIntegrationTest()
    exit_code = tester.run_all()
    sys.exit(exit_code)
