"""
Production Redis Async Cache & Session Connection Pool.
"""

import json
import logging
from typing import Any, Optional
import os

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# In-memory fallback cache when Redis is disconnected / offline
_memory_cache: dict = {}


class RedisCache:
    def __init__(self):
        self.connected = False
        self._client = None

    async def initialize(self):
        try:
            import redis.asyncio as aioredis
            self._client = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
            await self._client.ping()
            self.connected = True
            logger.info("Redis cache connected to %s", REDIS_URL)
        except Exception as e:
            self.connected = False
            logger.warning("Redis connection skipped (using in-memory fallback): %s", e)

    async def get(self, key: str) -> Optional[Any]:
        if self.connected and self._client:
            try:
                val = await self._client.get(key)
                return json.loads(val) if val else None
            except Exception:
                pass
        return _memory_cache.get(key)

    async def set(self, key: str, value: Any, expire_seconds: int = 300) -> bool:
        if self.connected and self._client:
            try:
                await self._client.set(key, json.dumps(value), ex=expire_seconds)
                return True
            except Exception:
                pass
        _memory_cache[key] = value
        return True

    async def delete(self, key: str) -> bool:
        if self.connected and self._client:
            try:
                await self._client.delete(key)
            except Exception:
                pass
        _memory_cache.pop(key, None)
        return True


redis_cache = RedisCache()
