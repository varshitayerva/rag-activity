from typing import List, Dict, Any

class RRFFusion:
    """Reciprocal Rank Fusion - combines vector and BM25 search results."""

    @staticmethod
    def fuse(vector_results: List[Dict[str, Any]],
             bm25_results: List[Dict[str, Any]],
             k: int = 60) -> List[Dict[str, Any]]:
        """Fuse vector search and BM25 results using RRF.

        Formula: score = 1/(k + rank_vector) + 1/(k + rank_bm25)

        Args:
            vector_results: Results from vector search (with 'rank', 'score', 'text')
            bm25_results: Results from BM25 search (with 'rank', 'score', 'text')
            k: RRF parameter (default 60, controls weight of top results)

        Returns:
            Fused results sorted by combined RRF score
        """
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

        # Calculate combined RRF scores
        combined_results = []
        for text, scores in rrf_scores.items():
            combined_score = scores.get('vector_score', 0) + scores.get('bm25_score', 0)
            combined_results.append({
                'text': text,
                'combined_rrf_score': combined_score,
                'vector_rank': scores.get('vector_rank', None),
                'vector_score': scores.get('vector_relevance', None),
                'bm25_rank': scores.get('bm25_rank', None),
                'bm25_score': scores.get('bm25_relevance', None),
                'from_vector': scores.get('from_vector', False),
                'from_bm25': scores.get('from_bm25', False),
            })

        # Sort by combined RRF score descending
        combined_results.sort(key=lambda x: x['combined_rrf_score'], reverse=True)

        # Add final rank
        for idx, result in enumerate(combined_results):
            result['final_rank'] = idx

        return combined_results

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
