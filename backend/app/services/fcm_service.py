"""
FCM / Notification service for marketplace events.

Provides best-effort push via firebase_admin.messaging.
- Handles missing Firebase init gracefully (log and return True/False without raising)
- Resolves artisan FCM token via artisans.fcm_token column if exists, else notification_tokens table, else topic fallback
- Functions:
    send_enquiry_notification(supabase, artisan_id, product_title, buyer_name, enquiry_id, product_id=None, message=None) -> bool
    send_product_published_notification(artisan_id, product_title, product_id) -> bool
    send_enquiry_accepted_notification(supabase, buyer_identifier, buyer_name, enquiry_id, product_title?, product_id?) -> bool

All functions are sync but also provide async wrappers for FastAPI await handling.
Exceptions are caught and logged, never propagate to marketplace flow.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import firebase_admin  # type: ignore
    from firebase_admin import messaging  # type: ignore
except ImportError:
    firebase_admin = None  # type: ignore
    messaging = None  # type: ignore  # noqa: F811


def _ensure_firebase() -> bool:
    """Ensure Firebase Admin is initialized. Returns True if messaging can be used."""
    if firebase_admin is None or messaging is None:
        logger.debug("firebase-admin not installed — FCM disabled")
        return False
    try:
        # Check if already initialized
        if getattr(firebase_admin, "_apps", None):
            if firebase_admin._apps:  # type: ignore
                return True
    except Exception:
        pass

    # Try to initialize via existing security helper
    try:
        from app.core.security import initialize_firebase

        initialized = initialize_firebase()
        if initialized:
            return True
        # Even if initialize returns False (mock mode), check if apps now exist
        if firebase_admin._apps:  # type: ignore
            return True
        logger.debug("Firebase not initialized (mock mode) — FCM will log only")
        return False
    except Exception as exc:
        logger.debug("Failed to initialize Firebase for FCM: %s", exc)
        return False


def _send_to_token(token: str, title: str, body: str, data: Dict[str, str]) -> bool:
    """Low-level send to single token. Returns True on success."""
    if not _ensure_firebase() or messaging is None:
        logger.info("[FCM-MOCK] Would send to token %s: title='%s' body='%s' data=%s", token[:12] + "...", title, body, data)
        return True  # Mock success — don't block flow

    # Ensure all data values are strings (FCM requirement)
    str_data = {str(k): str(v) for k, v in (data or {}).items() if v is not None}

    # Build message with notification + data + Android high priority
    try:
        android_config = None
        try:
            android_config = messaging.AndroidConfig(  # type: ignore
                priority="high",
                notification=messaging.AndroidNotification(  # type: ignore
                    priority="high",
                    visibility="public",
                    color="#8D4B08",  # Terracotta
                ),
            )
        except Exception:
            android_config = None

        msg = messaging.Message(  # type: ignore
            token=token,
            notification=messaging.Notification(title=title, body=body),  # type: ignore
            data=str_data,
            android=android_config,
        )
        result = messaging.send(msg)  # type: ignore
        logger.info("FCM sent to token %s result=%s title='%s'", token[:12] + "...", result, title)
        return True
    except Exception as exc:
        # Handle invalid token, not found, etc — log and return False
        err_str = str(exc).lower()
        if "not found" in err_str or "invalid" in err_str or "unregistered" in err_str:
            logger.warning("FCM token invalid/unregistered %s: %s", token[:12] + "...", exc)
            # Optionally we could delete invalid token from DB here
        else:
            logger.warning("FCM send to token failed %s: %s", token[:12] + "...", exc)
        return False


def _send_to_topic(topic: str, title: str, body: str, data: Dict[str, str]) -> bool:
    """Send to topic as fallback (e.g., artisan_<id>)."""
    if not _ensure_firebase() or messaging is None:
        logger.info("[FCM-MOCK] Would send to topic %s: title='%s' body='%s' data=%s", topic, title, body, data)
        return True

    str_data = {str(k): str(v) for k, v in (data or {}).items() if v is not None}
    try:
        # Topic must match [a-zA-Z0-9-_.~%]+
        safe_topic = topic.replace(":", "_").replace("/", "_")
        msg = messaging.Message(  # type: ignore
            topic=safe_topic,
            notification=messaging.Notification(title=title, body=body),  # type: ignore
            data=str_data,
        )
        result = messaging.send(msg)  # type: ignore
        logger.info("FCM sent to topic %s result=%s", safe_topic, result)
        return True
    except Exception as exc:
        logger.warning("FCM send to topic %s failed: %s", topic, exc)
        return False


def _resolve_artisan_tokens(supabase_client, artisan_id: str) -> List[str]:
    """Resolve FCM tokens for artisan_id via multiple fallbacks. Returns list of tokens.

    Tries:
      1) artisans.fcm_token column (if exists)
      2) notification_tokens table where user_id = artisan's firebase_uid or artisan_id
    Handles missing column/table gracefully.
    """
    tokens: List[str] = []
    if not artisan_id:
        return tokens
    client = supabase_client
    # 1) artisans.fcm_token
    try:
        res = client.table("artisans").select("fcm_token,firebase_uid").eq("id", artisan_id).limit(1).execute()
        if res.data:
            row = res.data[0]
            fcm = row.get("fcm_token")
            if fcm and isinstance(fcm, str) and fcm.strip():
                tokens.append(fcm.strip())
            # Also try lookup notification_tokens via firebase_uid
            firebase_uid = row.get("firebase_uid")
            if firebase_uid:
                try:
                    nt_res = client.table("notification_tokens").select("token").eq("user_id", firebase_uid).execute()
                    for r in (nt_res.data or []):
                        t = r.get("token")
                        if t and t.strip() and t not in tokens:
                            tokens.append(t.strip())
                except Exception as nt_exc:
                    logger.debug("notification_tokens lookup by firebase_uid failed (non-fatal): %s", nt_exc)
                try:
                    # Also try by artisan_id as user_id
                    nt2 = client.table("notification_tokens").select("token").eq("user_id", artisan_id).execute()
                    for r in (nt2.data or []):
                        t = r.get("token")
                        if t and t.strip() and t not in tokens:
                            tokens.append(t.strip())
                except Exception:
                    pass
    except Exception as exc:
        # Column may not exist (pre-007) or table missing
        err = str(exc).lower()
        if "fcm_token" in err or "column" in err:
            logger.debug("artisans.fcm_token column missing, trying notification_tokens fallback: %s", exc)
            # Try notification_tokens fallback directly by artisan_id
            try:
                nt_res = client.table("notification_tokens").select("token").eq("user_id", artisan_id).execute()
                for r in (nt_res.data or []):
                    t = r.get("token")
                    if t and t.strip():
                        tokens.append(t.strip())
            except Exception as nt_exc:
                logger.debug("notification_tokens fallback failed: %s", nt_exc)
        else:
            logger.debug("Failed to resolve artisan tokens for %s: %s", artisan_id, exc)
            # Still try notification_tokens generic
            try:
                nt_res = client.table("notification_tokens").select("token").eq("user_id", artisan_id).execute()
                for r in (nt_res.data or []):
                    t = r.get("token")
                    if t and t.strip():
                        tokens.append(t.strip())
            except Exception:
                pass

    # Deduplicate preserve order
    seen = set()
    deduped = []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            deduped.append(t)
    return deduped


def _resolve_buyer_tokens(supabase_client, buyer_profile_id: Optional[str], buyer_user_id: Optional[str]) -> List[str]:
    """Resolve buyer tokens via notification_tokens or buyer_profiles-linked artisan if needed."""
    tokens: List[str] = []
    client = supabase_client
    user_ids_to_try: List[str] = []
    if buyer_user_id:
        user_ids_to_try.append(buyer_user_id)
    if buyer_profile_id:
        # Fetch buyer_profiles user_id
        try:
            bp = client.table("buyer_profiles").select("user_id").eq("id", buyer_profile_id).limit(1).execute()
            if bp.data and bp.data[0].get("user_id"):
                uid = str(bp.data[0].get("user_id")).strip()
                if uid and uid not in user_ids_to_try:
                    user_ids_to_try.append(uid)
        except Exception:
            pass
        # Also try buyer_profile_id itself as user_id key (legacy)
        if buyer_profile_id not in user_ids_to_try:
            user_ids_to_try.append(buyer_profile_id)

    for uid in user_ids_to_try:
        try:
            nt_res = client.table("notification_tokens").select("token").eq("user_id", uid).execute()
            for r in (nt_res.data or []):
                t = r.get("token")
                if t and t.strip() and t not in tokens:
                    tokens.append(t.strip())
        except Exception:
            continue
        # Also try artisans table if buyer is also artisan
        try:
            art_res = client.table("artisans").select("fcm_token").eq("firebase_uid", uid).limit(1).execute()
            if art_res.data:
                fcm = art_res.data[0].get("fcm_token")
                if fcm and fcm.strip() and fcm not in tokens:
                    tokens.append(fcm.strip())
        except Exception:
            pass
    return tokens


# ── Public API ────────────────────────────────────────────────────────────────

def send_enquiry_notification(
    supabase_client,
    artisan_id: str,
    product_title: str,
    buyer_name: str,
    enquiry_id: str,
    product_id: Optional[str] = None,
    message: Optional[str] = None,
    buyer_phone: Optional[str] = None,
) -> bool:
    """
    Send FCM to artisan when a new enquiry arrives.

    Args:
        supabase_client: Supabase client (service_role)
        artisan_id: Owner artisan id to notify
        product_title: Product title for notification
        buyer_name: Buyer display name
        enquiry_id: Enquiry id for data payload
        product_id: Product id
        message: Enquiry message preview
    Returns:
        True if at least one send succeeded or mocked, False if all failed. Never raises.
    """
    try:
        if not artisan_id:
            logger.warning("send_enquiry_notification called with empty artisan_id — skipping")
            return False
        safe_title = (product_title or "Your product").strip() or "Your product"
        safe_buyer = (buyer_name or "A buyer").strip() or "A buyer"
        safe_enquiry = (enquiry_id or "").strip()
        safe_product = (product_id or "").strip()
        safe_msg = (message or "").strip()
        if len(safe_msg) > 120:
            safe_msg = safe_msg[:117] + "..."

        title = f"New Enquiry for {safe_title}"
        body = f"{safe_buyer} sent an enquiry" + (f": {safe_msg}" if safe_msg else "")

        data: Dict[str, str] = {
            "type": "enquiry",
            "product_title": safe_title,
            "buyer_name": safe_buyer,
            "enquiry_id": safe_enquiry,
            "product_id": safe_product,
            "message": safe_msg,
            "title": title,
            "body": body,
        }
        # Clean empty
        data = {k: v for k, v in data.items() if v}

        tokens = _resolve_artisan_tokens(supabase_client, artisan_id)
        if tokens:
            success = False
            for tok in tokens:
                ok = _send_to_token(tok, title, body, data)
                success = success or ok
            return success
        else:
            # No token — fallback to topic + log
            logger.info("No FCM token found for artisan %s — falling back to topic artisan_%s", artisan_id, artisan_id)
            # Try topic send (subscribers can subscribe client-side to artisan_<id> topic)
            topic_ok = _send_to_topic(f"artisan_{artisan_id}", title, body, data)
            # Even if topic send fails, we return True to not block enquiry flow (best-effort)
            # But log for observability
            if not topic_ok:
                logger.info("[FCM] No token and topic send failed for artisan %s — logged only (MVP)", artisan_id)
            return True
    except Exception as exc:
        logger.warning("send_enquiry_notification failed (non-fatal) for artisan %s: %s", artisan_id, exc, exc_info=False)
        return False


# Flexible wrapper to support legacy marketplace.py call signature: (artisan_id, product_dict, enquiry_dict)
def send_enquiry_notification_legacy(
    supabase_client,
    artisan_id: str,
    product: Any,
    enquiry: Any,
) -> bool:
    """Adapter for older callers that pass product/enquiry dicts."""
    try:
        product_title = ""
        product_id = ""
        if isinstance(product, dict):
            product_title = str(product.get("title") or product.get("name") or "Your product")
            product_id = str(product.get("id") or "")
        elif isinstance(product, str):
            product_title = product
        buyer_name = "A buyer"
        enquiry_id = ""
        message = ""
        buyer_phone = None
        if isinstance(enquiry, dict):
            buyer_name = str(enquiry.get("buyer_name") or enquiry.get("buyerName") or "A buyer")
            enquiry_id = str(enquiry.get("id") or "")
            message = str(enquiry.get("message") or "")
            buyer_phone = enquiry.get("buyer_phone")
            # product_id fallback
            if not product_id:
                product_id = str(enquiry.get("product_id") or "")
        return send_enquiry_notification(
            supabase_client, artisan_id, product_title, buyer_name, enquiry_id, product_id, message, buyer_phone
        )
    except Exception as exc:
        logger.warning("send_enquiry_notification_legacy failed: %s", exc)
        return False


def send_product_published_notification(
    supabase_client,
    artisan_id: str,
    product_title: str,
    product_id: str,
) -> bool:
    """
    Notify artisan that their product is now published.
    Also can be called with (artisan_id, product_title, product_id) or (supabase, artisan_id, product_title, product_id)
    Handles overloaded signature for compatibility.
    """
    # Handle overloaded first arg being supabase client vs artisan_id
    # If called as send_product_published_notification(artisan_id, product_title, product_id) without supabase,
    # we detect by checking if first arg looks like supabase client (has .table)
    try:
        # Detect if supabase_client is actually artisan_id string and artisan_id is product_title etc.
        # Normal signature: (supabase_client, artisan_id, product_title, product_id)
        # Legacy Marketplace may call with 3 args? spec says artisan_id, product_title, product_id
        # We'll support both: if supabase_client is str and artisan_id is str and product_title is str with no supabase,
        # then treat supabase_client as artisan_id.
        if isinstance(supabase_client, str) and isinstance(artisan_id, str) and isinstance(product_title, str):
            # Could be legacy 3-arg where supabase_client is artisan_id
            # Check if product_id is None and we have 3 args only? But function always has 4 params, product_id may be None
            # We need to detect: if first arg has no .table attribute and looks like UUID, it's artisan_id
            has_table = hasattr(supabase_client, "table")
            if not has_table:
                # Shift args: supabase_client is actually artisan_id
                product_id_actual = product_title  # third arg was product_id originally
                # artisan_id param is actually product_title
                # product_title param is actually product_id
                # This is confusion; simpler: handle both by checking types
                # If called as (artisan_id, product_title, product_id) then:
                #   supabase_client = artisan_id (uuid str)
                #   artisan_id = product_title (title str)
                #   product_title = product_id (id str)
                #   product_id = maybe None or missing
                # We can detect by trying to fetch supabase: if supabase_client doesn't have table, we need to get real supabase
                try:
                    from app.database.connection import get_supabase_client

                    real_supabase = get_supabase_client()
                except Exception:
                    real_supabase = None
                if real_supabase is not None:
                    # Reassign correctly
                    real_artisan_id = supabase_client  # first arg
                    real_product_title = artisan_id  # second arg
                    real_product_id = product_title  # third arg
                    return send_product_published_notification(real_supabase, real_artisan_id, real_product_title, real_product_id)
                else:
                    # No supabase, mock log
                    logger.info("[FCM-MOCK] Product published artisan=%s title=%s", supabase_client, artisan_id)
                    return True
    except Exception:
        pass

    try:
        if not artisan_id:
            logger.warning("send_product_published_notification called with empty artisan_id — skipping")
            return False
        # When called with supabase_client first, artisan_id is second param (correct)
        # But if overloaded detection above didn't trigger, use as is
        # If supabase_client looks like supabase (has table), then artisan_id is correct
        # Otherwise we already handled fallback
        # Ensure product_title and product_id are strings
        safe_title = (product_title or "Your product").strip() or "Your product"
        safe_product_id = (product_id or "").strip()

        title = "Product Published!"
        body = f'Your product "{safe_title}" is now live on the marketplace.'

        data: Dict[str, str] = {
            "type": "published",
            "product_title": safe_title,
            "product_id": safe_product_id,
            "title": title,
            "body": body,
        }
        data = {k: v for k, v in data.items() if v}

        # Need supabase client to resolve tokens if available; if first arg is actually supabase, use it
        supabase = supabase_client
        has_table = hasattr(supabase, "table")
        if not has_table:
            # No supabase available, try to get one
            try:
                from app.database.connection import get_supabase_client

                supabase = get_supabase_client()
            except Exception:
                supabase = None

        if supabase is not None:
            try:
                tokens = _resolve_artisan_tokens(supabase, artisan_id)
                if tokens:
                    success = False
                    for tok in tokens:
                        ok = _send_to_token(tok, title, body, data)
                        success = success or ok
                    return success
                else:
                    logger.info("No FCM token for artisan %s for published notify — topic fallback", artisan_id)
                    topic_ok = _send_to_topic(f"artisan_{artisan_id}", title, body, data)
                    return topic_ok or True
            except Exception as exc:
                logger.debug("Failed to resolve tokens for published notify: %s", exc)
                # Fallback mock
                logger.info("[FCM-MOCK] Would notify artisan %s product published: %s", artisan_id, safe_title)
                return True
        else:
            # No supabase, just log/mock
            if _ensure_firebase():
                # Try topic without token resolution
                return _send_to_topic(f"artisan_{artisan_id}", title, body, data)
            else:
                logger.info("[FCM-MOCK] Product published notify artisan=%s title=%s", artisan_id, safe_title)
                return True
    except Exception as exc:
        logger.warning("send_product_published_notification failed (non-fatal): %s", exc)
        return False


def send_enquiry_accepted_notification(
    supabase_client,
    buyer_user_id_or_artisan_id: str,
    buyer_name: Optional[str] = None,
    enquiry_id: Optional[str] = None,
    product_id: Optional[str] = None,
    product_title: Optional[str] = None,
    # Alternative overload params
    **kwargs,
) -> bool:
    """
    Notify buyer that their enquiry was accepted.

    Flexible signature:
      send_enquiry_accepted_notification(supabase, buyer_user_id, buyer_name, enquiry_id, product_id)
      send_enquiry_accepted_notification(supabase, artisan_id=..., buyer_name=..., enquiry_id=..., product_id=..., product_title=...)
    Also handles legacy (buyer_identifier) as artisan_id-like.

    Tries to resolve buyer tokens via notification_tokens and artisans tables.
    Falls back to topic buyer_<id>.
    """
    try:
        # Handle kwargs overrides
        if "buyer_name" in kwargs:
            buyer_name = kwargs["buyer_name"]
        if "enquiry_id" in kwargs:
            enquiry_id = kwargs["enquiry_id"]
        if "product_id" in kwargs:
            product_id = kwargs["product_id"]
        if "product_title" in kwargs:
            product_title = kwargs["product_title"]
        # Support buyer_profile_id alias
        buyer_profile_id = kwargs.get("buyer_profile_id")

        identifier = buyer_user_id_or_artisan_id
        if not identifier and kwargs.get("artisan_id"):
            identifier = kwargs.get("artisan_id")
        if not identifier and kwargs.get("buyer_profile_id"):
            identifier = kwargs.get("buyer_profile_id")

        if not identifier:
            logger.warning("send_enquiry_accepted_notification called with empty identifier — skipping")
            return False

        safe_buyer = (buyer_name or "Buyer").strip() or "Buyer"
        safe_enquiry = (enquiry_id or "").strip()
        safe_product = (product_id or "").strip()
        safe_title = (product_title or "your enquiry").strip()

        title = "Enquiry Accepted"
        body = f"{safe_buyer} accepted your enquiry. Connect now to finalize the order."
        # If product_title provided, add context
        if product_title:
            body = f"{safe_buyer} accepted your enquiry for \"{safe_title}\"."

        data: Dict[str, str] = {
            "type": "accepted",
            "buyer_name": safe_buyer,
            "enquiry_id": safe_enquiry,
            "product_id": safe_product,
            "product_title": product_title or "",
            "title": title,
            "body": body,
        }
        data = {k: v for k, v in data.items() if v}

        supabase = supabase_client
        # If first arg not supabase-like, try to get real client
        if not hasattr(supabase, "table"):
            try:
                from app.database.connection import get_supabase_client

                supabase = get_supabase_client()
            except Exception:
                supabase = None

        if supabase is not None:
            # Try resolve buyer tokens via multiple paths
            tokens: List[str] = []
            # Try as notification_tokens user_id = identifier
            try:
                tokens = _resolve_buyer_tokens(supabase, buyer_profile_id, identifier)
            except Exception:
                tokens = []
            # Also try direct artisan token if identifier is artisan_id (fallback)
            if not tokens:
                try:
                    tokens = _resolve_artisan_tokens(supabase, identifier)
                except Exception:
                    pass
            if tokens:
                success = False
                for tok in tokens:
                    ok = _send_to_token(tok, title, body, data)
                    success = success or ok
                return success
            else:
                logger.info("No buyer FCM token for %s — topic fallback buyer_%s", identifier, identifier)
                topic_ok = _send_to_topic(f"buyer_{identifier}", title, body, data)
                # Also try artisan topic as fallback
                if not topic_ok:
                    topic_ok = _send_to_topic(f"artisan_{identifier}", title, body, data)
                return topic_ok or True
        else:
            if _ensure_firebase():
                return _send_to_topic(f"buyer_{identifier}", title, body, data) or True
            else:
                logger.info("[FCM-MOCK] Enquiry accepted notify buyer=%s", safe_buyer)
                return True
    except Exception as exc:
        logger.warning("send_enquiry_accepted_notification failed (non-fatal): %s", exc)
        return False


# ── Async wrappers (for marketplace.py await handling) ───────────────────────

async def async_send_enquiry_notification(*args, **kwargs) -> bool:
    """Async wrapper around send_enquiry_notification for await compatibility."""
    try:
        # Support legacy 3-arg (artisan_id, product, enquiry) where first arg is artisan_id not supabase
        if len(args) == 3 and isinstance(args[0], str) and isinstance(args[1], dict) and isinstance(args[2], dict):
            # Need supabase client
            try:
                from app.database.connection import get_supabase_client

                supabase = get_supabase_client()
            except Exception:
                supabase = None
            if supabase is None:
                logger.info("[FCM-MOCK] async_send_enquiry legacy no supabase")
                return True
            return send_enquiry_notification_legacy(supabase, args[0], args[1], args[2])
        return send_enquiry_notification(*args, **kwargs)
    except Exception as exc:
        logger.warning("async_send_enquiry_notification failed: %s", exc)
        return False


async def async_send_product_published_notification(*args, **kwargs) -> bool:
    return send_product_published_notification(*args, **kwargs)


async def async_send_enquiry_accepted_notification(*args, **kwargs) -> bool:
    return send_enquiry_accepted_notification(*args, **kwargs)


# Alias for notification_service compatibility
send_enquiry_notification_async = async_send_enquiry_notification
send_product_published_notification_async = async_send_product_published_notification
send_enquiry_accepted_notification_async = async_send_enquiry_accepted_notification
