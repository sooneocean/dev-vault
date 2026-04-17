"""
Advanced caching system with multiple backends and eviction strategies.

Supports in-memory, Redis, and filesystem caching with TTL and hit tracking.
"""

import logging
import hashlib
import pickle
import json
import inspect
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from collections import OrderedDict

logger = logging.getLogger(__name__)

# Try to import Redis
try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    logger.warning("Redis not available for caching")


class CacheBackendType(str, Enum):
    """Cache backend types."""
    MEMORY = "memory"
    REDIS = "redis"
    FILESYSTEM = "filesystem"


class EvictionPolicy(str, Enum):
    """Cache eviction policies."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In First Out
    TTL = "ttl"  # Time To Live


@dataclass
class CacheEntry:
    """Single cache entry."""
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    size_bytes: int = 0
    ttl_seconds: Optional[int] = None


@dataclass
class CacheStats:
    """Cache statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_size_bytes: int = 0
    entry_count: int = 0
    hit_rate: float = 0.0


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set value in cache."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete cache entry."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass

    @abstractmethod
    def clear(self) -> bool:
        """Clear all cache."""
        pass

    @abstractmethod
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        pass


class InMemoryCache(CacheBackend):
    """In-memory cache backend with LRU/LFU/FIFO/TTL policies."""

    def __init__(
        self,
        max_size_bytes: int = 1024 * 1024 * 100,  # 100 MB
        eviction_policy: EvictionPolicy = EvictionPolicy.LRU,
    ):
        self.max_size_bytes = max_size_bytes
        self.eviction_policy = eviction_policy
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stats = CacheStats()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        self._cleanup_expired()

        if key not in self.cache:
            self.stats.misses += 1
            return None

        entry = self.cache[key]

        # Check TTL
        if entry.ttl_seconds:
            age = (datetime.now(timezone.utc) - entry.accessed_at).total_seconds()
            if age > entry.ttl_seconds:
                del self.cache[key]
                self.stats.misses += 1
                return None

        # Update access info
        entry.accessed_at = datetime.now(timezone.utc)
        entry.access_count += 1

        # Move to end for LRU
        if self.eviction_policy == EvictionPolicy.LRU:
            self.cache.move_to_end(key)

        self.stats.hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set value in cache."""
        self._cleanup_expired()

        # Calculate size (rough estimate)
        size = len(pickle.dumps(value))

        # Check if we need to evict
        current_size = sum(e.size_bytes for e in self.cache.values())
        while current_size + size > self.max_size_bytes and self.cache:
            self._evict_one()
            current_size = sum(e.size_bytes for e in self.cache.values())

        now = datetime.now(timezone.utc)
        self.cache[key] = CacheEntry(
            key=key,
            value=value,
            created_at=now,
            accessed_at=now,
            size_bytes=size,
            ttl_seconds=ttl_seconds,
        )

        # Move to end for LRU
        if self.eviction_policy == EvictionPolicy.LRU:
            self.cache.move_to_end(key)

        return True

    def delete(self, key: str) -> bool:
        """Delete cache entry."""
        if key in self.cache:
            del self.cache[key]
            return True
        return False

    def exists(self, key: str) -> bool:
        """Check if key exists and not expired."""
        return self.get(key) is not None

    def clear(self) -> bool:
        """Clear all cache."""
        self.cache.clear()
        return True

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        self._cleanup_expired()

        total_size = sum(e.size_bytes for e in self.cache.values())
        total_accesses = self.stats.hits + self.stats.misses

        self.stats.total_size_bytes = total_size
        self.stats.entry_count = len(self.cache)
        self.stats.hit_rate = (
            self.stats.hits / total_accesses if total_accesses > 0 else 0.0
        )

        return self.stats

    def _evict_one(self):
        """Evict one entry based on policy."""
        if not self.cache:
            return

        if self.eviction_policy == EvictionPolicy.LRU:
            # Remove oldest (least recently used)
            key = next(iter(self.cache))
        elif self.eviction_policy == EvictionPolicy.LFU:
            # Remove least frequently used
            key = min(self.cache.keys(), key=lambda k: self.cache[k].access_count)
        elif self.eviction_policy == EvictionPolicy.FIFO:
            # Remove oldest created
            key = min(self.cache.keys(), key=lambda k: self.cache[k].created_at)
        else:
            key = next(iter(self.cache))

        del self.cache[key]
        self.stats.evictions += 1

    def _cleanup_expired(self):
        """Remove expired entries."""
        now = datetime.now(timezone.utc)
        expired = []

        for key, entry in self.cache.items():
            if entry.ttl_seconds:
                age = (now - entry.accessed_at).total_seconds()
                if age > entry.ttl_seconds:
                    expired.append(key)

        for key in expired:
            del self.cache[key]


class RedisCache(CacheBackend):
    """Redis-based cache backend."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.enabled = HAS_REDIS
        self.stats = CacheStats()

        if not self.enabled:
            logger.warning("Redis not available for caching")
            return

        try:
            self.redis = redis.from_url(redis_url)
            self.redis.ping()
            logger.info(f"Redis cache connected: {redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.enabled = False

    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        if not self.enabled:
            return None

        try:
            value = self.redis.get(key)
            if value is None:
                self.stats.misses += 1
                return None

            self.stats.hits += 1
            return pickle.loads(value)
        except Exception as e:
            logger.error(f"Failed to get from Redis: {e}")
            self.stats.misses += 1
            return None

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set value in Redis cache."""
        if not self.enabled:
            return False

        try:
            serialized = pickle.dumps(value)
            if ttl_seconds:
                self.redis.setex(key, ttl_seconds, serialized)
            else:
                self.redis.set(key, serialized)
            return True
        except Exception as e:
            logger.error(f"Failed to set in Redis: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete cache entry."""
        if not self.enabled:
            return False

        try:
            return self.redis.delete(key) > 0
        except Exception as e:
            logger.error(f"Failed to delete from Redis: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not self.enabled:
            return False

        try:
            return self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Failed to check key: {e}")
            return False

    def clear(self) -> bool:
        """Clear all cache."""
        if not self.enabled:
            return False

        try:
            self.redis.flushdb()
            return True
        except Exception as e:
            logger.error(f"Failed to clear Redis: {e}")
            return False

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        if not self.enabled:
            return self.stats

        try:
            info = self.redis.info()
            self.stats.total_size_bytes = info.get("used_memory", 0)
            return self.stats
        except Exception as e:
            logger.warning(f"Failed to get Redis stats: {e}")
            return self.stats


class FilesystemCache(CacheBackend):
    """Filesystem-based cache backend."""

    def __init__(self, cache_dir: str = "/tmp/watermark_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.stats = CacheStats()

    def get(self, key: str) -> Optional[Any]:
        """Get value from filesystem cache."""
        try:
            cache_file = self._get_cache_file(key)
            if not cache_file.exists():
                self.stats.misses += 1
                return None

            # Check TTL metadata
            meta_file = cache_file.with_suffix(".meta")
            if meta_file.exists():
                with open(meta_file, "r") as f:
                    meta = json.load(f)
                    if "ttl_seconds" in meta and "created_at" in meta:
                        age = datetime.now(timezone.utc).timestamp() - float(meta["created_at"])
                        if age > meta["ttl_seconds"]:
                            cache_file.unlink()
                            meta_file.unlink()
                            self.stats.misses += 1
                            return None

            with open(cache_file, "rb") as f:
                self.stats.hits += 1
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Failed to get from filesystem: {e}")
            self.stats.misses += 1
            return None

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set value in filesystem cache."""
        try:
            cache_file = self._get_cache_file(key)
            with open(cache_file, "wb") as f:
                pickle.dump(value, f)

            # Save metadata
            if ttl_seconds:
                meta_file = cache_file.with_suffix(".meta")
                with open(meta_file, "w") as f:
                    json.dump({
                        "ttl_seconds": ttl_seconds,
                        "created_at": datetime.now(timezone.utc).timestamp(),
                    }, f)

            return True
        except Exception as e:
            logger.error(f"Failed to set in filesystem: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete cache entry."""
        try:
            cache_file = self._get_cache_file(key)
            if cache_file.exists():
                cache_file.unlink()

            meta_file = cache_file.with_suffix(".meta")
            if meta_file.exists():
                meta_file.unlink()

            return True
        except Exception as e:
            logger.error(f"Failed to delete from filesystem: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        return self._get_cache_file(key).exists()

    def clear(self) -> bool:
        """Clear all cache."""
        try:
            for file in self.cache_dir.glob("*"):
                file.unlink()
            return True
        except Exception as e:
            logger.error(f"Failed to clear filesystem cache: {e}")
            return False

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        try:
            total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*") if f.is_file())
            entry_count = len(list(self.cache_dir.glob("*.pickle")))

            self.stats.total_size_bytes = total_size
            self.stats.entry_count = entry_count

            return self.stats
        except Exception as e:
            logger.warning(f"Failed to get filesystem stats: {e}")
            return self.stats

    def _get_cache_file(self, key: str) -> Path:
        """Get cache file path for key."""
        # Use hash to avoid filesystem path issues
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.pickle"


class CacheManager:
    """High-level cache manager."""

    def __init__(
        self,
        backend_type: CacheBackendType = CacheBackendType.MEMORY,
        **kwargs,
    ):
        if backend_type == CacheBackendType.REDIS:
            self.backend = RedisCache(**kwargs)
        elif backend_type == CacheBackendType.FILESYSTEM:
            self.backend = FilesystemCache(**kwargs)
        else:
            self.backend = InMemoryCache(**kwargs)

        self.backend_type = backend_type
        logger.info(f"Cache manager initialized: {backend_type}")

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return self.backend.get(key)

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set value in cache."""
        return self.backend.set(key, value, ttl_seconds)

    def delete(self, key: str) -> bool:
        """Delete cache entry."""
        return self.backend.delete(key)

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        return self.backend.exists(key)

    def clear(self) -> bool:
        """Clear cache."""
        return self.backend.clear()

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self.backend.get_stats()

    def cache_decorator(self, ttl_seconds: Optional[int] = None):
        """Decorator for caching function results."""
        def decorator(func):
            async def async_wrapper(*args, **kwargs):
                # Create cache key from function name and args
                cache_key = f"{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"

                # Try to get from cache
                cached = self.get(cache_key)
                if cached is not None:
                    return cached

                # Call function and cache result
                result = await func(*args, **kwargs) if inspect.iscoroutinefunction(func) else func(*args, **kwargs)
                self.set(cache_key, result, ttl_seconds)
                return result

            def sync_wrapper(*args, **kwargs):
                cache_key = f"{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"
                cached = self.get(cache_key)
                if cached is not None:
                    return cached

                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl_seconds)
                return result

            return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

        return decorator


# Global cache manager instance
cache_manager: Optional[CacheManager] = None


def init_cache(
    backend_type: CacheBackendType = CacheBackendType.MEMORY,
    **kwargs,
):
    """Initialize global cache manager."""
    global cache_manager
    cache_manager = CacheManager(backend_type, **kwargs)
    logger.info(f"Global cache initialized: {backend_type}")


def get_cache() -> CacheManager:
    """Get global cache manager instance."""
    global cache_manager
    if cache_manager is None:
        init_cache()
    return cache_manager
