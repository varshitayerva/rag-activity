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

            logger.info("Database initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False

    # Document operations
    def add_document(self, filename: str, content_type: str, file_size: int,
                     department: str = None, category: str = None,
                     chunking_strategy: str = "semantic") -> int:
        """Add document to database. Returns document ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(
                    "INSERT INTO documents (filename, content_type, file_size, department, category, chunking_strategy) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                    (filename, content_type, file_size, department, category, chunking_strategy)
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

    # Document summary operations
    def add_document_summary(self, document_id: int, summary: str,
                            embedding: list, key_topics: str,
                            chunk_count: int) -> int:
        """Add document summary for hierarchical indexing."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(
                    """INSERT INTO document_summaries
                       (document_id, summary, embedding, key_topics, chunk_count)
                       VALUES (%s, %s, %s, %s, %s)
                       RETURNING id""",
                    (document_id, summary, embedding, key_topics, chunk_count)
                )
                summary_id = cursor.fetchone()[0]
                conn.commit()
                logger.info(f"Added document summary for doc {document_id}")
                return summary_id

            except psycopg2.IntegrityError:
                conn.rollback()
                logger.warning(f"Summary already exists for doc {document_id}")
                return None
            finally:
                cursor.close()

    def search_documents_by_summary(self, query_embedding: list,
                                   top_k: int = 10) -> List[Dict[str, Any]]:
        """Search documents by their summaries (stage 1 of hierarchical search)."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            try:
                cursor.execute(
                    """SELECT ds.id, ds.document_id, d.filename,
                              ds.summary, ds.key_topics, ds.chunk_count,
                              ds.embedding <-> %s::vector AS distance
                       FROM document_summaries ds
                       JOIN documents d ON ds.document_id = d.id
                       ORDER BY distance ASC
                       LIMIT %s""",
                    (query_embedding, top_k)
                )

                results = cursor.fetchall()
                return [dict(row) for row in results]

            finally:
                cursor.close()

    # User feedback operations
    def add_feedback(self, query: str, answer: str = None, confidence_score: float = None,
                    rating: int = None, feedback_text: str = None, chunks_used: str = None) -> int:
        """Add user feedback for a query/answer pair."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(
                    """INSERT INTO query_feedback
                       (query, answer, confidence_score, rating, feedback_text, chunks_used)
                       VALUES (%s, %s, %s, %s, %s, %s)
                       RETURNING id""",
                    (query, answer, confidence_score, rating, feedback_text, chunks_used)
                )
                feedback_id = cursor.fetchone()[0]
                conn.commit()
                logger.info(f"Recorded feedback: query={query[:50]}, rating={rating}")
                return feedback_id

            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to record feedback: {e}")
                return None
            finally:
                cursor.close()

    def get_feedback_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get feedback analytics for last N days."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            try:
                # Get summary stats
                cursor.execute(
                    """SELECT
                        COUNT(*) as total_feedback,
                        SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as thumbs_up,
                        SUM(CASE WHEN rating = -1 THEN 1 ELSE 0 END) as thumbs_down,
                        SUM(CASE WHEN rating = 0 THEN 1 ELSE 0 END) as neutral,
                        AVG(confidence_score) as avg_confidence
                       FROM query_feedback
                       WHERE created_at >= NOW() - INTERVAL '%s days'""",
                    (days,)
                )
                stats = dict(cursor.fetchone())

                # Get low-rated queries
                cursor.execute(
                    """SELECT query, COUNT(*) as count, AVG(confidence_score) as avg_confidence
                       FROM query_feedback
                       WHERE rating = -1 AND created_at >= NOW() - INTERVAL '%s days'
                       GROUP BY query
                       ORDER BY count DESC
                       LIMIT 10""",
                    (days,)
                )
                low_rated = [dict(row) for row in cursor.fetchall()]

                return {
                    'stats': stats,
                    'low_rated_queries': low_rated,
                    'period_days': days
                }

            finally:
                cursor.close()

    def get_low_confidence_queries(self, threshold: float = 0.4, limit: int = 20) -> List[Dict[str, Any]]:
        """Get queries with confidence below threshold for manual review."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            try:
                cursor.execute(
                    """SELECT query, COUNT(*) as occurrences, AVG(confidence_score) as avg_confidence
                       FROM query_feedback
                       WHERE confidence_score < %s
                       GROUP BY query
                       ORDER BY occurrences DESC, avg_confidence ASC
                       LIMIT %s""",
                    (threshold, limit)
                )

                return [dict(row) for row in cursor.fetchall()]

            finally:
                cursor.close()


# Global instance
db_client = PostgresClient()
