"""PostgreSQL client with connection pooling."""

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import os
from typing import List, Dict, Any
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class PostgresClient:
    """PostgreSQL client with connection pooling."""

    _pool = None

    def __init__(self):
        self.conn_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres'),
            'database': os.getenv('DB_NAME', 'fde_rag'),
        }
        self._init_pool()

    def _init_pool(self):
        """Initialize connection pool."""
        if PostgresClient._pool is None:
            try:
                PostgresClient._pool = pool.SimpleConnectionPool(
                    minconn=2,
                    maxconn=20,
                    **self.conn_params
                )
                logger.info("Database connection pool initialized (2-20 connections)")
            except Exception as e:
                logger.error(f"Failed to create connection pool: {e}")
                raise

    @contextmanager
    def get_connection(self):
        """Get connection from pool."""
        conn = None
        try:
            conn = PostgresClient._pool.getconn()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                PostgresClient._pool.putconn(conn)

    def init_db(self):
        """Initialize database schema."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Read and execute schema
                schema_path = os.path.join(
                    os.path.dirname(__file__),
                    'schema.sql'
                )
                with open(schema_path, 'r') as f:
                    schema = f.read()
                    cursor.execute(schema)

                conn.commit()
                cursor.close()

            print("✅ Database initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            return False

    # Document operations
    def add_document(self, filename: str, content_type: str, file_size: int,
                     department: str = None, category: str = None) -> int:
        """Add document to database. Returns document ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(
                    "INSERT INTO documents (filename, content_type, file_size, department, category) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                    (filename, content_type, file_size, department, category)
                )
                doc_id = cursor.fetchone()[0]
                conn.commit()
                return doc_id
            except psycopg2.IntegrityError:
                conn.rollback()
                # Document already exists, get its ID
                cursor.execute("SELECT id FROM documents WHERE filename = %s", (filename,))
                return cursor.fetchone()[0]
            finally:
                cursor.close()

    def get_document(self, doc_id: int) -> Dict[str, Any]:
        """Get document by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("SELECT * FROM documents WHERE id = %s", (doc_id,))
            result = cursor.fetchone()
            cursor.close()

            return dict(result) if result else None

    def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("SELECT * FROM documents ORDER BY created_at DESC")
            results = cursor.fetchall()
            cursor.close()

            return [dict(row) for row in results]

    # Chunk operations
    def add_chunks(self, doc_id: int, chunks: List[Dict[str, Any]]):
        """Add chunks to database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            for chunk in chunks:
                cursor.execute(
                    """INSERT INTO chunks (document_id, chunk_index, text, section, page_number)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (doc_id, chunk.get('chunk_index'), chunk['text'],
                     chunk.get('section'), chunk.get('page_number'))
                )

            conn.commit()
            cursor.close()

    def get_chunks(self, doc_id: int) -> List[Dict[str, Any]]:
        """Get all chunks for a document."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("SELECT * FROM chunks WHERE document_id = %s ORDER BY chunk_index", (doc_id,))
            results = cursor.fetchall()
            cursor.close()

            return [dict(row) for row in results]

    def get_chunk_by_id(self, chunk_id: int) -> Dict[str, Any]:
        """Get chunk by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("SELECT * FROM chunks WHERE id = %s", (chunk_id,))
            result = cursor.fetchone()
            cursor.close()

            return dict(result) if result else None

    def get_all_chunks(self) -> List[Dict[str, Any]]:
        """Get all chunks from all documents."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("SELECT * FROM chunks ORDER BY document_id, chunk_index")
            results = cursor.fetchall()
            cursor.close()

            return [dict(row) for row in results]

    def get_chunks_with_filters(self, department: str = None, category: str = None,
                                date_from: str = None, date_to: str = None) -> List[Dict[str, Any]]:
        """Get chunks filtered by department, category, and date range."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = """
                SELECT c.*, d.filename, d.department, d.category, d.created_at
                FROM chunks c
                JOIN documents d ON c.document_id = d.id
                WHERE 1=1
            """
            params = []

            if department:
                query += " AND d.department = %s"
                params.append(department)

            if category:
                query += " AND d.category = %s"
                params.append(category)

            if date_from:
                query += " AND d.created_at >= %s"
                params.append(date_from)

            if date_to:
                query += " AND d.created_at <= %s"
                params.append(date_to)

            query += " ORDER BY c.document_id, c.chunk_index"

            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()

            return [dict(row) for row in results]

    # Metrics
    def record_metric(self, metric_type: str, value: float):
        """Record a metric."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO metrics (metric_type, value) VALUES (%s, %s)",
                (metric_type, value)
            )

            conn.commit()
            cursor.close()

    def record_search_query(self, query: str, results_count: int, latency_ms: int):
        """Record search query for analytics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO search_queries (query, results_count, latency_ms) VALUES (%s, %s, %s)",
                (query, results_count, latency_ms)
            )

            conn.commit()
            cursor.close()

    def get_metrics(self, metric_type: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get metrics."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            if metric_type:
                cursor.execute(
                    "SELECT * FROM metrics WHERE metric_type = %s ORDER BY timestamp DESC LIMIT %s",
                    (metric_type, limit)
                )
            else:
                cursor.execute(
                    "SELECT * FROM metrics ORDER BY timestamp DESC LIMIT %s",
                    (limit,)
                )

            results = cursor.fetchall()
            cursor.close()

            return [dict(row) for row in results]


# Global instance
db_client = PostgresClient()
