"""
Specialized Supabase Storage bucket handling for product images.

- ensure_bucket_exists()
- upload_image(file: UploadFile, artisan_id: str) -> public_url
  Validates MIME (jpeg/png/webp), size <10MB, generates {artisan_id}/{uuid}.{ext}

Phase C notes:
- Blocking I/O: `client.storage.from_(...).upload()` is sync and called from
  async handlers (`upload_image`, `upload_bytes`). Under high concurrency,
  offload via `await run_in_threadpool(...)`. Current sync kept for backward
  compat with minimal load; wrappers are comments for future scale.
- No PII logged: logs only bucket/path prefix, never raw token.
"""

import logging
import mimetypes
import os
import uuid
from typing import Optional

from fastapi import HTTPException, UploadFile, status

from app.database.connection import get_supabase_client

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def _get_bucket_name() -> str:
    try:
        from app.core.config import get_settings

        return get_settings().SUPABASE_STORAGE_BUCKET or "product-images"
    except Exception:
        return os.getenv("SUPABASE_STORAGE_BUCKET", "product-images")


def _resolve_extension(content_type: Optional[str], filename: Optional[str]) -> str:
    """Derive file extension from MIME or original filename."""
    # Prefer MIME mapping
    if content_type and content_type.lower() in ALLOWED_MIME_TYPES:
        return ALLOWED_MIME_TYPES[content_type.lower()]

    # Fallback to filename extension
    if filename and "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext == "jpeg":
            ext = "jpg"
        if ext in ALLOWED_EXTENSIONS:
            return ext

    # Last resort: guess from MIME
    if content_type:
        guessed = mimetypes.guess_extension(content_type)
        if guessed:
            ext = guessed.lstrip(".").lower()
            if ext == "jpeg":
                ext = "jpg"
            if ext in ALLOWED_EXTENSIONS:
                return ext

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_MIME_TYPES.keys()))}",
    )


def ensure_bucket_exists() -> bool:
    """
    Checks if the configured bucket exists, attempts to create if missing.
    Returns True if bucket is available, raises HTTPException on failure.

    Note: Service_role key is required to create buckets. In production, create buckets
    via Supabase dashboard or migration instead.
    """
    client = get_supabase_client()
    bucket = _get_bucket_name()

    try:
        # List buckets and check existence
        buckets = client.storage.list_buckets()
        # list_buckets may return list of Bucket objects or dicts
        bucket_names = []
        for b in buckets or []:
            if isinstance(b, dict):
                bucket_names.append(b.get("name") or b.get("id"))
            else:
                bucket_names.append(getattr(b, "name", None) or getattr(b, "id", None))

        if bucket in bucket_names:
            logger.debug("Storage bucket '%s' exists", bucket)
            return True

        logger.warning("Storage bucket '%s' not found — attempting to create", bucket)
        try:
            # Create bucket as public for product images
            client.storage.create_bucket(bucket, options={"public": True})
            logger.info("Created storage bucket '%s' (public)", bucket)
            return True
        except Exception as create_exc:
            # If creation fails due to already exists race, treat as success
            if "already exists" in str(create_exc).lower() or "duplicate" in str(create_exc).lower():
                logger.info("Bucket '%s' already exists (race)", bucket)
                return True
            logger.error("Failed to create bucket '%s': %s", bucket, create_exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Storage bucket '{bucket}' not found and could not be created: {create_exc}",
            ) from create_exc

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to verify storage bucket '%s': %s", bucket, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify storage bucket: {exc}",
        ) from exc


