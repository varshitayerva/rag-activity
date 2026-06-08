from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class RRFFusion:
    """Reciprocal Rank Fusion - combines vector and BM25 search results."""

    @staticmethod
    def get_optimal_k(corpus_size: int) -> int:
        """
        Determine optimal k parameter based on corpus size.

        Args:
            corpus_size: Number of chunks in corpus

        Returns:
            Optimal k value

        Reference (empirically tuned):
        - <1,000 chunks: k=20 (top results matter more)
        - 1,000-10,000: k=40 (balanced)
        - 10,000-100,000: k=60 (current default)
        - >100,000: k=100 (dilute top results)
        """
        if corpus_size < 1_000:
            return 20
        elif corpus_size < 10_000:
            return 40
        elif corpus_size < 100_000:
            return 60
        else:
            return 100

    @staticmethod
    def fuse(vector_results: List[Dict[str, Any]],
             bm25_results: List[Dict[str, Any]],
             k: int = None,
             corpus_size: int = None,
             vector_weight: float = 0.5,
             bm25_weight: float = 0.5) -> List[Dict[str, Any]]:
        """Fuse vector search and BM25 results using Weighted RRF.

        Formula: score = vector_weight * 1/(k + rank_vector) + bm25_weight * 1/(k + rank_bm25)

        Args:
            vector_results: Results from vector search (with 'rank', 'score', 'text')
            bm25_results: Results from BM25 search (with 'rank', 'score', 'text')
            k: RRF parameter (if None, auto-detect from corpus_size)
            corpus_size: Size of corpus for k auto-detection
            vector_weight: Weight for vector search (default 0.5 for backward compatibility)
            bm25_weight: Weight for BM25 search (default 0.5 for backward compatibility)

        Returns:
            Fused results sorted by combined weighted RRF score
        """
        # Validate weights sum to ~1.0 (allow small tolerance)
        total_weight = vector_weight + bm25_weight
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Weights don't sum to 1.0 (total: {total_weight}). Normalizing...")
            vector_weight = vector_weight / total_weight
            bm25_weight = bm25_weight / total_weight

        # Auto-detect k if not provided
        if k is None:
            if corpus_size is None:
                k = 60  # Default fallback
            else:
                k = RRFFusion.get_optimal_k(corpus_size)
                logger.debug(f"Auto-detected RRF k={k} for corpus_size={corpus_size}")
        # Map text to RRF components
        rrf_scores = {}

        # Process vector results
        for result in vector_results:
            text = result['text']
            rank = result['rank']
            vector_score = 1.0 / (k + rank)
            rrf_scores[text] = rrf_scores.get(text, {})
            rrf_scores[text]['vector_score'] = vector_score
            rrf_scores[text]['vector_rank'] = rank
            rrf_scores[text]['vector_relevance'] = result['score']
            rrf_scores[text]['from_vector'] = True

        # Process BM25 results
        for result in bm25_results:
            text = result['text']
            rank = result['rank']
            bm25_score = 1.0 / (k + rank)
            rrf_scores[text] = rrf_scores.get(text, {})
            rrf_scores[text]['bm25_score'] = bm25_score
            rrf_scores[text]['bm25_rank'] = rank
            rrf_scores[text]['bm25_relevance'] = result['score']
            rrf_scores[text]['from_bm25'] = True

        # Calculate weighted combined RRF scores while preserving metadata
        combined_results = []
        for text, scores in rrf_scores.items():
            # Apply weights to individual scores then combine
            vector_component = (scores.get('vector_score', 0) * vector_weight) if scores.get('from_vector') else 0
            bm25_component = (scores.get('bm25_score', 0) * bm25_weight) if scores.get('from_bm25') else 0
            combined_score = vector_component + bm25_component

            # Get metadata from either vector or BM25 result
            metadata = {}
            if scores.get('from_vector'):
                # Find original vector result to get metadata
                for result in vector_results:
                    if result['text'] == text:
                        metadata = {k: v for k, v in result.items() if k not in ['text', 'score', 'rank']}
                        break
            if scores.get('from_bm25') and not metadata:
                # Fall back to BM25 metadata if vector doesn't have it
                for result in bm25_results:
                    if result['text'] == text:
                        metadata = {k: v for k, v in result.items() if k not in ['text', 'score', 'rank']}
                        break

            combined_results.append({
                'text': text,
                'combined_rrf_score': combined_score,
                'vector_rank': scores.get('vector_rank', None),
                'vector_score': scores.get('vector_relevance', None),
                'bm25_rank': scores.get('bm25_rank', None),
                'bm25_score': scores.get('bm25_relevance', None),
                'from_vector': scores.get('from_vector', False),
                'from_bm25': scores.get('from_bm25', False),
                'score': combined_score,  # Add final score for response
                **metadata  # Include all metadata
            })

        # Sort by combined RRF score descending
        combined_results.sort(key=lambda x: x['combined_rrf_score'], reverse=True)

        # Add final rank and format for response
        final_results = []
        for idx, result in enumerate(combined_results):
            filename = result.get('filename', 'Unknown')
            final_results.append({
                'text': result['text'],
                'score': result['combined_rrf_score'],
                'rank': idx,
                'chunk_id': result.get('chunk_id', ''),
                'doc_id': result.get('doc_id', ''),
                'filename': filename,
                'doc': filename,
                'section': result.get('section', ''),
                'page': result.get('page', 0),
                'department': result.get('department', ''),
                'category': result.get('category', ''),
                'vector_score': result.get('vector_score', 0),  # Original vector similarity (0-1)
                'bm25_score': result.get('bm25_score', 0),  # Original BM25 score
            })

        return final_results

    @staticmethod
    def apply_metadata_filter(results: List[Dict[str, Any]],
                             metadata_filter: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Filter results by metadata constraints.

        Args:
            results: Fused results with metadata payload
            metadata_filter: Dict with optional keys: department, category, date_from, date_to

        Returns:
            Filtered results
        """
        if not metadata_filter:
            return results

        filtered = []
        for result in results:
            # Check department filter
            if 'department' in metadata_filter and metadata_filter['department']:
                if result.get('department') != metadata_filter['department']:
                    continue

            # Check category filter
            if 'category' in metadata_filter and metadata_filter['category']:
                if result.get('category') != metadata_filter['category']:
                    continue

            # Check date range (would require ISO datetime parsing in real impl)
            if 'date_from' in metadata_filter and metadata_filter['date_from']:
                if result.get('uploaded_at', '') < metadata_filter['date_from']:
                    continue

            if 'date_to' in metadata_filter and metadata_filter['date_to']:
                if result.get('uploaded_at', '') > metadata_filter['date_to']:
                    continue

            filtered.append(result)

        return filtered
