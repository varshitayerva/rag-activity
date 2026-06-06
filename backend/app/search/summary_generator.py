"""Generate AI summaries of documents for hierarchical indexing."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DocumentSummaryGenerator:
    """Generate summaries using Groq LLM."""

    @staticmethod
    def generate_summary(text: str, max_length: int = 200) -> Optional[str]:
        """
        Generate a concise summary of document text.

        Args:
            text: Document text (first 5,000 characters)
            max_length: Maximum summary length in words

        Returns:
            Summary string or None if generation fails
        """
        if not text or len(text.strip()) < 100:
            logger.warning("Text too short to summarize")
            return None

        try:
            # Import here to avoid circular imports
            from backend.app.generation.service import client as groq_client

            # Truncate to first 5,000 chars to keep API cost low
            truncated = text[:5000]

            message = groq_client.messages.create(
                model="mixtral-8x7b-32768",
                max_tokens=150,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Summarize the following document in 2-3 sentences.
Focus on the main topic and key points.

Document:
{truncated}

Summary:"""
                    }
                ]
            )

            summary = message.content[0].text.strip()
            logger.info(f"Generated summary: {summary[:50]}...")
            return summary

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return None

    @staticmethod
    def extract_key_topics(text: str) -> str:
        """
        Extract key topics from document (simple approach).

        Args:
            text: Document text

        Returns:
            Comma-separated topics
        """
        # Simple keyword extraction (replace with NLP if needed)
        common_topics = [
            'policy', 'procedure', 'guidelines', 'rules', 'requirements',
            'benefits', 'leave', 'vacation', 'sick', 'emergency',
            'payroll', 'salary', 'bonus', 'compensation',
            'health', 'insurance', 'medical', 'dental', 'vision',
            'training', 'development', 'onboarding', 'course',
            'performance', 'review', 'evaluation', 'goals', 'kpi'
        ]

        text_lower = text.lower()
        found_topics = [t for t in common_topics if t in text_lower]

        return ", ".join(found_topics[:5]) if found_topics else "general"
