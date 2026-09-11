"""
Push service module for KalaCart notifications.

Exports:
- send_enquiry_notification
- send_enquiry_accepted_notification
- send_product_published_notification
"""

import logging
from typing import Any, Dict, List, Optional

from app.services.fcm_service import (
    async_send_enquiry_accepted_notification,
    async_send_enquiry_notification,
    async_send_product_published_notification,
    send_enquiry_accepted_notification,
    send_enquiry_notification,
    send_enquiry_notification_legacy,
    send_product_published_notification,
)

logger = logging.getLogger(__name__)

__all__ = [
    "send_enquiry_notification",
    "send_enquiry_notification_legacy",
    "send_product_published_notification",
    "send_enquiry_accepted_notification",
    "async_send_enquiry_notification",
    "async_send_product_published_notification",
    "async_send_enquiry_accepted_notification",
]
