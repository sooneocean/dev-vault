"""Streaming session management with result caching and TTL."""

import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of a single frame processing operation."""

    frame_id: int
    """Frame identifier in the session."""

    session_id: str
    """Parent session identifier."""

    status: str
    """Processing status: 'pending', 'processing', 'completed', 'error'."""

    output_frame: Optional[np.ndarray] = None
    """Processed frame (HxWx3, uint8) or None if not completed."""

    metrics: dict[str, Any] = field(default_factory=dict)
    """Per-frame metrics (inpaint_quality, boundary_smoothness, etc)."""

    error_message: Optional[str] = None
    """Error message if status is 'error'."""

    created_at: float = field(default_factory=time.time)
    """Timestamp when result was created."""

    completed_at: Optional[float] = None
    """Timestamp when processing completed."""

    def is_expired(self, ttl_sec: int) -> bool:
        """Check if result has expired based on TTL.

        Args:
            ttl_sec: Time-to-live in seconds.

        Returns:
            bool: True if result has expired.
        """
        return time.time() - self.created_at > ttl_sec

    def elapsed_ms(self) -> float:
        """Get elapsed time since creation in milliseconds.

        Returns:
            float: Elapsed milliseconds.
        """
        end_time = self.completed_at or time.time()
        return (end_time - self.created_at) * 1000


@dataclass
class StreamingSession:
    """Manages a single streaming session with result caching."""

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    """Unique session identifier."""

    created_at: float = field(default_factory=time.time)
    """Session creation timestamp."""

    last_activity: float = field(default_factory=time.time)
    """Timestamp of last activity (frame posted or polled)."""

    config: Optional[Any] = None
    """ProcessConfig instance for this session."""

    result_cache: dict[int, ProcessingResult] = field(default_factory=dict)
    """Cache of processing results keyed by frame_id."""

    frame_buffer: list[tuple[int, np.ndarray]] = field(default_factory=list)
    """Buffer of queued frames (frame_id, image_data)."""

    metrics_accumulator: dict[str, list] = field(default_factory=lambda: {
        "inpaint_quality": [],
        "boundary_smoothness": [],
        "temporal_consistency": [],
        "processing_time_ms": [],
    })
    """Accumulated metrics across all frames in session."""

    checkpoint_state: dict[str, Any] = field(default_factory=dict)
    """State saved during session for resumption."""

    frame_count: int = 0
    """Total frames posted to this session."""

    processing_errors: int = 0
    """Count of frames that failed processing."""

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = time.time()

    def is_inactive(self, timeout_sec: int) -> bool:
        """Check if session has been inactive for timeout duration.

        Args:
            timeout_sec: Inactivity timeout in seconds.

        Returns:
            bool: True if session inactive.
        """
        return time.time() - self.last_activity > timeout_sec

    def cache_result(self, result: ProcessingResult) -> None:
        """Cache a processing result.

        Args:
            result: ProcessingResult to cache.
        """
        self.result_cache[result.frame_id] = result
        self.update_activity()

    def get_result(self, frame_id: int, ttl_sec: int) -> Optional[ProcessingResult]:
        """Retrieve a cached result if available and not expired.

        Args:
            frame_id: Frame identifier.
            ttl_sec: Time-to-live in seconds.

        Returns:
            ProcessingResult or None if not found or expired.
        """
        if frame_id not in self.result_cache:
            return None
        result = self.result_cache[frame_id]
        if result.is_expired(ttl_sec):
            del self.result_cache[frame_id]
            return None
        self.update_activity()
        return result

    def expire_old_results(self, ttl_sec: int) -> int:
        """Remove expired results from cache.

        Args:
            ttl_sec: Time-to-live in seconds.

        Returns:
            int: Number of results removed.
        """
        expired_ids = [
            frame_id for frame_id, result in self.result_cache.items()
            if result.is_expired(ttl_sec)
        ]
        for frame_id in expired_ids:
            del self.result_cache[frame_id]
        return len(expired_ids)

    def add_metric(self, metric_name: str, value: float) -> None:
        """Add a metric value to accumulator.

        Args:
            metric_name: Name of the metric.
            value: Metric value.
        """
        if metric_name not in self.metrics_accumulator:
            self.metrics_accumulator[metric_name] = []
        self.metrics_accumulator[metric_name].append(value)

    def get_metrics_summary(self) -> dict[str, float]:
        """Get summary statistics for accumulated metrics.

        Returns:
            dict: Metric names mapped to mean values, or 0 if no samples.
        """
        summary = {}
        for metric_name, values in self.metrics_accumulator.items():
            if values:
                summary[metric_name] = float(np.mean(values))
            else:
                summary[metric_name] = 0.0
        return summary

    def save_checkpoint(self, checkpoint_path: Path) -> None:
        """Save session checkpoint to file.

        Args:
            checkpoint_path: Path to save checkpoint JSON.
        """
        import json
        checkpoint_data = {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "frame_count": self.frame_count,
            "metrics": self.get_metrics_summary(),
            "processing_errors": self.processing_errors,
        }
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        with open(checkpoint_path, "w") as f:
            json.dump(checkpoint_data, f, indent=2)
        logger.info(f"Checkpoint saved to {checkpoint_path}")

    def load_checkpoint(self, checkpoint_path: Path) -> bool:
        """Load session checkpoint from file.

        Args:
            checkpoint_path: Path to load checkpoint JSON.

        Returns:
            bool: True if checkpoint loaded successfully.
        """
        if not checkpoint_path.exists():
            return False
        try:
            import json
            with open(checkpoint_path, "r") as f:
                data = json.load(f)
            self.session_id = data.get("session_id", self.session_id)
            self.frame_count = data.get("frame_count", 0)
            self.processing_errors = data.get("processing_errors", 0)
            logger.info(f"Checkpoint loaded from {checkpoint_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return False


class SessionManager:
    """Manages collection of streaming sessions."""

    def __init__(self, session_timeout_sec: int = 600) -> None:
        """Initialize session manager.

        Args:
            session_timeout_sec: Timeout for inactive sessions (default 10 min).
        """
        self.sessions: dict[str, StreamingSession] = {}
        self.session_timeout_sec = session_timeout_sec
        logger.info(f"SessionManager initialized with {session_timeout_sec}s timeout")

    def create_session(self, config: Optional[Any] = None) -> StreamingSession:
        """Create a new streaming session.

        Args:
            config: Optional ProcessConfig for this session.

        Returns:
            StreamingSession: New session instance.
        """
        session = StreamingSession(config=config)
        self.sessions[session.session_id] = session
        logger.info(f"Created session {session.session_id}")
        return session

    def get_session(self, session_id: str) -> Optional[StreamingSession]:
        """Retrieve a session by ID.

        Args:
            session_id: Session identifier.

        Returns:
            StreamingSession or None if not found.
        """
        return self.sessions.get(session_id)

    def cleanup_inactive_sessions(self) -> int:
        """Remove sessions that have timed out.

        Returns:
            int: Number of sessions removed.
        """
        inactive_ids = [
            session_id for session_id, session in self.sessions.items()
            if session.is_inactive(self.session_timeout_sec)
        ]
        for session_id in inactive_ids:
            logger.info(f"Cleaning up inactive session {session_id}")
            del self.sessions[session_id]
        return len(inactive_ids)

    def get_session_count(self) -> int:
        """Get current number of active sessions.

        Returns:
            int: Active session count.
        """
        return len(self.sessions)
