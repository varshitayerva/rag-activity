import re
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class ConfidenceMetrics:
    """Confidence metrics for a generated response."""
    source_coverage: float
    hallucination_risk: float
    answer_completeness: float
    uncertainty_markers: int
    overall_confidence: float


class ConfidenceScorer:
    """Score confidence in generated responses."""

    # Uncertainty markers that indicate low confidence
    UNCERTAINTY_PHRASES = [
        r"\b(might|may|possibly|perhaps|seems|appears|suggests)\b",
        r"\bi\s+(think|believe|guess|assume|suppose)\b",
        r"\b(not (sure|certain)|unsure|unclear)\b",
        r"\b(unclear|ambiguous|vague|uncertain)\b",
        r"\bi\s+don'?t\s+(know|have|remember)\b",
    ]

    # Strong confidence markers
    CONFIDENCE_PHRASES = [
        r"\b(definitely|certainly|absolutely|clearly|obviously)\b",
        r"\b(based on|according to|as stated in)\b",
        r"\b(the documentation|the guide|the manual)\b",
        r"\b\d+(\.\d+)?%\b",  # Percentages
    ]

    def __init__(self):
        self.uncertainty_pattern = self._compile_patterns(self.UNCERTAINTY_PHRASES)
        self.confidence_pattern = self._compile_patterns(self.CONFIDENCE_PHRASES)

    @staticmethod
    def _compile_patterns(patterns: List[str]) -> re.Pattern:
        """Compile regex patterns into single pattern."""
        combined = "|".join(f"({p})" for p in patterns)
        return re.compile(combined, re.IGNORECASE)

    def score(
        self,
        response: str,
        chunks: List[Dict],
        query: str,
    ) -> ConfidenceMetrics:
        """Score response confidence.

        Args:
            response: Generated response text
            chunks: Source chunks used for generation
            query: Original user query

        Returns:
            ConfidenceMetrics with 0-1 scores
        """
        # Calculate individual metrics
        source_coverage = self._score_source_coverage(response, chunks)
        hallucination_risk = self._score_hallucination_risk(response, chunks)
        completeness = self._score_completeness(response, query)
        uncertainty_count = self._count_uncertainty_markers(response)

        # Calculate overall confidence (weighted average)
        overall = (
            source_coverage * 0.35 +
            (1.0 - hallucination_risk) * 0.35 +
            completeness * 0.20 +
            max(0, 1.0 - (uncertainty_count * 0.05)) * 0.10
        )

        return ConfidenceMetrics(
            source_coverage=source_coverage,
            hallucination_risk=hallucination_risk,
            answer_completeness=completeness,
            uncertainty_markers=uncertainty_count,
            overall_confidence=max(0.0, min(1.0, overall)),
        )

    def _score_source_coverage(self, response: str, chunks: List[Dict]) -> float:
        """Score how well response is covered by sources.

        Returns: 0-1 score (higher = better coverage)
        """
        if not chunks:
            return 0.0

        # Extract cited sources from response
        cited_count = 0
        for chunk in chunks:
            source = chunk.get("source", "")
            if source and source.lower() in response.lower():
                cited_count += 1

        coverage = cited_count / len(chunks) if chunks else 0.0
        return min(1.0, coverage)

    def _score_hallucination_risk(self, response: str, chunks: List[Dict]) -> float:
        """Score risk of hallucination (0-1, higher = higher risk).

        Returns: 0-1 score (lower = better, less hallucination)
        """
        risk = 0.0

        # Check for "I don't have reliable information" fallback
        if "don't have reliable information" in response.lower():
            return 0.0  # Safe fallback

        # Check for specific technical claims not in sources
        technical_claims = self._extract_technical_claims(response)
        source_texts = " ".join([c.get("text", "") for c in chunks])

        unfounded_claims = 0
        for claim in technical_claims:
            if claim not in source_texts and claim.lower() not in source_texts.lower():
                unfounded_claims += 1

        if technical_claims:
            risk = unfounded_claims / len(technical_claims)

        # Penalize if no sources cited
        if not any(c.get("source") in response for c in chunks):
            risk = min(1.0, risk + 0.2)

        return min(1.0, risk)

    def _score_completeness(self, response: str, query: str) -> float:
        """Score if response fully answers the query.

        Returns: 0-1 score (higher = more complete)
        """
        response_len = len(response.split())
        query_words = set(query.lower().split())

        # Response should be substantial (>50 words)
        if response_len < 50:
            return 0.3

        # Check if response addresses query keywords
        response_lower = response.lower()
        matched_keywords = sum(1 for word in query_words if word in response_lower)
        keyword_match_ratio = matched_keywords / len(query_words) if query_words else 0.0

        # Combine length and keyword matching
        completeness = (min(1.0, response_len / 200) * 0.6) + (keyword_match_ratio * 0.4)

        return min(1.0, completeness)

    def _count_uncertainty_markers(self, response: str) -> int:
        """Count uncertainty markers in response."""
        matches = self.uncertainty_pattern.findall(response)
        return len(matches)

    @staticmethod
    def _extract_technical_claims(response: str) -> List[str]:
        """Extract technical claims (code blocks, commands, etc)."""
        # Find code blocks and shell commands
        claims = []

        # Find things in backticks or code blocks
        code_pattern = r"`([^`]+)`"
        matches = re.findall(code_pattern, response)
        claims.extend(matches)

        # Find sentences with technical terms
        technical_pattern = r"(?:use|run|execute|type|enter|command|code):\s*([^.!?]+[.!?])"
        matches = re.findall(technical_pattern, response, re.IGNORECASE)
        claims.extend(matches)

        return claims

    def confidence_level(self, confidence: float) -> str:
        """Convert confidence score to level."""
        if confidence >= 0.85:
            return "high"
        elif confidence >= 0.65:
            return "medium"
        elif confidence >= 0.40:
            return "low"
        else:
            return "very_low"
