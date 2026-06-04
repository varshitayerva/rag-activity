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

    def __init__(self, host: str = "localhost", user: str = "postgres",
                 password: str = "1234", database: str = "fde_rag", port: int = 5432):
        """Initialize PostgreSQL connection."""
        self.conn_params = {
            "host": host,
            "user": user,
            "password": password,
            "database": database,
            "port": port
        }
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
                    1 - (embedding <-> %s::vector) AS score
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

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("PostgreSQL connection closed")

    def __del__(self):
        """Cleanup on deletion."""
        self.close()
