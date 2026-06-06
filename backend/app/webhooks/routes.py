"""Webhook management endpoints."""

from fastapi import APIRouter, HTTPException, Depends
import logging
from backend.app.webhooks.notifications import webhook_manager, AlertNotification
from backend.app.auth import require_auth
from backend.app.models.user import user_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])

@router.post("/register")
async def register_webhook(
    name: str,
    webhook_type: str,  # 'slack', 'email'
    config: dict,
    admin_key: str = Depends(require_auth)
):
    """Register a new webhook (admin only)."""
    admin = user_manager.get_user_by_api_key(admin_key)
    if not admin or admin.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    if webhook_type not in ['slack', 'email', 'custom']:
        raise HTTPException(status_code=400, detail="Invalid webhook type")

    try:
        webhook_manager.register_webhook(name, webhook_type, config)
        return {
            "message": "Webhook registered successfully",
            "webhook": {
                "name": name,
                "type": webhook_type
            }
        }
    except Exception as e:
        logger.error(f"Error registering webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_webhooks(admin_key: str = Depends(require_auth)):
    """List all webhooks (admin only)."""
    admin = user_manager.get_user_by_api_key(admin_key)
    if not admin or admin.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return {
        "webhooks": webhook_manager.get_webhook_list()
    }

@router.post("/test/{webhook_name}")
async def test_webhook(
    webhook_name: str,
    admin_key: str = Depends(require_auth)
):
    """Send a test alert to a webhook (admin only)."""
    admin = user_manager.get_user_by_api_key(admin_key)
    if not admin or admin.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        test_notification = AlertNotification(
            alert_name="Test Alert",
            alert_type="test",
            message="This is a test notification from the RAG system",
            severity="info",
            metric_value=1.0
        )

        import asyncio
        asyncio.create_task(webhook_manager.send_alert(test_notification, [webhook_name]))

        return {
            "message": "Test alert sent successfully",
            "webhook": webhook_name
        }
    except Exception as e:
        logger.error(f"Error sending test alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{webhook_name}")
async def delete_webhook(
    webhook_name: str,
    admin_key: str = Depends(require_auth)
):
    """Delete a webhook (admin only)."""
    admin = user_manager.get_user_by_api_key(admin_key)
    if not admin or admin.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    if webhook_name not in webhook_manager.webhooks:
        raise HTTPException(status_code=404, detail="Webhook not found")

    del webhook_manager.webhooks[webhook_name]
    logger.info(f"Webhook deleted: {webhook_name}")

    return {
        "message": "Webhook deleted successfully",
        "webhook": webhook_name
    }
