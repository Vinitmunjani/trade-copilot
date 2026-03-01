"""Notification service: webhook + optional SendGrid email notifications.

This service is intentionally lightweight and configurable via environment
variables. It sends a POST to `NOTIFICATION_WEBHOOK_URL` when set, and will
also send an email via SendGrid when `SENDGRID_API_KEY`, `NOTIFICATION_EMAIL_FROM`,
and `NOTIFICATION_EMAIL_TO` are configured.
"""
import asyncio
import logging
from typing import Any, Dict

import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self._settings = None

    def _settings_now(self):
        # Load settings on demand so env changes are respected in tests
        return get_settings()

    async def notify_trade_event(self, user_id: str, event_type: str, trade: Dict[str, Any]) -> None:
        settings = self._settings_now()
        tasks = []

        webhook = settings.NOTIFICATION_WEBHOOK_URL
        if webhook:
            tasks.append(self._send_webhook(webhook, {"user_id": user_id, "event": event_type, "trade": trade}))

        if settings.SENDGRID_API_KEY and settings.NOTIFICATION_EMAIL_FROM and settings.NOTIFICATION_EMAIL_TO:
            tasks.append(self._send_email_async(settings, user_id, event_type, trade))

        if not tasks:
            return

        # Run tasks concurrently, but don't let failures raise into caller
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, Exception):
                logger.error(f"Notification task error: {r}")

    async def _send_webhook(self, url: str, payload: Dict[str, Any]) -> None:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
        except Exception as e:
            logger.error(f"Webhook notification failed: {e}")

    async def _send_email_async(self, settings, user_id: str, event_type: str, trade: Dict[str, Any]) -> None:
        # SendGrid client is synchronous; run it in a thread to avoid blocking
        await asyncio.to_thread(self._send_email_sync, settings, user_id, event_type, trade)

    def _send_email_sync(self, settings, user_id: str, event_type: str, trade: Dict[str, Any]) -> None:
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail

            subject = f"Trade {event_type} for user {user_id}"
            body = f"Event: {event_type}\nUser: {user_id}\n\n{trade}"

            message = Mail(
                from_email=settings.NOTIFICATION_EMAIL_FROM,
                to_emails=settings.NOTIFICATION_EMAIL_TO,
                subject=subject,
                plain_text_content=body,
            )

            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            sg.send(message)
        except Exception as e:
            logger.error(f"SendGrid notification failed: {e}")


# Global instance
notification_service = NotificationService()
