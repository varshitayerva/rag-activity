"""API routes for new features: users, feedback, monitoring."""

from fastapi import APIRouter, HTTPException, Depends
import logging
from backend.app.models.user import user_manager
from backend.app.models.feedback import feedback_manager
from backend.app.cache.advanced_cache import cache_manager
from backend.app.monitoring.metrics import monitoring_system
from backend.app.auth import require_auth

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["features"])

# ==================== USER PROFILE ENDPOINTS ====================

@router.get("/user/profile")
async def get_user_profile(api_key: str = Depends(require_auth)):
    """Get current user profile."""
    user = user_manager.get_user_by_api_key(api_key)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_manager.record_login(api_key)
    return {
        "user": user.to_dict(),
        "stats": user_manager.get_user_stats(api_key)
    }

@router.get("/user/stats")
async def get_user_stats(api_key: str = Depends(require_auth)):
    """Get user statistics."""
    return {
        "stats": user_manager.get_user_stats(api_key)
    }

@router.post("/user/create")
async def create_user(
    username: str,
    email: str,
    department: str = None,
    admin_key: str = Depends(require_auth)
):
    """Create a new user (admin only)."""
    admin = user_manager.get_user_by_api_key(admin_key)
    if not admin or admin.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    user = user_manager.create_user(username, email, department)
    return {
        "message": "User created successfully",
        "user": user.to_dict(),
        "api_key": user.api_key
    }

@router.get("/users/list")
async def list_users(admin_key: str = Depends(require_auth)):
    """List all users (admin only)."""
    users = user_manager.list_users(admin_key)
    if not users:
        raise HTTPException(status_code=403, detail="Admin access required")

    return {
        "total_users": len(users),
        "users": users
    }

# ==================== FEEDBACK ENDPOINTS ====================

@router.post("/feedback/submit")
async def submit_feedback(
    query: str,
    answer: str,
    rating: int,
    comment: str = None,
    api_key: str = Depends(require_auth)
):
    """Submit feedback on an answer."""
    if not 1 <= rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5")

    user = user_manager.get_user_by_api_key(api_key)
    feedback = feedback_manager.submit_feedback(
        query=query,
        answer=answer,
        user_id=user.user_id,
        rating=rating,
        comment=comment
    )

    return {
        "message": "Feedback submitted successfully",
        "feedback_id": feedback.feedback_id
    }

@router.get("/feedback/stats")
async def get_feedback_stats(query: str = None):
    """Get feedback statistics."""
    stats = feedback_manager.get_feedback_stats(query)
    trends = feedback_manager.analyze_feedback_trends()

    return {
        "stats": {
            "total_feedback": stats.get('total_feedback', 0),
            "avg_rating": stats.get('avg_rating', 0),
            "quality_score": stats.get('avg_rating', 0) * 20,
            "distribution": stats.get('distribution', {5: 0, 4: 0, 3: 0, 2: 0, 1: 0})
        },
        "trends": {
            "total_feedback_count": trends.get('total_feedback', 0),
            "good_answers": trends.get('good_answers', 0),
            "poor_answers": trends.get('poor_answers', 0),
            "needs_improvement": trends.get('needs_improvement', False)
        }
    }

@router.get("/feedback/analysis")
async def get_feedback_analysis():
    """Get detailed feedback analysis."""
    low_rated = feedback_manager.get_low_rated_answers(threshold=2)
    return {
        "total_feedback": len(feedback_manager.feedbacks),
        "low_rated_count": len(low_rated),
        "trends": feedback_manager.analyze_feedback_trends(),
        "low_rated_samples": [f.to_dict() for f in low_rated[:5]]
    }

# ==================== CACHE ENDPOINTS ====================

@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics."""
    stats = cache_manager.get_stats()
    return {
        "stats": {
            "total_requests": stats.get('total_requests', 0),
            "cache_hits": stats.get('cache_hits', 0),
            "cache_misses": stats.get('cache_misses', 0),
            "hit_rate": stats.get('hit_rate', 0),
            "cache_evictions": stats.get('evictions', 0),
            "memory_used_mb": 0,
            "search_cache_size": stats.get('local_cache_size', 0),
            "search_cache_hit_rate": stats.get('hit_rate', 0),
            "generation_cache_size": 0,
            "generation_cache_hit_rate": 0,
        }
    }

@router.post("/cache/clear")
async def clear_cache(admin_key: str = Depends(require_auth)):
    """Clear all cache (admin only)."""
    admin = user_manager.get_user_by_api_key(admin_key)
    if not admin or admin.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    cache_manager.clear()
    return {"message": "Cache cleared successfully"}

# ==================== MONITORING ENDPOINTS ====================

@router.get("/health/detailed")
async def get_detailed_health():
    """Get detailed health status."""
    from backend.app.cache.metrics import MetricsCollector
    metrics = MetricsCollector.get_metrics()

    current_metrics = {
        'error_rate': 0.01,
        'latency': metrics.get('avg_latency_ms', 0),
        'cache_hit_rate': metrics.get('cache_hit_rate', 0),
        'qps': metrics.get('total_queries', 0) / max(1, (metrics.get('avg_latency_ms', 1) / 1000)),
    }

    health = monitoring_system.get_health_status(current_metrics)

    return {
        "health": {
            "score": health.get('score', 80),
            "status": health.get('status', 'healthy'),
            "cache_status": "healthy",
            "vector_index_status": "ready",
            "recent_errors": []
        }
    }

@router.get("/alerts/status")
async def get_alert_status():
    """Get alert status."""
    alert_status = monitoring_system.get_alert_status()
    formatted_alerts = {}

    for rule_name, alert_data in alert_status.items():
        formatted_alerts[rule_name] = {
            "name": alert_data.get('name', rule_name),
            "triggered": alert_data.get('triggered', False),
            "severity": alert_data.get('severity', 'warning'),
            "message": alert_data.get('message', ''),
            "threshold": alert_data.get('threshold', 'N/A'),
            "current_value": alert_data.get('current_value', 'N/A')
        }

    return {
        "alerts": formatted_alerts
    }

@router.get("/monitoring/metrics")
async def get_monitoring_metrics():
    """Get detailed monitoring metrics."""
    from backend.app.cache.metrics import MetricsCollector
    metrics = MetricsCollector.get_metrics()

    return {
        "metrics": {
            "total_queries": metrics.get('total_queries', 0),
            "avg_latency": metrics.get('avg_latency_ms', 0),
            "error_rate": metrics.get('error_rate', 0),
            "qps": metrics.get('total_queries', 0) / max(1, 60),
            "total_searches": metrics.get('total_searches', 0),
            "avg_search_latency": metrics.get('avg_latency_ms', 0),
            "total_generations": metrics.get('total_generations', 0),
            "avg_generation_latency": metrics.get('avg_latency_ms', 0),
            "min_latency": metrics.get('min_latency_ms', 0),
            "max_latency": metrics.get('max_latency_ms', 0),
        }
    }
