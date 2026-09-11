"""
Common Pydantic models used across endpoints.

Phase C audit — response model duplication:
- `ApiResponse[T]` is the intended generic envelope (success/message/data/error_code/details)
  for all success responses. Currently usage is split:
  * `analytics` (`ApiResponse[AnalyticsDashboardResponse]`) and some products
    endpoints use it correctly.
  * Many other handlers (`auth.sync_user`, `products.create`, `catalog`, `pricing`,
    `image`, `marketplace`, `notifications`) return raw dicts
    `{"success": True, "message": ..., "data": ...}` or `JSONResponse` with same shape.
  * This duplicates the envelope without type safety but preserves backward compat
    JSON shapes (`/api/v1/*` contracts). No breaking change made in Phase C.
  * Recommended incremental path (non-breaking): adopt `ApiResponse` gradually,
    keeping JSON shape identical, and add contract tests asserting envelope
    consistency. Keep generic for now; don't remove dict returns until versioned.
"""

from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """
    Standard envelope for all API responses.

    Phase C: used inconsistently — see module docstring. All handlers must
    still produce the same JSON shape `{success, message, data, error_code?}`.
    Whether via this generic or raw dict, the wire format is identical and
    tested. This model remains the canonical envelope for new endpoints.
    """
    success: bool = True
    message: str = "OK"
    data: Optional[T] = None
    error_code: Optional[str] = None
    details: Optional[Any] = None


class HealthResponse(BaseModel):
    status: str