async def upload_image(file: UploadFile, artisan_id: str) -> str:
    """
    Validates and uploads an UploadFile to Supabase Storage.

    Validations:
      - artisan_id required
      - MIME must be jpeg/png/webp
      - Size < 10 MB
      - Generates filename {artisan_id}/{uuid}.{ext}

    Returns:
        Public URL string
    """
    if not artisan_id:
        raise HTTPException(status_code=400, detail="artisan_id is required")
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="File is required")

    content_type = (file.content_type or "").lower().strip()

    # Validate MIME
    if content_type not in ALLOWED_MIME_TYPES:
        # Allow fallback check via extension if content_type missing/misreported
        ext_check = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext_check not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type '{content_type or ext_check}'. Allowed: jpeg, png, webp",
            )
        # If extension is valid but MIME not, trust extension and set MIME
        if ext_check in ("jpg", "jpeg"):
            content_type = "image/jpeg"
        elif ext_check == "png":
            content_type = "image/png"
        elif ext_check == "webp":
            content_type = "image/webp"

    # Read bytes and validate size
    try:
        file_bytes = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {exc}") from exc

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({len(file_bytes)} bytes). Max is {MAX_FILE_SIZE_BYTES} bytes (10MB)",
        )

    # Ensure bucket exists (idempotent)
    ensure_bucket_exists()

    # Generate unique filename
    ext = _resolve_extension(content_type, file.filename)
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    storage_path = f"{artisan_id}/{unique_name}"
    bucket = _get_bucket_name()
    client = get_supabase_client()

    try:
        client.storage.from_(bucket).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": content_type, "upsert": "false"},
        )
        logger.info("Uploaded image %s (%d bytes) to bucket %s", storage_path, len(file_bytes), bucket)
    except Exception as exc:
        err_lower = str(exc).lower()
        if "already exists" in err_lower or "duplicate" in err_lower:
            # Extremely unlikely due to UUID, but retry with new UUID
            storage_path = f"{artisan_id}/{uuid.uuid4().hex}.{ext}"
            try:
                client.storage.from_(bucket).upload(
                    path=storage_path,
                    file=file_bytes,
                    file_options={"content-type": content_type, "upsert": "false"},
                )
            except Exception as retry_exc:
                logger.error("Retry upload failed for %s: %s", storage_path, retry_exc)
                raise HTTPException(status_code=500, detail=f"Failed to upload image: {retry_exc}") from retry_exc
        else:
            logger.error("Failed to upload image %s: %s", storage_path, exc)
            raise HTTPException(status_code=500, detail=f"Failed to upload image: {exc}") from exc

    # Return public URL
    try:
        url = client.storage.from_(bucket).get_public_url(storage_path)
        if isinstance(url, dict):
            public_url = url.get("publicUrl") or url.get("public_url") or str(url)
        else:
            public_url = str(url)
        # Supabase-py v2 returns the URL string directly
        # Ensure we return a string URL
        logger.debug("Public URL for %s: %s", storage_path, public_url)
        return public_url
    except Exception as exc:
        logger.error("Failed to get public URL for %s: %s", storage_path, exc)
        raise HTTPException(status_code=500, detail=f"Upload succeeded but failed to get public URL: {exc}") from exc


def get_public_url_for_path(path: str) -> str:
    """Helper to get public URL for an existing storage path."""
    if not path:
        raise HTTPException(status_code=400, detail="Storage path is required")
    client = get_supabase_client()
    bucket = _get_bucket_name()
    try:
        url = client.storage.from_(bucket).get_public_url(path)
        if isinstance(url, dict):
            return url.get("publicUrl") or url.get("public_url") or str(url)
        return str(url)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to get public URL: {exc}") from exc


