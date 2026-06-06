"""Query Intelligence Module - Intent Detection, Expansion, Classification"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class QueryIntent(str, Enum):
    """Query intent classification types"""
    CONCEPTUAL = "conceptual"  # "What is X?", "Define X"
    PROCEDURAL = "procedural"  # "How to X?", "Steps to X"
    FACTUAL = "factual"        # "Who is X?", "When did X?", "Where is X?"
    NAVIGATIONAL = "navigational"  # "Find X document", "Show me X"
    COMPARATIVE = "comparative"  # "Compare X vs Y", "Difference between"


class QueryProcessor:
    """Process queries for better retrieval and ranking"""

    # Intent detection keywords
    INTENT_KEYWORDS = {
        QueryIntent.PROCEDURAL: [
            "how", "how to", "steps", "process", "procedure", "tutorial",
            "guide", "instructions", "implement", "configure", "setup",
            "install", "deploy", "build", "create", "develop"
        ],
        QueryIntent.CONCEPTUAL: [
            "what", "define", "explain", "concept", "theory", "understand",
            "meaning", "difference", "relation", "background", "overview"
        ],
        QueryIntent.FACTUAL: [
            "who", "when", "where", "which", "fact", "information",
            "data", "find", "locate", "specific", "detail", "example"
        ],
        QueryIntent.COMPARATIVE: [
            "compare", "versus", "vs", "difference", "similar", "better",
            "pros and cons", "tradeoff", "advantage", "disadvantage"
        ],
        QueryIntent.NAVIGATIONAL: [
            "find", "show", "list", "get", "retrieve", "fetch", "search",
            "document", "page", "section", "chapter"
        ]
    }

    # Simple synonym/expansion dictionary
    QUERY_SYNONYMS = {
        "authentication": ["auth", "login", "signin", "security", "credentials", "password"],
        "configuration": ["config", "setup", "setting", "parameter", "option"],
        "database": ["db", "sql", "data", "storage", "persistence"],
        "integration": ["integrate", "connect", "interface", "link", "api"],
        "performance": ["speed", "latency", "optimization", "throughput", "efficiency"],
        "security": ["secure", "encrypt", "authenticate", "authorize", "protection"],
        "error": ["bug", "issue", "problem", "failure", "exception", "crash"],
        "deployment": ["deploy", "release", "launch", "production", "publish"],
        "testing": ["test", "quality", "qa", "validate", "verify"],
        "documentation": ["doc", "docs", "guide", "manual", "readme"]
    }

    def __init__(self):
        """Initialize query processor"""
        self.intent_cache = {}  # Simple cache for intent detection
        self.expansion_cache = {}  # Cache for query expansions

    def detect_intent(self, query: str) -> QueryIntent:
        """
        Detect the intent of a query.

        Args:
            query: User query string

        Returns:
            QueryIntent enum value
        """
        # Check cache first
        if query.lower() in self.intent_cache:
            return self.intent_cache[query.lower()]

        query_lower = query.lower()
        scores = {intent: 0 for intent in QueryIntent}

        # Score each intent based on keyword matches
        for intent, keywords in self.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    scores[intent] += 1

        # Determine intent with highest score
        detected_intent = max(scores, key=scores.get) if max(scores.values()) > 0 else QueryIntent.FACTUAL

        # Cache result
        self.intent_cache[query_lower] = detected_intent

        logger.debug(f"Query: '{query}' → Intent: {detected_intent.value} (scores: {scores})")
        return detected_intent

    def get_intent_weights(self, intent: QueryIntent) -> Dict[str, float]:
        """
        Get RRF weights based on query intent.

        Args:
            intent: QueryIntent enum

        Returns:
            Dict with vector_weight and bm25_weight
        """
        weights_map = {
            QueryIntent.CONCEPTUAL: {"vector_weight": 0.7, "bm25_weight": 0.3},
            QueryIntent.PROCEDURAL: {"vector_weight": 0.6, "bm25_weight": 0.4},
            QueryIntent.FACTUAL: {"vector_weight": 0.4, "bm25_weight": 0.6},
            QueryIntent.NAVIGATIONAL: {"vector_weight": 0.3, "bm25_weight": 0.7},
            QueryIntent.COMPARATIVE: {"vector_weight": 0.65, "bm25_weight": 0.35},
        }
        return weights_map.get(intent, {"vector_weight": 0.5, "bm25_weight": 0.5})

    def expand_query_synonyms(self, query: str) -> List[str]:
        """
        Generate query expansions using synonym database.

        Args:
            query: Original query

        Returns:
            List of expanded query variations
        """
        if query.lower() in self.expansion_cache:
            return self.expansion_cache[query.lower()]

        expansions = [query]  # Include original
        query_lower = query.lower()

        # Find synonyms for words in query
        for word, synonyms in self.QUERY_SYNONYMS.items():
            if word in query_lower:
                # Create variations with each synonym
                for synonym in synonyms[:2]:  # Limit to 2 per word to avoid explosion
                    variation = query_lower.replace(word, synonym)
                    if variation not in expansions:
                        expansions.append(variation)

        # Limit to 5 total expansions
        result = expansions[:5]
        self.expansion_cache[query.lower()] = result

        logger.debug(f"Query expansion: '{query}' → {result}")
        return result

    def extract_keywords(self, query: str) -> List[str]:
        """
        Extract important keywords from query.

        Args:
            query: Query string

        Returns:
            List of important keywords
        """
        # Remove common words
        stop_words = {
            "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "from", "by", "is", "are", "was", "were", "be", "been",
            "have", "has", "do", "does", "did", "can", "could", "will", "would",
            "should", "may", "might", "must", "shall", "that", "this", "it"
        }

        # Tokenize and filter
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        return keywords

    def classify_complexity(self, query: str) -> str:
        """
        Classify query complexity (simple/moderate/complex).

        Args:
            query: Query string

        Returns:
            "simple" | "moderate" | "complex"
        """
        word_count = len(query.split())
        keyword_count = len(self.extract_keywords(query))
        question_count = query.count("?") + query.count("and") + query.count("with")

        if word_count <= 5 and keyword_count <= 3:
            return "simple"
        elif word_count <= 15 and keyword_count <= 6:
            return "moderate"
        else:
            return "complex"

    def prepare_query(
        self,
        query: str,
        detect_intent: bool = True,
        expand: bool = False
    ) -> Dict[str, Any]:
        """
        Prepare query with all intelligence processing.

        Args:
            query: Original user query
            detect_intent: Whether to detect intent
            expand: Whether to expand query variations

        Returns:
            Dict with processed query information
        """
        result = {
            "original": query,
            "intent": None,
            "intent_weights": None,
            "keywords": self.extract_keywords(query),
            "complexity": self.classify_complexity(query),
            "expansions": [query],  # Default: just original
        }

        if detect_intent:
            intent = self.detect_intent(query)
            result["intent"] = intent.value
            result["intent_weights"] = self.get_intent_weights(intent)

        if expand:
            result["expansions"] = self.expand_query_synonyms(query)

        return result

    def clear_cache(self):
        """Clear all caches"""
        self.intent_cache.clear()
        self.expansion_cache.clear()
        logger.info("Query processor caches cleared")
