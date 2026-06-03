"""Feedback system for answer quality improvement."""

import uuid
from datetime import datetime
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class Feedback:
    """Feedback on an answer."""

    def __init__(self, query: str, answer: str, user_id: str, rating: int,
                 comment: str = None, sources: List[str] = None):
        self.feedback_id = str(uuid.uuid4())
        self.query = query
        self.answer = answer
        self.user_id = user_id
        self.rating = rating  # 1-5 stars
        self.comment = comment
        self.sources = sources or []
        self.created_at = datetime.utcnow()
        self.helpful = None  # Was this feedback helpful?

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'feedback_id': self.feedback_id,
            'query': self.query,
            'answer': self.answer[:200] + "..." if len(self.answer) > 200 else self.answer,
            'user_id': self.user_id,
            'rating': self.rating,
            'comment': self.comment,
            'sources': self.sources,
            'created_at': self.created_at.isoformat(),
            'helpful': self.helpful,
        }


class FeedbackManager:
    """Manage feedback collection and analysis."""

    def __init__(self):
        self.feedbacks: List[Feedback] = []
        self.ratings_by_query: Dict[str, List[int]] = {}

    def submit_feedback(self, query: str, answer: str, user_id: str, rating: int,
                       comment: str = None, sources: List[str] = None) -> Feedback:
        """Submit feedback on an answer."""
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        feedback = Feedback(
            query=query,
            answer=answer,
            user_id=user_id,
            rating=rating,
            comment=comment,
            sources=sources
        )

        self.feedbacks.append(feedback)

        # Track ratings by query
        if query not in self.ratings_by_query:
            self.ratings_by_query[query] = []
        self.ratings_by_query[query].append(rating)

        logger.info(f"Feedback recorded: {query[:50]}... - Rating: {rating}/5")
        return feedback

    def get_feedback_stats(self, query: str = None) -> Dict[str, Any]:
        """Get feedback statistics."""
        if query:
            ratings = self.ratings_by_query.get(query, [])
        else:
            ratings = [f.rating for f in self.feedbacks]

        if not ratings:
            return {
                'total_feedback': 0,
                'avg_rating': 0,
                'distribution': {}
            }

        total = len(ratings)
        avg = sum(ratings) / total
        distribution = {i: ratings.count(i) for i in range(1, 6)}

        return {
            'total_feedback': total,
            'avg_rating': round(avg, 2),
            'distribution': distribution,
            'quality_score': 'Good' if avg >= 4 else 'Fair' if avg >= 3 else 'Poor',
        }

    def get_low_rated_answers(self, threshold: int = 2) -> List[Feedback]:
        """Get answers with low ratings for improvement."""
        return [f for f in self.feedbacks if f.rating <= threshold]

    def get_user_feedback(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all feedback from a user."""
        return [f.to_dict() for f in self.feedbacks if f.user_id == user_id]

    def analyze_feedback_trends(self) -> Dict[str, Any]:
        """Analyze feedback trends."""
        if not self.feedbacks:
            return {'status': 'No feedback yet'}

        avg_rating = sum(f.rating for f in self.feedbacks) / len(self.feedbacks)
        poor_feedback = len([f for f in self.feedbacks if f.rating <= 2])
        good_feedback = len([f for f in self.feedbacks if f.rating >= 4])

        top_queries = sorted(
            self.ratings_by_query.items(),
            key=lambda x: (sum(x[1]) / len(x[1])),
            reverse=True
        )[:5]

        return {
            'total_feedback_count': len(self.feedbacks),
            'overall_avg_rating': round(avg_rating, 2),
            'poor_answers': poor_feedback,
            'good_answers': good_feedback,
            'top_rated_queries': [q for q, _ in top_queries],
            'needs_improvement': poor_feedback > good_feedback,
        }


# Global instance
feedback_manager = FeedbackManager()
