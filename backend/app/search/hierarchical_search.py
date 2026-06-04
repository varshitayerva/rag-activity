"""Two-stage hierarchical search: filter documents → retrieve chunks."""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class HierarchicalSearchService:
    """Two-stage search: document filtering + chunk retrieval."""

    def __init__(self, hybrid_search_service=None, embeddings_client=None, db_client=None):
        """
        Initialize hierarchical search service.

        Args:
            hybrid_search_service: HybridSearchService instance
            embeddings_client: EmbeddingsClient instance
            db_client: PostgresClient instance
        """
        # Lazy import to avoid circular imports
        if hybrid_search_service is None:
            from backend.app.search.hybrid_search import HybridSearchService
            hybrid_search_service = HybridSearchService()

        if embeddings_client is None:
            from backend.app.search.embeddings import EmbeddingsClient
            embeddings_client = EmbeddingsClient()

        if db_client is None:
            from backend.app.database.postgres import db_client as default_db
            db_client = default_db

        self.hybrid_search = hybrid_search_service
        self.embeddings = embeddings_client
        self.db = db_client

    async def search(self, query: str, top_k: int = 10,
                     doc_top_k: int = 5) -> Dict[str, Any]:
        """
        Hierarchical search with two stages.

        Args:
            query: User search query
            top_k: Number of final chunk results
            doc_top_k: Number of documents to search (stage 1)

        Returns:
            Search results with hierarchical metadata
        """
        # Stage 1: Filter documents by summary
        query_embedding = self.embeddings.embed_query(query)

        doc_results = self.db.search_documents_by_summary(
            query_embedding,
            top_k=doc_top_k
        )

        if not doc_results:
            logger.warning("No relevant documents found in stage 1")
            return {
                'query': query,
                'chunks': [],
                'search_type': 'hierarchical',
                'num_results': 0,
                'stage1_docs': 0,
            }

        relevant_doc_ids = [d['document_id'] for d in doc_results]

        # Stage 2: Search chunks within relevant documents
        chunk_results = await self.hybrid_search.search(
            query,
            top_k=top_k,
            metadata_filter={'document_ids': relevant_doc_ids}  # Filter to relevant docs
        )

        return {
            'query': query,
            'chunks': chunk_results.get('chunks', []),
            'search_type': 'hierarchical',
            'num_results': len(chunk_results.get('chunks', [])),
            'stage1_docs': len(doc_results),
            'stage1_results': doc_results,
        }
