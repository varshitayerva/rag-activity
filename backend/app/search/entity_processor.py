"""Entity Extraction & Linking for intelligent result boosting"""

import logging
from typing import List, Dict, Any, Optional, Set
import re

logger = logging.getLogger(__name__)


class EntityProcessor:
    """Extract and track entities in queries and documents"""

    # Common entity patterns
    ENTITY_PATTERNS = {
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'phone': r'\+?1?\d{9,15}',
        'url': r'https?://[^\s]+',
        'date': r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
        'number': r'\b\d+(?:\.\d+)?\b',
        'version': r'v?\d+\.\d+(?:\.\d+)?',
    }

    def __init__(self):
        """Initialize entity processor"""
        self.entity_index = {}  # {entity: [doc_ids]}
        self.extracted_cache = {}  # Cache extracted entities

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities from text.

        Args:
            text: Text to extract entities from

        Returns:
            Dict mapping entity type to list of entities found
        """
        if text in self.extracted_cache:
            return self.extracted_cache[text]

        entities = {}

        # Extract based on patterns
        for entity_type, pattern in self.ENTITY_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities[entity_type] = list(set(matches))  # Remove duplicates

        # Simple NER for common noun phrases
        entities['keywords'] = self._extract_keywords(text)

        self.extracted_cache[text] = entities
        logger.debug(f"Extracted entities: {len(entities)} types, {sum(len(v) for v in entities.values())} total")

        return entities

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract important keywords/noun phrases.

        Args:
            text: Text to extract from

        Returns:
            List of important keywords
        """
        # Simple keyword extraction: words capitalized or in ALL CAPS
        words = text.split()
        keywords = []

        for word in words:
            # Check if word is capitalized (potential proper noun) or all caps (acronym)
            if (word[0].isupper() and len(word) > 2) or word.isupper():
                # Remove punctuation
                clean_word = re.sub(r'[^\w]', '', word)
                if clean_word and len(clean_word) > 2:
                    keywords.append(clean_word)

        return list(set(keywords))  # Remove duplicates

    def score_entity_match(
        self,
        query_entities: Dict[str, List[str]],
        result_entities: Dict[str, List[str]]
    ) -> float:
        """
        Score how well result entities match query entities.

        Args:
            query_entities: Entities from query
            result_entities: Entities from result

        Returns:
            Match score (0-1)
        """
        total_query_entities = sum(len(v) for v in query_entities.values())
        if total_query_entities == 0:
            return 0.5  # Neutral score

        matches = 0
        for entity_type, query_list in query_entities.items():
            result_list = result_entities.get(entity_type, [])
            # Count matching entities
            for q_ent in query_list:
                for r_ent in result_list:
                    if q_ent.lower() in r_ent.lower() or r_ent.lower() in q_ent.lower():
                        matches += 1

        # Normalize score
        score = min(1.0, matches / max(1, total_query_entities))
        return score

    def get_boost_factor(self, entity_match_score: float) -> float:
        """
        Get boost factor from entity match score.

        Args:
            entity_match_score: Match score (0-1)

        Returns:
            Boost factor for result score
        """
        # Boost factor: 1.0 (no boost) to 1.3 (30% boost)
        return 1.0 + (entity_match_score * 0.3)

    def index_entities(self, doc_id: str, text: str):
        """
        Index entities in a document.

        Args:
            doc_id: Document ID
            text: Document text
        """
        entities = self.extract_entities(text)

        # Index all entities
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                key = f"{entity_type}:{entity.lower()}"
                if key not in self.entity_index:
                    self.entity_index[key] = set()
                self.entity_index[key].add(doc_id)

        logger.debug(f"Indexed {len(self.entity_index)} unique entities for doc {doc_id}")

    def get_stats(self) -> Dict[str, Any]:
        """Get entity processor statistics"""
        return {
            "total_unique_entities": len(self.entity_index),
            "cache_size": len(self.extracted_cache),
            "entity_types": list(self.ENTITY_PATTERNS.keys()) + ["keywords"]
        }

    def clear_cache(self):
        """Clear extraction cache"""
        self.extracted_cache.clear()
        logger.info("Entity extraction cache cleared")
