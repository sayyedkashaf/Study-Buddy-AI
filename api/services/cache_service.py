"""
Cache Service — Redis wrapper with automatic in-memory fallback.

If Redis is not available (common on Windows dev environments),
gracefully falls back to an in-memory dictionary cache.
"""

import json
import hashlib
import logging
from datetime import datetime, timezone

from api.core.config import REDIS_HOST, REDIS_PORT

logger = logging.getLogger(__name__)


class CacheService:
    """
    Cache service with Redis primary and in-memory fallback.
    Uses singleton pattern — Redis connection is attempted only once.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if CacheService._initialized:
            return
        CacheService._initialized = True

        self._redis = None
        self._memory_cache: dict = {}  # Fallback
        self._using_redis = False
        self._connect_redis()

    def _connect_redis(self):
        """Try connecting to Redis once; fall back to in-memory if unavailable."""
        self._using_redis = False
        try:
            import redis

            self._redis = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=0,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
            self._redis.ping()
            self._using_redis = True
            logger.info("✅ Connected to Redis cache")
        except Exception:
            logger.info("ℹ️  Redis not available — using in-memory cache (this is fine for development)")
            self._redis = None
            self._using_redis = False

    @staticmethod
    def cache_key(prefix: str, data: str) -> str:
        """Generate a deterministic cache key from a prefix and data string."""
        hash_digest = hashlib.md5(data.encode()).hexdigest()
        return f"{prefix}:{hash_digest}"

    def get(self, key: str):
        """
        Retrieve a value from cache.

        Returns:
            Deserialized value, or None if not found / expired.
        """
        if self._using_redis and self._redis:
            try:
                value = self._redis.get(key)
                return json.loads(value) if value else None
            except Exception as e:
                logger.warning(f"Redis GET failed ({e}), switching to in-memory cache")
                self._using_redis = False

        entry = self._memory_cache.get(key)
        if entry is None:
            return None
        # Check TTL
        if entry["expires_at"] and datetime.now(timezone.utc).timestamp() > entry["expires_at"]:
            del self._memory_cache[key]
            return None
        return entry["value"]

    def set(self, key: str, value, ttl: int = 3600):
        """
        Store a value in cache with TTL.

        Args:
            key: Cache key.
            value: Any JSON-serializable value.
            ttl: Time to live in seconds (default: 1 hour).
        """
        if self._using_redis and self._redis:
            try:
                self._redis.setex(key, ttl, json.dumps(value))
                return
            except Exception as e:
                logger.warning(f"Redis SET failed ({e}), switching to in-memory cache")
                self._using_redis = False

        self._memory_cache[key] = {
            "value": value,
            "expires_at": datetime.now(timezone.utc).timestamp() + ttl,
        }

    def delete(self, key: str):
        """Remove a key from cache."""
        if self._using_redis and self._redis:
            try:
                self._redis.delete(key)
            except Exception as e:
                logger.warning(f"Redis DELETE failed: {e}")
        self._memory_cache.pop(key, None)

    def clear_prefix(self, prefix: str):
        """Delete all keys matching a prefix."""
        if self._using_redis and self._redis:
            try:
                keys = self._redis.keys(f"{prefix}:*")
                if keys:
                    self._redis.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis CLEAR failed: {e}")

        keys_to_delete = [k for k in self._memory_cache if k.startswith(f"{prefix}:")]
        for k in keys_to_delete:
            del self._memory_cache[k]

    @property
    def backend(self) -> str:
        """Return which backend is active."""
        return "redis" if self._using_redis else "memory"
