"""
PostgreSQL client for vector storage and similarity search.
Stores embeddings as binary data and computes similarity in Python.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any
import numpy as np
import pickle

class PostgresVectorDB:
    """Vector database using PostgreSQL + pgvector."""

    def __init__(self, host: str = "localhost", user: str = "postgres",
                 password: str = "1234", database: str = "fde_rag", port: int = 5432):
        """Initialize PostgreSQL connection.

        Args:
            host: PostgreSQL host
            user: PostgreSQL username
            password: PostgreSQL password
            database: Database name
            port: PostgreSQL port
        """
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
        """Establish database connection."""
        try:
            self.connection = psycopg2.connect(**self.conn_params)
            print(f"Connected to PostgreSQL at {self.conn_params['host']}:{self.conn_params['port']}/{self.conn_params['database']}")
        except Exception as e:
            print(f"Failed to connect to PostgreSQL: {e}")
            raise

    def add_points(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """Add chunks with embeddings to PostgreSQL.

        Args:
            chunks: List of chunk dicts with metadata
            embeddings: List of embedding vectors
        """
        if not self.connection:
            self._connect()

        cursor = self.connection.cursor()
        try:
            for chunk, embedding in zip(chunks, embeddings):
                # Convert embedding to binary format using pickle
                embedding_array = np.array(embedding, dtype=np.float32)
                embedding_bytes = pickle.dumps(embedding_array)

                cursor.execute("""
                INSERT INTO chunks (chunk_id, text, doc_id, filename, section, page, department, category, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (chunk_id) DO UPDATE SET
                    text = EXCLUDED.text,
                    embedding = EXCLUDED.embedding
                """, (
                    chunk.get('chunk_id'),
                    chunk.get('text'),
                    chunk.get('doc_id', ''),
                    chunk.get('filename', ''),
                    chunk.get('section', ''),
                    chunk.get('page', 0),
                    chunk.get('department', ''),
                    chunk.get('category', ''),
                    embedding_bytes
                ))

            self.connection.commit()
            print(f"Added {len(chunks)} chunks to PostgreSQL")
        except Exception as e:
            self.connection.rollback()
            print(f"Error adding points: {e}")
            raise
        finally:
            cursor.close()

    def search(self, query_vector: List[float], top_k: int = 50) -> List[Dict[str, Any]]:
        """Search for similar vectors using cosine similarity.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return

        Returns:
            List of search results with scores
        """
        if not self.connection:
            self._connect()

        cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        try:
            # Fetch all chunks and compute similarity in Python
            cursor.execute("""
            SELECT
                id,
                chunk_id,
                text,
                doc_id,
                filename,
                section,
                page,
                department,
                category,
                embedding
            FROM chunks
            ORDER BY id
            """)

            results = cursor.fetchall()

            # Compute cosine similarity
            query_array = np.array(query_vector, dtype=np.float32)
            query_norm = np.linalg.norm(query_array)

            similarities = []
            for row in results:
                if row['embedding']:
                    try:
                        stored_array = pickle.loads(row['embedding'])
                        stored_norm = np.linalg.norm(stored_array)
                        if query_norm > 0 and stored_norm > 0:
                            similarity = np.dot(query_array, stored_array) / (query_norm * stored_norm)
                        else:
                            similarity = 0.0
                    except:
                        similarity = 0.0
                else:
                    similarity = 0.0

                similarities.append((row, float(similarity)))

            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)

            # Format results
            formatted_results = []
            for idx, (row, score) in enumerate(similarities[:top_k]):
                formatted_results.append({
                    'chunk_id': row['chunk_id'],
                    'text': row['text'],
                    'doc_id': row['doc_id'],
                    'filename': row['filename'],
                    'section': row['section'],
                    'page': row['page'],
                    'department': row['department'],
                    'category': row['category'],
                    'score': score,
                    'rank': idx
                })

            return formatted_results

        except Exception as e:
            print(f"Error searching: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            cursor.close()

    def get_all_texts(self) -> List[str]:
        """Retrieve all chunk texts for BM25 indexing."""
        if not self.connection:
            self._connect()

        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT text FROM chunks ORDER BY id")
            results = cursor.fetchall()
            return [row[0] for row in results]
        except Exception as e:
            print(f"Error retrieving texts: {e}")
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
            SELECT chunk_id, text, doc_id, filename, section, page, department, category
            FROM chunks
            ORDER BY id
            """)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error retrieving chunks: {e}")
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
            print("All chunks deleted from PostgreSQL")
        except Exception as e:
            self.connection.rollback()
            print(f"Error deleting chunks: {e}")
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
            print(f"Error getting count: {e}")
            return 0
        finally:
            cursor.close()

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            print("PostgreSQL connection closed")

    def __del__(self):
        """Cleanup on deletion."""
        self.close()