def upload_bytes(bucket: str, path: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    """
    Generic bytes upload helper for pipeline and other raw-byte use cases.

    Uploads `data` to Supabase Storage at `path` inside `bucket` and returns
    the public URL. Generates no local file handling; secure random paths
    should be provided by caller (never raw user filename).

    Args:
        bucket: Storage bucket name. If empty/None, resolved from Settings.
        path: Storage object path, e.g., "{artisan_id}/{uuid}_enhanced.png".
        data: Raw bytes to upload.
        content_type: MIME type for the object.

    Returns:
        Public URL string.

    Behavior:
        - Validates path traversal and empty data.
        - Ensures bucket exists (via ensure_bucket_exists when possible).
        - Falls back to placeholder URL in DEBUG mode if Supabase is unavailable
          or credentials missing (https://placeholder.supabase.co/...).
        - Raises HTTPException 500 in production on storage failure.
    """
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty data for upload")
    if not path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Storage path is required")
    # Path traversal guard for storage path itself
    if ".." in path or path.startswith("/") or "\\" in path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid storage path")

    # Resolve bucket
    target_bucket = bucket or _get_bucket_name()

    # Resolve settings for DEBUG fallback
    is_debug = False
    supabase_url: Optional[str] = None
    try:
        from app.core.config import get_settings

        _settings = get_settings()
        is_debug = bool(_settings.DEBUG)
        supabase_url = _settings.SUPABASE_URL
        if not target_bucket:
            target_bucket = _settings.SUPABASE_STORAGE_BUCKET or target_bucket
    except Exception:
        is_debug = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes", "on")
        supabase_url = os.getenv("SUPABASE_URL")
        if not target_bucket:
            target_bucket = os.getenv("SUPABASE_STORAGE_BUCKET", "product-images")

    # Normalize supabase_url for placeholder construction
    placeholder_base = (supabase_url or "").rstrip("/") if supabase_url else "https://placeholder.supabase.co"

    # Try to ensure bucket exists (best-effort, ignore in mock mode)
    if not is_debug or supabase_url:
        try:
            ensure_bucket_exists()
        except Exception as be:
            logger.debug("ensure_bucket_exists failed (non-fatal) for %s: %s", target_bucket, be)

    # Attempt upload
    try:
        client = get_supabase_client()
        # Supabase-py expects file as bytes and file_options with content-type
        client.storage.from_(target_bucket).upload(
            path=path,
            file=data,
            file_options={"content-type": content_type, "upsert": "false"},
        )
        logger.info("Uploaded bytes to %s/%s (%d bytes, %s)", target_bucket, path, len(data), content_type)
    except Exception as exc:
        err_lower = str(exc).lower()
        # Duplicate due to UUID collision (extremely rare) -> try alternative path
        if "already exists" in err_lower or "duplicate" in err_lower:
            alt_path = f"{path.rsplit('.',1)[0]}_{uuid.uuid4().hex[:6]}.{path.rsplit('.',1)[-1]}" if "." in path else f"{path}_{uuid.uuid4().hex[:6]}"
            try:
                client = get_supabase_client()
                client.storage.from_(target_bucket).upload(
                    path=alt_path,
                    file=data,
                    file_options={"content-type": content_type, "upsert": "false"},
                )
                path = alt_path
                logger.info("Retry upload succeeded for alternate path %s/%s", target_bucket, path)
            except Exception as retry_exc:
                if is_debug:
                    logger.warning("Supabase upload failed for %s (%s) — returning mock URL (DEBUG mode)", path, retry_exc)
                    return f"{placeholder_base}/storage/v1/object/public/{target_bucket}/{path}"
                logger.error("Failed to upload bytes to %s/%s: %s", target_bucket, path, retry_exc)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to upload to storage: {retry_exc}") from retry_exc
        else:
            if is_debug:
                logger.warning("Supabase upload failed for %s/%s (%s) — returning mock URL (DEBUG mode)", target_bucket, path, exc)
                return f"{placeholder_base}/storage/v1/object/public/{target_bucket}/{path}"
            logger.error("Failed to upload bytes to %s/%s: %s", target_bucket, path, exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to upload to storage: {exc}") from exc

    # Get public URL
    try:
        client = get_supabase_client()
        url = client.storage.from_(target_bucket).get_public_url(path)
        if isinstance(url, dict):
            public_url = url.get("publicUrl") or url.get("public_url") or str(url)
        else:
            public_url = str(url)
        # If Supabase returns empty or placeholder, construct manually
        if not public_url or public_url == "None" or "None" in public_url:
            raise ValueError("Empty public URL from Supabase")
        logger.debug("Public URL for %s/%s: %s", target_bucket, path, public_url)
        return public_url
    except Exception as exc:
        if is_debug:
            logger.warning("Failed to get public URL for %s/%s (%s) — returning mock URL (DEBUG mode)", target_bucket, path, exc)
            return f"{placeholder_base}/storage/v1/object/public/{target_bucket}/{path}"
        logger.error("Failed to get public URL for %s/%s: %s", target_bucket, path, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload succeeded but failed to get public URL: {exc}") from exc
