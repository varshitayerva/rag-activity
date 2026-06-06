"""Feedback and confidence score API routes."""

from fastapi import APIRouter, Form, HTTPException, Depends
from typing import Optional
import logging
from backend.app.database.postgres import db_client
from backend.app.auth import require_auth

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["feedback"])


@router.post("/feedback")
async def submit_feedback(
    query: str = Form(...),
    rating: int = Form(...),
    feedback_text: Optional[str] = Form(None),
    confidence_score: Optional[float] = Form(None),
    answer: Optional[str] = Form(None),
    chunks_used: Optional[str] = Form(None),
    api_key: str = Depends(require_auth)
) -> dict:
    """Submit user feedback on search results.

    Args:
        query: The search query
        rating: User rating (-1=thumbs down, 0=neutral, 1=thumbs up)
        feedback_text: Optional feedback comment
        confidence_score: Confidence score of the answer
        answer: The generated answer
        chunks_used: JSON string of chunk IDs used
    """
    if rating not in [-1, 0, 1]:
        raise HTTPException(status_code=400, detail="Rating must be -1, 0, or 1")

    try:
        feedback_id = db_client.add_feedback(
            query=query,
            answer=answer,
            confidence_score=confidence_score,
            rating=rating,
            feedback_text=feedback_text,
            chunks_used=chunks_used
        )

        if not feedback_id:
            raise HTTPException(status_code=500, detail="Failed to save feedback")

        return {
            "status": "success",
            "feedback_id": feedback_id,
            "message": "Thank you for your feedback!"
        }

    except Exception as e:
        logger.error(f"Feedback submission error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save feedback")


@router.get("/admin/feedback-analytics")
async def get_feedback_analytics(
    days: int = 30,
    api_key: str = Depends(require_auth)
) -> dict:
    """Get feedback analytics (admin only).

    Args:
        days: Number of days to analyze (default 30)
    """
    try:
        analytics = db_client.get_feedback_analytics(days=days)
        return {
            "status": "success",
            "data": analytics
        }
    except Exception as e:
        logger.error(f"Analytics retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")


@router.get("/admin/low-confidence-queries")
async def get_low_confidence_queries(
    threshold: float = 0.4,
    limit: int = 20,
    api_key: str = Depends(require_auth)
) -> dict:
    """Get queries with low confidence scores for manual review.

    Args:
        threshold: Confidence threshold (default 0.4)
        limit: Maximum results to return (default 20)
    """
    try:
        queries = db_client.get_low_confidence_queries(
            threshold=threshold,
            limit=limit
        )
        return {
            "status": "success",
            "threshold": threshold,
            "count": len(queries),
            "queries": queries
        }
    except Exception as e:
        logger.error(f"Low confidence queries error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve queries")
