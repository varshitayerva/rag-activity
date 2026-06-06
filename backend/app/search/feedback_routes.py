"""Feedback and confidence score API routes."""

from fastapi import APIRouter, Form, HTTPException, Depends
from typing import Optional
import logging
from backend.app.database.postgres import db_client
from backend.app.auth import require_auth, require_admin_auth

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
    logger.info(f"Feedback submission received: query={query[:50]}, rating={rating}, confidence={confidence_score}")

    if rating not in [-1, 0, 1]:
        logger.error(f"Invalid rating: {rating}")
        raise HTTPException(status_code=400, detail="Rating must be -1, 0, or 1")

    try:
        logger.info(f"Attempting to save feedback to database...")
        feedback_id = db_client.add_feedback(
            query=query,
            answer=answer,
            confidence_score=confidence_score,
            rating=rating,
            feedback_text=feedback_text,
            chunks_used=chunks_used
        )

        if not feedback_id:
            logger.error(f"Failed to save feedback - no ID returned")
            raise HTTPException(status_code=500, detail="Failed to save feedback")

        logger.info(f"Feedback saved successfully with ID: {feedback_id}")
        return {
            "status": "success",
            "feedback_id": feedback_id,
            "message": "Thank you for your feedback!"
        }

    except Exception as e:
        logger.error(f"Feedback submission error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save feedback")


@router.get("/admin/feedback-analytics")
async def get_feedback_analytics(
    days: int = 30,
    api_key: str = Depends(require_admin_auth)
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
    api_key: str = Depends(require_admin_auth)
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


@router.get("/admin/all-feedback")
async def get_all_feedback(
    limit: int = 100,
    offset: int = 0,
    days: int = 30,
    api_key: str = Depends(require_admin_auth)
) -> dict:
    """Get all feedback submissions (admin only).

    Args:
        limit: Number of feedback entries per page (default 100)
        offset: Pagination offset (default 0)
        days: Number of days to look back (default 30)
    """
    try:
        logger.info(f"Fetching feedback: limit={limit}, offset={offset}, days={days}")
        result = db_client.get_all_feedback(limit=limit, offset=offset, days=days)
        logger.info(f"Feedback query result: total={result.get('total')}, count={len(result.get('feedback', []))}")
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        logger.error(f"Failed to retrieve feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve feedback")


@router.get("/admin/feedback-debug")
async def debug_feedback(
    api_key: str = Depends(require_admin_auth)
) -> dict:
    """Debug endpoint to check feedback database status (admin only)."""
    try:
        from backend.app.database.postgres import db_client as db

        # Check total feedback count (all time)
        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Total count
            cursor.execute("SELECT COUNT(*) as total FROM query_feedback")
            total = cursor.fetchone()[0]

            # Count by rating
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as positive,
                    SUM(CASE WHEN rating = -1 THEN 1 ELSE 0 END) as negative,
                    SUM(CASE WHEN rating = 0 THEN 1 ELSE 0 END) as neutral
                FROM query_feedback
            """)
            counts = cursor.fetchone()

            # Sample feedback
            cursor.execute("""
                SELECT id, query, rating, confidence_score, created_at
                FROM query_feedback
                ORDER BY created_at DESC
                LIMIT 5
            """)
            samples = cursor.fetchall()

            cursor.close()

        return {
            "status": "success",
            "debug_info": {
                "total_feedback_all_time": total,
                "ratings": {
                    "positive_thumbs_up": counts[0] or 0,
                    "negative_thumbs_down": counts[1] or 0,
                    "neutral": counts[2] or 0
                },
                "recent_samples": [
                    {
                        "id": s[0],
                        "query": s[1],
                        "rating": s[2],
                        "confidence_score": s[3],
                        "created_at": str(s[4])
                    } for s in samples
                ]
            }
        }
    except Exception as e:
        logger.error(f"Debug endpoint error: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }
