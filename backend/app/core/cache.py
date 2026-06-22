"""Redis caching layer — specialties, doctor profiles, online status.

Usage:
    from app.core.cache import cache
    await cache.set("key", data, ttl=300)
    data = await cache.get("key")
    await cache.delete("key")
    await cache.invalidate_pattern("doctor:*")
"""

import json
from typing import Optional, Any
from app.core.config import settings


class RedisCache:
    """Redis-backed cache with JSON serialization.

    Falls back to in-memory dict when Redis is unavailable.
    """

    def __init__(self):
        self._redis = None
        self._fallback: dict = {}  # in-memory fallback
        self._connected = False

    async def connect(self):
        """Initialize Redis connection."""
        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            await self._redis.ping()
            self._connected = True
        except Exception:
            self._connected = False
            self._redis = None

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        if self._connected and self._redis:
            try:
                val = await self._redis.get(key)
                return json.loads(val) if val else None
            except Exception:
                pass
        return self._fallback.get(key)

    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set a value with TTL (seconds)."""
        if self._connected and self._redis:
            try:
                await self._redis.setex(key, ttl, json.dumps(value, default=str))
                return
            except Exception:
                pass
        self._fallback[key] = value

    async def delete(self, key: str):
        """Delete a key."""
        if self._connected and self._redis:
            try:
                await self._redis.delete(key)
                return
            except Exception:
                pass
        self._fallback.pop(key, None)

    async def invalidate_pattern(self, pattern: str):
        """Delete all keys matching a pattern (e.g. 'doctor:*')."""
        if self._connected and self._redis:
            try:
                cursor = 0
                while True:
                    cursor, keys = await self._redis.scan(cursor, match=pattern, count=100)
                    if keys:
                        await self._redis.delete(*keys)
                    if cursor == 0:
                        break
                return
            except Exception:
                pass
        # Fallback: remove matching keys
        to_delete = [k for k in self._fallback if _match_pattern(k, pattern)]
        for k in to_delete:
            del self._fallback[k]

    async def close(self):
        if self._redis:
            await self._redis.close()

    @property
    def is_connected(self) -> bool:
        return self._connected


def _match_pattern(key: str, pattern: str) -> bool:
    """Simple glob matching for in-memory fallback."""
    if pattern.endswith("*"):
        return key.startswith(pattern[:-1])
    return key == pattern


# ── Cache key builders ──

def specialties_key() -> str:
    return "specialties:all"


def doctor_profile_key(doctor_id) -> str:
    return f"doctor:{doctor_id}:profile"


def doctor_online_key(doctor_id) -> str:
    return f"doctor:{doctor_id}:online"


# Singleton
cache = RedisCache()
