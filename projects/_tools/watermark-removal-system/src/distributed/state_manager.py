"""
Distributed state management for coordinating across multiple workers.

Supports Redis and in-memory backends with TTL and consistency guarantees.
"""

import logging
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Try to import Redis
try:
    import redis
    from redis import Redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    logger.warning("Redis not available, using in-memory state")


@dataclass
class StateEntry:
    """Single state entry."""
    key: str
    value: Any
    created_at: datetime
    updated_at: datetime
    ttl_seconds: Optional[int] = None
    version: int = 1


class StateManager(ABC):
    """Abstract base class for state management."""

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set state value."""
        pass

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get state value."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete state entry."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass

    @abstractmethod
    def increment(self, key: str, amount: int = 1) -> int:
        """Increment numeric value."""
        pass

    @abstractmethod
    def get_all(self, pattern: str = "*") -> Dict[str, Any]:
        """Get all entries matching pattern."""
        pass


class InMemoryStateManager(StateManager):
    """In-memory state manager for development."""

    def __init__(self):
        self.state: Dict[str, StateEntry] = {}

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set state value."""
        now = datetime.now(timezone.utc)
        self.state[key] = StateEntry(
            key=key,
            value=value,
            created_at=now,
            updated_at=now,
            ttl_seconds=ttl_seconds,
        )
        self._cleanup_expired()
        logger.debug(f"Set state {key}")
        return True

    def get(self, key: str) -> Optional[Any]:
        """Get state value."""
        self._cleanup_expired()
        entry = self.state.get(key)
        if entry is None:
            return None

        # Check TTL
        if entry.ttl_seconds:
            age = (datetime.now(timezone.utc) - entry.updated_at).total_seconds()
            if age > entry.ttl_seconds:
                del self.state[key]
                return None

        return entry.value

    def delete(self, key: str) -> bool:
        """Delete state entry."""
        if key in self.state:
            del self.state[key]
            logger.debug(f"Deleted state {key}")
            return True
        return False

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        return key in self.state and self.get(key) is not None

    def increment(self, key: str, amount: int = 1) -> int:
        """Increment numeric value."""
        current = self.get(key) or 0
        new_value = current + amount
        self.set(key, new_value)
        return new_value

    def get_all(self, pattern: str = "*") -> Dict[str, Any]:
        """Get all entries matching pattern."""
        self._cleanup_expired()

        if pattern == "*":
            return {k: v.value for k, v in self.state.items()}

        # Simple pattern matching
        result = {}
        for k, v in self.state.items():
            if self._matches_pattern(k, pattern):
                result[k] = v.value
        return result

    def _cleanup_expired(self):
        """Remove expired entries."""
        now = datetime.now(timezone.utc)
        expired = []

        for key, entry in self.state.items():
            if entry.ttl_seconds:
                age = (now - entry.updated_at).total_seconds()
                if age > entry.ttl_seconds:
                    expired.append(key)

        for key in expired:
            del self.state[key]

    @staticmethod
    def _matches_pattern(key: str, pattern: str) -> bool:
        """Simple glob-style pattern matching."""
        import fnmatch
        return fnmatch.fnmatch(key, pattern)


