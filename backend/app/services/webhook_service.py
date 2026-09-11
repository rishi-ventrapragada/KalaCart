"""
Webhook Event Dispatching & Signature Engine for KalaCart Partner Ecosystem.
"""

import hashlib
import hmac
import json
import logging
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)

# In-memory webhook subscriptions & delivery records
_WEBHOOKS_STORE: Dict[str, Dict[str, Any]] = {
    "wh-default-001": {
        "id": "wh-default-001",
        "target_url": "https://partner-erp.craftbazaar.in/webhooks/kalacart",
        "secret_token": "whsec_live_99887766554433221100aabbcc",
        "events": ["order.created", "order.status_changed", "rfq.received", "payment.escrow_settled"],
        "is_active": True,
        "failure_count": 0,
        "last_triggered_at": "2026-09-06T18:30:00Z",
        "created_at": "2026-09-01T00:00:00Z"
    }
}

_WEBHOOK_DELIVERIES: List[Dict[str, Any]] = [
    {
        "id": "del-001",
        "webhook_id": "wh-default-001",
        "event_type": "order.created",
        "payload": {
            "order_id": "ord-2026-8812",
            "amount": 4200.0,
            "currency": "INR",
            "buyer_name": "FabIndia Sourcing"
        },
        "response_status": 200,
        "delivery_status": "success",
        "signature": "sha256=1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d",
        "delivered_at": "2026-09-06T18:30:01Z"
    }
]


def register_webhook(target_url: str, events: List[str]) -> Dict[str, Any]:
    """Registers a new partner webhook endpoint with auto-generated secret."""
    webhook_id = f"wh-{secrets.token_hex(6)}"
    secret = f"whsec_live_{secrets.token_hex(16)}"
    record = {
        "id": webhook_id,
        "target_url": target_url,
        "secret_token": secret,
        "events": events,
        "is_active": True,
        "failure_count": 0,
        "last_triggered_at": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    _WEBHOOKS_STORE[webhook_id] = record
    return record


def list_webhooks() -> List[Dict[str, Any]]:
    """Returns active webhook endpoints."""
    return list(_WEBHOOKS_STORE.values())


def delete_webhook(webhook_id: str) -> bool:
    """Removes a registered webhook."""
    if webhook_id in _WEBHOOKS_STORE:
        del _WEBHOOKS_STORE[webhook_id]
        return True
    return False


def sign_webhook_payload(secret: str, payload_bytes: bytes) -> str:
    """Computes HMAC-SHA256 signature for webhook payload."""
    sig = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


async def trigger_webhook_event(
    event_type: str,
    payload: Dict[str, Any],
    specific_webhook_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Dispatches event payload to all subscribed endpoints with X-KalaCart-Signature.
    """
    results = []
    targets = [w for w in _WEBHOOKS_STORE.values() if w["is_active"]]
    if specific_webhook_id:
        targets = [w for w in targets if w["id"] == specific_webhook_id]

    payload_json = json.dumps(payload, sort_keys=True).encode("utf-8")
    
    for hook in targets:
        if event_type not in hook.get("events", []) and "*:*" not in hook.get("events", []):
            continue

        signature = sign_webhook_payload(hook["secret_token"], payload_json)
        delivery_id = f"del-{secrets.token_hex(6)}"
        
        delivery_record = {
            "id": delivery_id,
            "webhook_id": hook["id"],
            "event_type": event_type,
            "payload": payload,
            "response_status": 200,  # Simulated mock delivery in sandbox
            "delivery_status": "success",
            "signature": signature,
            "delivered_at": datetime.now(timezone.utc).isoformat()
        }

        # Update last triggered
        hook["last_triggered_at"] = delivery_record["delivered_at"]
        _WEBHOOK_DELIVERIES.insert(0, delivery_record)
        results.append(delivery_record)

    return results


def get_webhook_deliveries(webhook_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves delivery audit history."""
    if webhook_id:
        return [d for d in _WEBHOOK_DELIVERIES if d["webhook_id"] == webhook_id]
    return _WEBHOOK_DELIVERIES[:50]
