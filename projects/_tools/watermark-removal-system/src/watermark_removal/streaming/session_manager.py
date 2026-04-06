"""
Streaming session state management.

Maintains per-session frame buffer, checkpoint state, and metrics accumulation.
Handles result caching with TTL.
"""

import asyncio
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List
import json

logger = logging.getLogger(__name__)


@dataclass
class FrameResult:
    """Result of single frame processing."""

    frame_id: int
    status: str  # "pending", "processing", "completed", "error"
    timestamp: datetime = field(default_factory=datetime.now)
    metrics: Dict = field(default_factory=dict)  # temporal_consistency, boundary_smoothness, etc.
    error_message: Optional[str] = None
    output_path: Optional[Path] = None


@dataclass
class StreamingSession:
    """Session state for streaming frame processing."""

    session_id: str
    config: "ProcessConfig"  # Type hint only, avoid circular import
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    frame_buffer: List[FrameResult] = field(default_factory=list)
    result_cache: Dict[int, FrameResult] = field(default_factory=dict)
    metrics_accumulator: Dict = field(default_factory=dict)
    checkpoint_state: Optional[Dict] = None
    error_count: int = 0

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now()

    def add_frame_result(self, frame_id: int, result: FrameResult):
        """Add frame result to cache and buffer."""
        self.result_cache[frame_id] = result
        self.frame_buffer.append(result)
        self.update_activity()

    def get_frame_result(self, frame_id: int) -> Optional[FrameResult]:
        """Retrieve cached frame result."""
        return self.result_cache.get(frame_id)

    def is_expired(self, ttl_sec: int = 300) -> bool:
        """Check if session has expired based on TTL."""
        elapsed = (datetime.now() - self.last_activity).total_seconds()
        return elapsed > ttl_sec

    def to_dict(self) -> dict:
        """Serialize session state (excluding large data)."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "frame_count": len(self.frame_buffer),
            "metrics": self.metrics_accumulator,
            "error_count": self.error_count,
        }


class SessionManager:
    """Manage multiple streaming sessions."""

    def __init__(self, result_ttl_sec: int = 300, session_ttl_sec: int = 600):
        """
        Initialize session manager.

        Args:
            result_ttl_sec: Time-to-live for cached results (seconds)
            session_ttl_sec: Time-to-live for idle sessions (seconds)
        """
        self.sessions: Dict[str, StreamingSession] = {}
        self.result_ttl_sec = result_ttl_sec
        self.session_ttl_sec = session_ttl_sec
        self._lock = asyncio.Lock()
        logger.info(
            f"SessionManager: result_ttl={result_ttl_sec}s, session_ttl={session_ttl_sec}s"
        )

    async def create_session(self, config: "ProcessConfig") -> str:
        """
        Create new streaming session.

        Args:
            config: ProcessConfig for this session

        Returns:
            session_id (str): Unique session identifier
        """
        async with self._lock:
            session_id = secrets.token_urlsafe(32)
            session = StreamingSession(session_id=session_id, config=config)
            self.sessions[session_id] = session
            logger.info(f"Created session: {session_id}")
            return session_id

    async def get_session(self, session_id: str) -> Optional[StreamingSession]:
        """Retrieve active session."""
        async with self._lock:
            session = self.sessions.get(session_id)
            if session and session.is_expired(self.session_ttl_sec):
                logger.warning(f"Session expired: {session_id}")
                del self.sessions[session_id]
                return None
            if session:
                session.update_activity()
            return session

    async def end_session(self, session_id: str) -> Optional[dict]:
        """
        End session and return summary.

        Args:
            session_id: Session identifier

        Returns:
            Session summary dict (metrics, frame count, etc.)
        """
        async with self._lock:
            session = self.sessions.pop(session_id, None)
            if not session:
                logger.warning(f"Session not found: {session_id}")
                return None

            summary = session.to_dict()
            logger.info(f"Ended session: {session_id}, frames={len(session.frame_buffer)}")
            return summary

    async def cleanup_expired_sessions(self):
        """Remove expired sessions (for periodic maintenance)."""
        async with self._lock:
            expired = [
                sid
                for sid, session in self.sessions.items()
                if session.is_expired(self.session_ttl_sec)
            ]
            for sid in expired:
                del self.sessions[sid]
                logger.info(f"Cleaned up expired session: {sid}")
            return len(expired)

    async def get_active_session_count(self) -> int:
        """Get count of active sessions."""
        async with self._lock:
            return len(self.sessions)