class RedisStateManager(StateManager):
    """Redis-based distributed state manager."""

    def __init__(self, redis_url: str = "redis://localhost:6379", db: int = 0):
        self.redis_url = redis_url
        self.enabled = HAS_REDIS

        if not self.enabled:
            logger.warning("Redis not available")
            return

        try:
            self.redis = redis.from_url(redis_url)
            self.redis.ping()
            logger.info(f"Redis connected: {redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.enabled = False

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set state value in Redis."""
        if not self.enabled:
            return False

        try:
            serialized = json.dumps(value)
            if ttl_seconds:
                self.redis.setex(key, ttl_seconds, serialized)
            else:
                self.redis.set(key, serialized)
            logger.debug(f"Set Redis state {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to set state: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """Get state value from Redis."""
        if not self.enabled:
            return None

        try:
            value = self.redis.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            logger.error(f"Failed to get state: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Delete state entry from Redis."""
        if not self.enabled:
            return False

        try:
            result = self.redis.delete(key)
            logger.debug(f"Deleted Redis state {key}")
            return result > 0
        except Exception as e:
            logger.error(f"Failed to delete state: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        if not self.enabled:
            return False

        try:
            return self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Failed to check key existence: {e}")
            return False

    def increment(self, key: str, amount: int = 1) -> int:
        """Increment numeric value in Redis."""
        if not self.enabled:
            return 0

        try:
            return self.redis.incrby(key, amount)
        except Exception as e:
            logger.error(f"Failed to increment: {e}")
            return 0

    def get_all(self, pattern: str = "*") -> Dict[str, Any]:
        """Get all entries matching pattern from Redis."""
        if not self.enabled:
            return {}

        try:
            keys = self.redis.keys(pattern)
            result = {}
            for key in keys:
                value = self.redis.get(key)
                if value:
                    result[key.decode() if isinstance(key, bytes) else key] = json.loads(value)
            return result
        except Exception as e:
            logger.error(f"Failed to get all states: {e}")
            return {}


class DistributedSessionState:
    """Manage streaming session state across workers."""

    SESSION_KEY_PREFIX = "session:"
    WORKER_KEY_PREFIX = "worker:"
    TASK_KEY_PREFIX = "task:"

    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager

    def create_session(self, session_id: str, session_data: Dict[str, Any], ttl_seconds: int = 3600) -> bool:
        """Create distributed session state."""
        key = f"{self.SESSION_KEY_PREFIX}{session_id}"
        return self.state_manager.set(key, session_data, ttl_seconds)

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session state."""
        key = f"{self.SESSION_KEY_PREFIX}{session_id}"
        return self.state_manager.get(key)

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session state."""
        key = f"{self.SESSION_KEY_PREFIX}{session_id}"
        current = self.state_manager.get(key)
        if current is None:
            return False

        current.update(updates)
        # Preserve TTL by reading and resetting
        return self.state_manager.set(key, current)

    def delete_session(self, session_id: str) -> bool:
        """Delete session state."""
        key = f"{self.SESSION_KEY_PREFIX}{session_id}"
        return self.state_manager.delete(key)

    def register_worker(self, worker_id: str, worker_info: Dict[str, Any], ttl_seconds: int = 300) -> bool:
        """Register worker with heartbeat."""
        key = f"{self.WORKER_KEY_PREFIX}{worker_id}"
        worker_info["heartbeat"] = datetime.now(timezone.utc).isoformat()
        return self.state_manager.set(key, worker_info, ttl_seconds)

    def get_workers(self) -> List[Dict[str, Any]]:
        """Get all active workers."""
        workers = self.state_manager.get_all(f"{self.WORKER_KEY_PREFIX}*")
        return list(workers.values())

    def update_task_progress(self, task_id: str, progress: float, status: str = "running") -> bool:
        """Update task progress."""
        key = f"{self.TASK_KEY_PREFIX}{task_id}"
        return self.state_manager.set(
            key,
            {
                "task_id": task_id,
                "progress": progress,
                "status": status,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            ttl_seconds=3600,
        )

    def get_task_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task progress."""
        key = f"{self.TASK_KEY_PREFIX}{task_id}"
        return self.state_manager.get(key)


class StateManagerFactory:
    """Factory for creating state managers."""

    @staticmethod
    def create(state_type: str = "auto", **kwargs) -> StateManager:
        """
        Create state manager.

        Args:
            state_type: "redis", "memory", or "auto"
            **kwargs: Arguments for state manager

        Returns:
            Configured StateManager instance
        """
        if state_type == "auto":
            if HAS_REDIS:
                return RedisStateManager(**kwargs)
            else:
                logger.info("Using in-memory state (Redis not available)")
                return InMemoryStateManager()

        elif state_type == "redis":
            if not HAS_REDIS:
                logger.warning("Redis not available, falling back to in-memory")
                return InMemoryStateManager()
            return RedisStateManager(**kwargs)

        elif state_type == "memory":
            return InMemoryStateManager()

        else:
            raise ValueError(f"Unknown state type: {state_type}")


# Global state manager instance
state_manager: Optional[StateManager] = None


def init_state_manager(state_type: str = "auto", **kwargs):
    """Initialize global state manager."""
    global state_manager
    state_manager = StateManagerFactory.create(state_type, **kwargs)
    logger.info(f"State manager initialized: {state_type}")


def get_state_manager() -> StateManager:
    """Get global state manager instance."""
    global state_manager
    if state_manager is None:
        init_state_manager()
    return state_manager


def get_session_state() -> DistributedSessionState:
    """Get distributed session state manager."""
    return DistributedSessionState(get_state_manager())
