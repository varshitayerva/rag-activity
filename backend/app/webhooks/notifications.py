"""Webhook and notification system for alerts."""

import os
import asyncio
import httpx
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class AlertNotification:
    """Alert notification to send via webhooks."""

    def __init__(self, alert_name: str, alert_type: str, message: str,
                 severity: str, metric_value: float = None):
        self.alert_name = alert_name
        self.alert_type = alert_type  # 'error_rate', 'latency', etc.
        self.message = message
        self.severity = severity  # 'info', 'warning', 'critical'
        self.metric_value = metric_value
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'alert_name': self.alert_name,
            'alert_type': self.alert_type,
            'message': self.message,
            'severity': self.severity,
            'metric_value': self.metric_value,
            'timestamp': self.timestamp.isoformat(),
        }


class SlackNotifier:
    """Send alerts to Slack via webhook."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send(self, notification: AlertNotification) -> bool:
        """Send alert to Slack."""
        # Determine color based on severity
        color_map = {
            'info': '#36a64f',      # Green
            'warning': '#ff9900',   # Orange
            'critical': '#ff0000',  # Red
        }

        message = {
            "attachments": [
                {
                    "color": color_map.get(notification.severity, '#36a64f'),
                    "title": f"🚨 {notification.alert_name}",
                    "text": notification.message,
                    "fields": [
                        {
                            "title": "Type",
                            "value": notification.alert_type,
                            "short": True
                        },
                        {
                            "title": "Severity",
                            "value": notification.severity.upper(),
                            "short": True
                        },
                        {
                            "title": "Timestamp",
                            "value": notification.timestamp.isoformat(),
                            "short": False
                        }
                    ],
                    "footer": "RAG System Monitoring",
                    "ts": int(notification.timestamp.timestamp())
                }
            ]
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.webhook_url, json=message, timeout=10)
                success = response.status_code == 200
                logger.info(f"Slack notification sent: {notification.alert_name} ({response.status_code})")
                return success
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False


class EmailNotifier:
    """Send alerts via email using SMTP."""

    def __init__(self, sender_email: str, sender_password: str, smtp_server: str = "smtp.gmail.com"):
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.smtp_server = smtp_server

    async def send(self, notification: AlertNotification, recipient_email: str) -> bool:
        """Send alert email."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            # Create email
            message = MIMEMultipart()
            message["From"] = self.sender_email
            message["To"] = recipient_email
            message["Subject"] = f"[{notification.severity.upper()}] {notification.alert_name}"

            # Email body
            body = f"""
Alert: {notification.alert_name}
Type: {notification.alert_type}
Severity: {notification.severity.upper()}
Message: {notification.message}
Metric Value: {notification.metric_value}
Timestamp: {notification.timestamp.isoformat()}

---
RAG System Monitoring
            """

            message.attach(MIMEText(body, "plain"))

            # Send email (non-blocking via asyncio)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_email, message, recipient_email)

            logger.info(f"Email notification sent to {recipient_email}: {notification.alert_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False

    def _send_email(self, message, recipient_email):
        """Send email synchronously."""
        try:
            import smtplib
            server = smtplib.SMTP_SSL(self.smtp_server, 465)
            server.login(self.sender_email, self.sender_password)
            server.send_message(message)
            server.quit()
        except Exception as e:
            logger.error(f"SMTP error: {e}")


class WebhookManager:
    """Manage webhooks for alerts."""

    def __init__(self):
        self.webhooks: Dict[str, Dict[str, Any]] = {}
        self.slack_notifier: Optional[SlackNotifier] = None
        self.email_notifier: Optional[EmailNotifier] = None
        self._init_webhooks()

    def _init_webhooks(self):
        """Initialize webhooks from environment."""
        # Slack webhook
        slack_url = os.getenv('SLACK_WEBHOOK_URL')
        if slack_url:
            self.slack_notifier = SlackNotifier(slack_url)
            logger.info("Slack webhook initialized")

        # Email webhook
        email_user = os.getenv('EMAIL_SENDER')
        email_pass = os.getenv('EMAIL_PASSWORD')
        if email_user and email_pass:
            self.email_notifier = EmailNotifier(email_user, email_pass)
            logger.info("Email notifier initialized")

    def register_webhook(self, name: str, webhook_type: str, config: Dict[str, Any]):
        """Register a new webhook."""
        self.webhooks[name] = {
            'type': webhook_type,  # 'slack', 'email', 'custom'
            'config': config,
            'created_at': datetime.utcnow().isoformat(),
            'active': True,
        }
        logger.info(f"Webhook registered: {name} ({webhook_type})")

    async def send_alert(self, notification: AlertNotification, webhook_names: List[str] = None):
        """Send alert to all or specific webhooks."""
        webhooks_to_use = webhook_names if webhook_names else list(self.webhooks.keys())

        tasks = []

        for webhook_name in webhooks_to_use:
            if webhook_name not in self.webhooks:
                logger.warning(f"Webhook not found: {webhook_name}")
                continue

            webhook = self.webhooks[webhook_name]
            if not webhook['active']:
                continue

            if webhook['type'] == 'slack' and self.slack_notifier:
                tasks.append(self.slack_notifier.send(notification))
            elif webhook['type'] == 'email' and self.email_notifier:
                recipient = webhook['config'].get('recipient_email')
                if recipient:
                    tasks.append(self.email_notifier.send(notification, recipient))

        if tasks:
            await asyncio.gather(*tasks)

    def get_webhook_list(self) -> List[Dict[str, Any]]:
        """Get list of registered webhooks."""
        return [
            {
                'name': name,
                **webhook
            }
            for name, webhook in self.webhooks.items()
        ]


# Global instance
webhook_manager = WebhookManager()
