"""
Notification service alias — re-exports fcm_service for compatibility.

Marketplace.py attempts both app.services.fcm_service and app.services.notification_service.
This module ensures both import paths work.
"""

from app.services.fcm_service import (  # noqa: F401
    async_send_enquiry_accepted_notification,
    async_send_enquiry_notification,
    async_send_product_published_notification,
    send_enquiry_accepted_notification,
    send_enquiry_notification,
    send_enquiry_notification_legacy,
    send_product_published_notification,
)

__all__ = [
    "send_enquiry_notification",
    "send_enquiry_notification_legacy",
    "send_product_published_notification",
    "send_enquiry_accepted_notification",
    "async_send_enquiry_notification",
    "async_send_product_published_notification",
    "async_send_enquiry_accepted_notification",
]
