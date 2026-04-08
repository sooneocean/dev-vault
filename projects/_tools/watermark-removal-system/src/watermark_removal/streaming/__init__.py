"""
Streaming module for real-time watermark removal.

Provides async session management, background processing queue, and FastAPI server.
"""

from .session_manager import SessionManager, StreamingSession, FrameResult
from .queue_processor import BackgroundTaskRunner
from .server import app

__all__ = [
    "SessionManager",
    "StreamingSession",
    "FrameResult",
    "BackgroundTaskRunner",
    "app",
]
