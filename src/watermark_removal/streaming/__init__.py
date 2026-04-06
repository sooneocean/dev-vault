"""Streaming server and session management for watermark removal."""

from .session_manager import StreamingSession, SessionManager
from .queue_processor import BackgroundTaskRunner

__all__ = ["StreamingSession", "SessionManager", "BackgroundTaskRunner", "create_app"]


def create_app(*args, **kwargs):
    """Lazy import create_app to avoid cv2 dependency at module load time."""
    from .server import create_app as _create_app
    return _create_app(*args, **kwargs)
