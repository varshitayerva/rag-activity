"""Answer-Aware Retrieval and Query Decomposition"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import re

logger = logging.getLogger(__name__)


class QueryDecomposer:
    """Decompose complex queries into sub-questions"""

    def __init__(self):
        """Initialize query decomposer"""
        self.decomposition_cache = {}

    def is_complex_query(self, query: str) -> bool:
        """
        Check if query is complex (multi-part).

        Args:
            query: Query string

        Returns:
            True if complex
        """
        # Multi-part indicators
        indicators = [
            ' and ',
            ' vs ',
            ' versus ',
            ' compare ',
            ' difference ',
            ' both ',
            ' how and ',
            '?.*?and',
            '?.*?but'
        ]

        query_lower = query.lower()
        return any(ind in query_lower for ind in indicators)

    def decompose_query(self, query: str) -> List[str]:
        """
        Decompose complex query into sub-queries.

        Args:
            query: Complex query

        Returns:
            List of sub-queries
        """
        if query in self.decomposition_cache:
            return self.decomposition_cache[query]

        if not self.is_complex_query(query):
            return [query]

        sub_queries = []
        query_lower = query.lower()

        # Split on 'and'
        if ' and ' in query_lower:
            parts = query.split(' and ')
            sub_queries.extend(parts)
        # Split on 'vs/versus'
        elif ' vs ' in query_lower or ' versus ' in query_lower:
            parts = re.split(r' vs\.? | versus ', query, flags=re.IGNORECASE)
            sub_queries.extend(parts)
        # Split on 'compare'
        elif 'compare' in query_lower:
            # Extract entities being compared
            match = re.search(r'compare\s+(\w+)\s+(?:and|with)\s+(\w+)', query, re.IGNORECASE)
            if match:
                sub_queries.append(f"What is {match.group(1)}")
                sub_queries.append(f"What is {match.group(2)}")
            else:
                sub_queries.append(query)
        else:
            sub_queries.append(query)

        # Clean up sub-queries
        sub_queries = [q.strip() for q in sub_queries if q.strip()]

        self.decomposition_cache[query] = sub_queries
        logger.debug(f"Decomposed query into {len(sub_queries)} sub-queries")

        return sub_queries

    def merge_results(
        self,
        sub_query_results: List[List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Merge results from multiple sub-queries.

        Args:
            sub_query_results: Results for each sub-query

        Returns:
            Merged and deduplicated results
        """
        # Deduplicate by chunk_id
        seen = {}
        merged = []

        for results in sub_query_results:
            for result in results:
                chunk_id = result.get('chunk_id')
                if chunk_id not in seen:
                    seen[chunk_id] = result
                    merged.append(result)
                else:
                    # Boost score if appears in multiple sub-query results
                    seen[chunk_id]['score'] *= 1.1

        # Re-sort by score
        merged.sort(key=lambda x: x.get('score', 0), reverse=True)

        return merged


class AnswerAwarenessRanker:
    """Rank documents based on answer relevance"""

    def __init__(self):
        """Initialize answer-aware ranker"""
        self.answer_keywords = {}

    def extract_answer_keywords(self, query: str) -> List[str]:
        """
        Extract keywords that would appear in ideal answer.

        Args:
            query: Query string

        Returns:
            List of expected answer keywords
        """
        keywords = []

        # Who questions: expect names
        if query.lower().startswith('who'):
            keywords.extend(['person', 'name', 'founder', 'author', 'creator'])

        # What/Which questions: expect definitions/categories
        if query.lower().startswith(('what', 'which')):
            keywords.extend(['is', 'are', 'definition', 'type', 'category'])

        # How questions: expect steps/process
        if query.lower().startswith('how'):
            keywords.extend(['step', 'process', 'procedure', 'method', 'way'])

        # When questions: expect dates/times
        if query.lower().startswith('when'):
            keywords.extend(['date', 'time', 'year', 'month', 'day', 'period'])

        # Where questions: expect locations
        if query.lower().startswith('where'):
            keywords.extend(['location', 'place', 'country', 'city', 'address'])

        # Why questions: expect reasons/causes
        if query.lower().startswith('why'):
            keywords.extend(['because', 'reason', 'cause', 'due', 'result'])

        return keywords

    def score_answer_relevance(
        self,
        result_text: str,
        answer_keywords: List[str]
    ) -> float:
        """
        Score how well result contains answer keywords.

        Args:
            result_text: Result text
            answer_keywords: Expected answer keywords

        Returns:
            Relevance score (0-1)
        """
        if not answer_keywords:
            return 0.5

        text_lower = result_text.lower()
        matches = sum(1 for kw in answer_keywords if kw in text_lower)
        score = min(1.0, matches / len(answer_keywords))

        return score

    def boost_answer_aware_results(
        self,
        results: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Boost results that contain answer-relevant keywords.

        Args:
            results: Search results
            query: Original query

        Returns:
            Re-ranked results
        """
        answer_keywords = self.extract_answer_keywords(query)

        boosted = []
        for result in results:
            text = result.get('text', '')
            relevance_score = self.score_answer_relevance(text, answer_keywords)

            # Apply answer-aware boost (1.0 to 1.25)
            boost_factor = 1.0 + (relevance_score * 0.25)
            result['original_score'] = result.get('score', 0)
            result['score'] = result.get('score', 0) * boost_factor
            result['answer_aware_boost'] = boost_factor

            boosted.append(result)

        # Re-sort
        boosted.sort(key=lambda x: x.get('score', 0), reverse=True)

        logger.debug(f"Applied answer-aware ranking to {len(boosted)} results")
        return boosted
