"""Hallucination control and validation service."""

import re
import logging
from typing import List, Dict, Any, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


class HallucinationValidator:
    """Validates LLM responses against source documents to detect hallucinations."""

    FORBIDDEN_PATTERNS = [
        r"\bI believe\b",
        r"\bit is commonly known\b",
        r"\baccording to my training\b",
        r"\bfrom my knowledge\b",
        r"\bin general\b",
        r"\bmost experts agree\b",
        r"\bas far as I know\b",
    ]

    def __init__(self):
        self.forbidden_phrases = self.FORBIDDEN_PATTERNS

    def extract_claims(self, answer: str) -> List[Dict[str, Any]]:
        """Extract individual claims from answer text."""
        sentences = re.split(r'[.!?]+', answer)
        claims = []

        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if len(sentence) > 10:
                claims.append({
                    'text': sentence,
                    'index': i,
                    'has_citation': '[' in sentence and ']' in sentence,
                    'length': len(sentence.split())
                })

        return claims

    def validate_citations(self, answer: str, source_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate that claims in answer are properly cited."""
        claims = self.extract_claims(answer)
        source_texts = {str(i): chunk.get('text', '').lower() for i, chunk in enumerate(source_chunks)}

        validated_claims = []
        uncited_claims = []

        for claim in claims:
            claim_text = claim['text'].lower()

            citation_match = re.search(r'\[(?:Source|Chunk)?:?\s*(\w+|\d+)\]', claim['text'])
            if citation_match:
                chunk_ref = citation_match.group(1)
                is_cited = any(chunk_ref in str(source_chunks[i].get('chunk_id', ''))
                              for i in range(len(source_chunks)))
            else:
                is_cited = False

            if not is_cited and len(claim['text']) > 20:
                uncited_claims.append(claim)
                validated_claims.append({
                    **claim,
                    'confidence': 'LOW',
                    'status': 'UNCITED',
                    'risk': 'HIGH'
                })
            else:
                validated_claims.append({
                    **claim,
                    'confidence': 'HIGH',
                    'status': 'CITED',
                    'risk': 'LOW'
                })

        return {
            'total_claims': len(claims),
            'cited_claims': len([c for c in validated_claims if c['status'] == 'CITED']),
            'uncited_claims': len(uncited_claims),
            'citation_rate': len([c for c in validated_claims if c['status'] == 'CITED']) / max(len(claims), 1),
            'claims': validated_claims
        }

    def check_forbidden_phrases(self, answer: str) -> List[Dict[str, Any]]:
        """Check for forbidden phrases that indicate uncertainty or hallucination."""
        violations = []

        for pattern in self.FORBIDDEN_PATTERNS:
            matches = re.finditer(pattern, answer, re.IGNORECASE)
            for match in matches:
                start = max(0, match.start() - 50)
                end = min(len(answer), match.end() + 50)
                context = answer[start:end]

                violations.append({
                    'phrase': match.group(),
                    'context': context.strip(),
                    'severity': 'HIGH'
                })

        return violations

    def semantic_coherence_check(self, source_chunks: List[Dict[str, Any]]) -> Tuple[bool, float]:
        """Check if retrieved chunks are semantically coherent (about same topic)."""
        if len(source_chunks) < 2:
            return True, 1.0

        scores = [chunk.get('vector_score', chunk.get('score', 0)) for chunk in source_chunks]

        if not scores:
            return True, 0.5

        avg_score = sum(scores) / len(scores)
        std_dev = (sum((x - avg_score) ** 2 for x in scores) / len(scores)) ** 0.5

        coherence_score = max(0, 1 - (std_dev / avg_score if avg_score > 0 else 0))
        is_coherent = coherence_score > 0.6

        return is_coherent, coherence_score

    def calculate_hallucination_risk(
        self,
        answer: str,
        source_chunks: List[Dict[str, Any]],
        confidence_score: float
    ) -> Dict[str, Any]:
        """Calculate overall hallucination risk score (0-1, higher = more risky)."""

        forbidden_violations = self.check_forbidden_phrases(answer)
        citation_validation = self.validate_citations(answer, source_chunks)
        is_coherent, coherence_score = self.semantic_coherence_check(source_chunks)

        risk_factors = {
            'low_confidence': max(0, 0.6 - confidence_score) / 0.6,
            'uncited_claims': citation_validation['uncited_claims'] / max(citation_validation['total_claims'], 1),
            'forbidden_phrases': min(len(forbidden_violations) * 0.2, 1.0),
            'incoherent_sources': 0 if is_coherent else 0.3,
        }

        total_risk = sum(risk_factors.values()) / len(risk_factors)
        total_risk = min(max(total_risk, 0), 1.0)

        return {
            'hallucination_risk': total_risk,
            'risk_level': 'HIGH' if total_risk > 0.6 else 'MEDIUM' if total_risk > 0.3 else 'LOW',
            'risk_factors': risk_factors,
            'forbidden_violations': forbidden_violations,
            'citation_validation': citation_validation,
            'source_coherence': {
                'is_coherent': is_coherent,
                'score': coherence_score
            },
            'recommendation': self._get_recommendation(total_risk, citation_validation['citation_rate'])
        }

    def _get_recommendation(self, risk_score: float, citation_rate: float) -> str:
        """Generate recommendation based on hallucination risk."""
        if risk_score > 0.6:
            return "HIGH RISK: Answer contains unverified information. Consider asking for a more specific query."
        elif risk_score > 0.3 and citation_rate < 0.7:
            return "MEDIUM RISK: Some claims lack proper citations. Review sources carefully."
        else:
            return "LOW RISK: Answer is well-grounded in retrieved documents."

    def sanitize_answer(self, answer: str, validation_result: Dict[str, Any]) -> str:
        """Remove or flag uncited claims in answer."""
        if validation_result['hallucination_risk'] < 0.4:
            return answer

        claims = validation_result['citation_validation']['claims']
        modified_answer = answer

        for claim in claims:
            if claim['status'] == 'UNCITED' and claim['risk'] == 'HIGH':
                sanitized = f"[UNCERTAIN: {claim['text']}]"
                modified_answer = modified_answer.replace(claim['text'], sanitized, 1)

        return modified_answer
