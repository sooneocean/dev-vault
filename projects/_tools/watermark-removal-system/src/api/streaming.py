"""
Streaming API endpoint for real-time frame processing.

Provides WebSocket-based streaming with frame buffers, live statistics,
and configurable quality presets.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Optional, Callable
from contextlib import asynccontextmanager

from fastapi import APIRouter, WebSocket, HTTPException, Depends
from fastapi.responses import JSONResponse

from src.api.models import (
    StreamingSessionRequest,
    StreamingSessionResponse,
    SessionStatusResponse,
    StreamingStatsMessage,
    StreamingErrorResponse,
    FrameStatistics,
)
from src.queue.frame_buffer import FrameBuffer, Frame, FrameQueue
import numpy as np

logger = logging.getLogger(__name__)

# Session management
class StreamingSession:
    """Manages a single streaming session with frame buffer and statistics."""

    def __init__(
        self,
        session_id: str,
        config: StreamingSessionRequest,
    ):
        self.session_id = session_id
        self.config = config
        self.buffer = FrameBuffer(
            max_size=config.buffer_size,
            overflow_policy="drop",
        )
        self.queue = FrameQueue(
            buffer_size=config.buffer_size,
            overflow_policy="drop",
        )

        self.created_at = datetime.utcnow()
        self.status = "active"
        self.frame_count = 0
        self.error_count = 0
        self.processing_times = []
        self.gpu_utilization = 0.0

        logger.info(f"Session {session_id} created: {config.source_url}")

    async def add_frame(
        self,
        image: np.ndarray,
        processing_time_ms: float = 0.0,
    ) -> bool:
        """
        Add processed frame to session buffer.

        Args:
            image: Processed frame (BGR ndarray)
            processing_time_ms: Time spent processing this frame

        Returns:
            True if added, False if dropped due to buffer full
        """
        frame = Frame(
            frame_id=self.frame_count,
            image=image,
            timestamp_ms=float((datetime.utcnow() - self.created_at).total_seconds() * 1000),
            sequence=self.frame_count,
        )

        self.frame_count += 1
        self.processing_times.append(processing_time_ms)
        if len(self.processing_times) > 1000:
            self.processing_times = self.processing_times[-500:]

        return await self.buffer.put(frame)

    def get_stats(self) -> dict:
        """Get current session statistics."""
        uptime_sec = (datetime.utcnow() - self.created_at).total_seconds()
        avg_processing_ms = (
            sum(self.processing_times) / len(self.processing_times)
            if self.processing_times
            else 0.0
        )
        avg_fps = self.frame_count / uptime_sec if uptime_sec > 0 else 0.0

        buffer_stats = self.buffer.stats()

        return {
            "session_id": self.session_id,
            "status": self.status,
            "uptime_sec": uptime_sec,
            "frames_processed": self.frame_count,
            "frames_dropped": buffer_stats["frames_dropped"],
            "avg_fps": avg_fps,
            "errors": self.error_count,
            "queue_depth": buffer_stats["queue_depth"],
            "avg_processing_time_ms": avg_processing_ms,
        }

    async def close(self):
        """Close session and clean up resources."""
        self.status = "stopped"
        await self.buffer.clear()
        logger.info(f"Session {self.session_id} closed")


class StreamingSessionManager:
    """Manages active streaming sessions."""

    def __init__(self):
        self.sessions: Dict[str, StreamingSession] = {}
        self.lock = asyncio.Lock()

    async def create_session(self, config: StreamingSessionRequest) -> StreamingSession:
        """Create new streaming session."""
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        session = StreamingSession(session_id, config)

        async with self.lock:
            self.sessions[session_id] = session

        return session

    async def get_session(self, session_id: str) -> Optional[StreamingSession]:
        """Get session by ID."""
        async with self.lock:
            return self.sessions.get(session_id)

    async def close_session(self, session_id: str) -> bool:
        """Close and remove session."""
        async with self.lock:
            if session_id in self.sessions:
                await self.sessions[session_id].close()
                del self.sessions[session_id]
                return True
        return False

    async def get_all_sessions(self) -> Dict[str, StreamingSession]:
        """Get all active sessions."""
        async with self.lock:
            return dict(self.sessions)


# Global session manager
session_manager = StreamingSessionManager()

# Router
router = APIRouter(prefix="/stream", tags=["streaming"])


@router.post("/start", response_model=StreamingSessionResponse)
async def start_streaming(request: StreamingSessionRequest):
    """
    Start a new streaming session.

    Args:
        request: StreamingSessionRequest with source URL and config

    Returns:
        StreamingSessionResponse with session details
    """
    try:
        session = await session_manager.create_session(request)

        return StreamingSessionResponse(
            session_id=session.session_id,
            status="active",
            stream_url=f"ws://localhost:8000/stream/{session.session_id}",
            stats_url=f"ws://localhost:8000/stats/{session.session_id}",
            created_at=session.created_at.isoformat() + "Z",
        )
    except Exception as e:
        logger.error(f"Error starting streaming session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(session_id: str):
    """
    Get status of streaming session.

    Args:
        session_id: Session ID to query

    Returns:
        SessionStatusResponse with metrics
    """
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    stats = session.get_stats()
    return SessionStatusResponse(**stats)


@router.websocket("/ws/{session_id}")
async def websocket_stream(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for streaming frames.

    Receives frame data and streams processed output.
    """
    session = await session_manager.get_session(session_id)
    if not session:
        await websocket.close(code=4004, reason="Session not found")
        return

    await websocket.accept()
    logger.info(f"WebSocket connected for session {session_id}")

    try:
        while session.status == "active":
            try:
                # Receive frame data from client
                # In production, this would receive actual frame bytes
                # For now, simulate frame reception
                data = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)

                if data.get("type") == "frame":
                    # In production, decode frame data
                    # For now, create dummy frame
                    dummy_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
                    await session.add_frame(
                        dummy_frame,
                        processing_time_ms=data.get("processing_time_ms", 0.0),
                    )

                    # Send acknowledgement
                    await websocket.send_json(
                        {
                            "type": "ack",
                            "frame_id": session.frame_count - 1,
                            "queue_depth": session.buffer.size(),
                        }
                    )

            except asyncio.TimeoutError:
                # No data received, check for buffered frames to send
                frame = await session.buffer.get_nowait()
                if frame:
                    # Send frame to client
                    await websocket.send_json(
                        {
                            "type": "frame",
                            "frame_id": frame.frame_id,
                            "timestamp_ms": frame.timestamp_ms,
                            "shape": frame.image.shape,
                        }
                    )

            except Exception as e:
                logger.error(f"Error in stream {session_id}: {e}")
                session.error_count += 1
                await websocket.send_json(
                    {
                        "type": "error",
                        "error": str(e),
                        "error_code": "FRAME_PROCESSING_ERROR",
                    }
                )

    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
    finally:
        await websocket.close()
        logger.info(f"WebSocket disconnected for session {session_id}")


