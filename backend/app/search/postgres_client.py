"""PostgreSQL client with pgvector for HNSW-accelerated vector search."""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any
import logging

try:
    from pgvector.psycopg2 import register_vector
except ImportError:
    register_vector = None

logger = logging.getLogger(__name__)


class PostgresVectorDB:
    """Vector database using PostgreSQL + pgvector with HNSW indexing."""

    def __init__(self, host: str = None, user: str = None,
                 password: str = None, database: str = None, port: int = None):
        """Initialize PostgreSQL connection."""
        import os
        self.conn_params = {
            "host": host or os.getenv("DB_HOST", "localhost"),
            "user": user or os.getenv("DB_USER", "postgres"),
            "password": password or os.getenv("DB_PASSWORD"),
            "database": database or os.getenv("DB_NAME", "fde_rag"),
            "port": port or int(os.getenv("DB_PORT", 5432))
        }
        if not self.conn_params["password"]:
            raise ValueError("Database password must be provided via DB_PASSWORD environment variable")
        self.connection = None
        self.vector_size = 1536
        self._connect()

    def _connect(self):
        """Establish database connection and register pgvector."""
        try:
            self.connection = psycopg2.connect(**self.conn_params)
            if register_vector:
                register_vector(self.connection)
            logger.info(f"Connected to PostgreSQL: {self.conn_params['host']}:{self.conn_params['port']}/{self.conn_params['database']}")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    def add_points(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """Add chunks with pgvector embeddings to PostgreSQL (HNSW indexed)."""
        if not self.connection:
            self._connect()

        cursor = self.connection.cursor()
        try:
            for chunk, embedding in zip(chunks, embeddings):
                cursor.execute("""
                    INSERT INTO chunks
                    (document_id, chunk_index, text, section, page_number, embedding, department, category)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    chunk.get('document_id'),
                    chunk.get('chunk_index', 0),
                    chunk.get('text'),
                    chunk.get('section'),
                    chunk.get('page_number', 0),
                    embedding,
                    chunk.get('department'),
                    chunk.get('category')
                ))

            self.connection.commit()
            logger.info(f"Added {len(chunks)} chunks to PostgreSQL with pgvector")
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error adding points: {e}")
            raise
        finally:
            cursor.close()

    def search(self, query_vector: List[float], top_k: int = 50) -> List[Dict[str, Any]]:
        """Search using pgvector with HNSW index (cosine distance operator <->)."""
        if not self.connection:
            self._connect()

        cursor = None
        try:
            # Reset connection if in error state
            self.connection.rollback()

            cursor = self.connection.cursor(cursor_factory=RealDictCursor)

            # Convert list to pgvector format (as string)
            query_str = "[" + ",".join(str(x) for x in query_vector) + "]"

            cursor.execute("""
                SELECT
                    id,
                    document_id,
                    chunk_index,
                    text,
                    section,
                    page_number,
                    department,
                    category,
                    created_at,
                    (2 - (embedding <-> %s::vector)) / 2 AS score
                FROM chunks
                WHERE embedding IS NOT NULL
                ORDER BY embedding <-> %s::vector
                LIMIT %s
            """, (query_str, query_str, top_k))

            results = cursor.fetchall()
            formatted_results = []
            for idx, row in enumerate(results):
                formatted_results.append({
                    'chunk_id': row['id'],
                    'document_id': row['document_id'],
                    'text': row['text'],
                    'section': row['section'],
                    'page': row['page_number'],
                    'department': row['department'],
                    'category': row['category'],
                    'created_at': str(row['created_at']),
                    'score': float(row['score']),
                    'rank': idx
                })

            return formatted_results
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def get_all_texts(self) -> List[str]:
        """Retrieve all chunk texts for BM25 indexing."""
        if not self.connection:
            self._connect()

        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT text FROM chunks ORDER BY id")
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error retrieving texts: {e}")
            return []
        finally:
            cursor.close()

    def get_all_chunks(self) -> List[Dict[str, Any]]:
        """Retrieve all chunks with metadata for BM25."""
        if not self.connection:
            self._connect()

        cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("""
                SELECT id, document_id, text, section, page_number, department, category, created_at
                FROM chunks
                ORDER BY id
            """)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error retrieving chunks: {e}")
            return []
        finally:
            cursor.close()

    def delete_all(self):
        """Delete all chunks from database."""
        if not self.connection:
            self._connect()

        cursor = self.connection.cursor()
        try:
            cursor.execute("DELETE FROM chunks")
            self.connection.commit()
            logger.info("All chunks deleted from PostgreSQL")
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Error deleting chunks: {e}")
        finally:
            cursor.close()

    def get_count(self) -> int:
        """Get total number of chunks in database."""
        if not self.connection:
            self._connect()

        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM chunks")
            count = cursor.fetchone()[0]
            return count
        except Exception as e:
            logger.error(f"Error getting count: {e}")
            return 0
        finally:
            cursor.close()

    def get_chunk_context(self, doc_id: int, chunk_index: int, offset: int) -> Optional[Dict[str, Any]]:
        """
        Get neighboring chunk for context expansion.

        Args:
            doc_id: Document ID
            chunk_index: Current chunk index
            offset: -1 for previous chunk, +1 for next chunk

        Returns:
            Chunk dict with text, or None if not found
        """
        if not self.connection:
            self._connect()

        cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        try:
            target_index = chunk_index + offset
            cursor.execute(
                "SELECT id, text, chunk_index FROM chunks WHERE document_id = %s AND chunk_index = %s LIMIT 1",
                (doc_id, target_index)
            )
            result = cursor.fetchone()
            return dict(result) if result else None
        except Exception as e:
            logger.warning(f"Error fetching context chunk: {e}")
            return None
        finally:
            cursor.close()

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("PostgreSQL connection closed")

    def __del__(self):
        """Cleanup on deletion."""
        self.close()