@router.websocket("/stats/{session_id}")
async def websocket_stats(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for live statistics streaming.

    Sends frame statistics and performance metrics in real-time.
    """
    session = await session_manager.get_session(session_id)
    if not session:
        await websocket.close(code=4004, reason="Session not found")
        return

    await websocket.accept()
    logger.info(f"Stats WebSocket connected for session {session_id}")

    try:
        while session.status == "active":
            try:
                # Send statistics every 100ms
                await asyncio.sleep(0.1)

                stats = session.get_stats()

                # Create frame statistics message
                frame_stat = FrameStatistics(
                    frame_id=session.frame_count,
                    timestamp_ms=float(
                        (datetime.utcnow() - session.created_at).total_seconds() * 1000
                    ),
                    processing_time_ms=(
                        session.processing_times[-1]
                        if session.processing_times
                        else 0.0
                    ),
                    gpu_utilization_pct=session.gpu_utilization,
                    queue_depth=stats["queue_depth"],
                    fps=stats["avg_fps"],
                    status="processing" if session.status == "active" else "completed",
                )

                # Send as StreamingStatsMessage
                msg = StreamingStatsMessage(
                    event_type="frame_processed",
                    data={
                        "frame_id": frame_stat.frame_id,
                        "timestamp_ms": frame_stat.timestamp_ms,
                        "processing_time_ms": frame_stat.processing_time_ms,
                        "gpu_utilization_pct": frame_stat.gpu_utilization_pct,
                        "queue_depth": frame_stat.queue_depth,
                        "fps": frame_stat.fps,
                        "status": frame_stat.status,
                    },
                    timestamp=datetime.utcnow().isoformat() + "Z",
                )

                await websocket.send_json(msg.dict())

            except Exception as e:
                logger.error(f"Error sending stats for {session_id}: {e}")
                await websocket.send_json(
                    {
                        "event_type": "error",
                        "data": {"error": str(e)},
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                    }
                )

    except Exception as e:
        logger.error(f"Stats WebSocket error for session {session_id}: {e}")
    finally:
        await websocket.close()
        logger.info(f"Stats WebSocket disconnected for session {session_id}")


@router.post("/{session_id}/stop", response_model=dict)
async def stop_streaming(session_id: str):
    """
    Stop a streaming session.

    Args:
        session_id: Session to stop

    Returns:
        Confirmation with final statistics
    """
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    stats = session.get_stats()
    await session_manager.close_session(session_id)

    return {
        "session_id": session_id,
        "status": "stopped",
        "final_stats": stats,
    }


@router.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    sessions = await session_manager.get_all_sessions()
    return {
        "status": "healthy",
        "active_sessions": len(sessions),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
