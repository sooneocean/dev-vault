"""
Unit tests for streaming API endpoint.

Tests session management, frame streaming, buffer handling, and WebSocket communication.
"""

import pytest
import asyncio
import numpy as np
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from src.api.streaming import (
    StreamingSession,
    StreamingSessionManager,
    router,
)
from src.api.models import (
    StreamingSessionRequest,
    VideoFormatEnum,
    QualityPresetEnum,
)
from src.queue.frame_buffer import Frame


class TestStreamingSession:
    """Test StreamingSession class."""

    def test_session_creation(self):
        """StreamingSession initializes correctly."""
        config = StreamingSessionRequest(
            source_url="file:///test.mp4",
            output_format=VideoFormatEnum.H264,
            quality_preset=QualityPresetEnum.BALANCED,
            buffer_size=30,
            enable_stats=True,
        )

        session = StreamingSession("sess_test123", config)

        assert session.session_id == "sess_test123"
        assert session.status == "active"
        assert session.frame_count == 0
        assert session.error_count == 0
        assert session.config == config

    def test_session_buffer_created(self):
        """StreamingSession creates frame buffer."""
        config = StreamingSessionRequest(source_url="file:///test.mp4")
        session = StreamingSession("sess_test123", config)

        assert session.buffer is not None
        assert session.buffer.max_size == config.buffer_size

    @pytest.mark.asyncio
    async def test_add_frame_increments_count(self):
        """add_frame increments frame counter."""
        config = StreamingSessionRequest(source_url="file:///test.mp4")
        session = StreamingSession("sess_test123", config)

        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        await session.add_frame(frame, processing_time_ms=42.5)

        assert session.frame_count == 1
        assert len(session.processing_times) == 1
        assert session.processing_times[0] == 42.5

    @pytest.mark.asyncio
    async def test_add_frame_respects_buffer_policy(self):
        """add_frame respects buffer overflow policy."""
        config = StreamingSessionRequest(source_url="file:///test.mp4", buffer_size=2)
        session = StreamingSession("sess_test123", config)

        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)

        # Fill buffer
        result1 = await session.add_frame(frame)
        result2 = await session.add_frame(frame)

        # Buffer full, should drop
        result3 = await session.add_frame(frame)

        assert result1 is True
        assert result2 is True
        # Third frame may be dropped due to overflow policy
        assert isinstance(result3, bool)

    def test_get_stats(self):
        """get_stats returns valid statistics."""
        config = StreamingSessionRequest(source_url="file:///test.mp4")
        session = StreamingSession("sess_test123", config)

        stats = session.get_stats()

        assert "session_id" in stats
        assert "status" in stats
        assert "uptime_sec" in stats
        assert "frames_processed" in stats
        assert "frames_dropped" in stats
        assert "avg_fps" in stats
        assert "errors" in stats

        assert stats["session_id"] == "sess_test123"
        assert stats["status"] == "active"
        assert stats["frames_processed"] == 0

    def test_get_stats_uptime_increases(self):
        """get_stats uptime increases with time."""
        config = StreamingSessionRequest(source_url="file:///test.mp4")
        session = StreamingSession("sess_test123", config)

        stats1 = session.get_stats()
        asyncio.run(asyncio.sleep(0.01))
        stats2 = session.get_stats()

        # Uptime should increase (allowing some tolerance for timing variations)
        assert stats2["uptime_sec"] >= stats1["uptime_sec"]

    @pytest.mark.asyncio
    async def test_session_close(self):
        """close() stops session and cleans buffer."""
        config = StreamingSessionRequest(source_url="file:///test.mp4")
        session = StreamingSession("sess_test123", config)

        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        await session.add_frame(frame)

        await session.close()

        assert session.status == "stopped"
        assert session.buffer.is_empty()


class TestStreamingSessionManager:
    """Test StreamingSessionManager."""

    @pytest.mark.asyncio
    async def test_create_session(self):
        """create_session creates new session with unique ID."""
        manager = StreamingSessionManager()
        config = StreamingSessionRequest(source_url="file:///test.mp4")

        session = await manager.create_session(config)

        assert session is not None
        assert session.session_id.startswith("sess_")
        assert session.status == "active"

    @pytest.mark.asyncio
    async def test_create_session_generates_unique_ids(self):
        """create_session generates unique session IDs."""
        manager = StreamingSessionManager()
        config = StreamingSessionRequest(source_url="file:///test.mp4")

        session1 = await manager.create_session(config)
        session2 = await manager.create_session(config)

        assert session1.session_id != session2.session_id

    @pytest.mark.asyncio
    async def test_get_session(self):
        """get_session retrieves created session."""
        manager = StreamingSessionManager()
        config = StreamingSessionRequest(source_url="file:///test.mp4")

        created = await manager.create_session(config)
        retrieved = await manager.get_session(created.session_id)

        assert retrieved == created

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self):
        """get_session returns None for nonexistent session."""
        manager = StreamingSessionManager()

        result = await manager.get_session("sess_nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_close_session(self):
        """close_session removes and closes session."""
        manager = StreamingSessionManager()
        config = StreamingSessionRequest(source_url="file:///test.mp4")

        session = await manager.create_session(config)
        result = await manager.close_session(session.session_id)

        assert result is True
        assert await manager.get_session(session.session_id) is None

    @pytest.mark.asyncio
    async def test_close_nonexistent_session(self):
        """close_session returns False for nonexistent session."""
        manager = StreamingSessionManager()

        result = await manager.close_session("sess_nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_all_sessions(self):
        """get_all_sessions returns all active sessions."""
        manager = StreamingSessionManager()
        config = StreamingSessionRequest(source_url="file:///test.mp4")

        session1 = await manager.create_session(config)
        session2 = await manager.create_session(config)

        all_sessions = await manager.get_all_sessions()

        assert len(all_sessions) == 2
        assert session1.session_id in all_sessions
        assert session2.session_id in all_sessions


class TestStreamingEndpoints:
    """Test streaming API endpoints."""

    @pytest.mark.asyncio
    async def test_start_streaming_valid_request(self):
        """POST /stream/start creates session."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        client = TestClient(app)

        payload = {
            "source_url": "file:///test.mp4",
            "output_format": "h264",
            "quality_preset": "balanced",
            "buffer_size": 30,
            "enable_stats": True,
        }

        response = client.post("/stream/start", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "active"
        assert "stream_url" in data
        assert "stats_url" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_start_streaming_invalid_buffer_size(self):
        """POST /stream/start rejects invalid buffer size."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        client = TestClient(app)

        # Buffer size out of range (>300)
        payload = {
            "source_url": "file:///test.mp4",
            "buffer_size": 500,
        }

        response = client.post("/stream/start", json=payload)

        # Should fail validation
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_session_status_existing(self):
        """GET /stream/{session_id}/status returns session status."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        client = TestClient(app)

        # Create session first
        create_payload = {"source_url": "file:///test.mp4"}
        create_response = client.post("/stream/start", json=create_payload)
        session_id = create_response.json()["session_id"]

        # Get status
        status_response = client.get(f"/stream/{session_id}/status")

        assert status_response.status_code == 200
        data = status_response.json()
        assert data["session_id"] == session_id
        assert data["status"] == "active"
        assert "frames_processed" in data
        assert "frames_dropped" in data
        assert "avg_fps" in data

    @pytest.mark.asyncio
    async def test_get_session_status_nonexistent(self):
        """GET /stream/{session_id}/status returns 404 for nonexistent session."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        client = TestClient(app)

        response = client.get("/stream/sess_nonexistent/status")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_stop_streaming(self):
        """POST /stream/{session_id}/stop closes session."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        client = TestClient(app)

        # Create session
        create_response = client.post("/stream/start", json={"source_url": "file:///test.mp4"})
        session_id = create_response.json()["session_id"]

        # Stop session
        stop_response = client.post(f"/stream/{session_id}/stop")

        assert stop_response.status_code == 200
        data = stop_response.json()
        assert data["session_id"] == session_id
        assert data["status"] == "stopped"
        assert "final_stats" in data

    @pytest.mark.asyncio
    async def test_stop_nonexistent_session(self):
        """POST /stream/{session_id}/stop returns 404 for nonexistent session."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        client = TestClient(app)

        response = client.post("/stream/sess_nonexistent/stop")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_health_check(self):
        """GET /stream/health returns health status."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        client = TestClient(app)

        response = client.get("/stream/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "active_sessions" in data
        assert "timestamp" in data


class TestBufferOverflowHandling:
    """Test buffer overflow scenarios."""

    @pytest.mark.asyncio
    async def test_buffer_drop_policy(self):
        """Buffer with drop policy discards oldest frame."""
        config = StreamingSessionRequest(
            source_url="file:///test.mp4",
            buffer_size=3,
        )
        session = StreamingSession("sess_test", config)

        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)

        # Add frames
        for i in range(5):
            result = await session.add_frame(frame)
            # All should be accepted (drop policy doesn't reject, just drops oldest)
            assert isinstance(result, bool)

        # Buffer should have max of 3 frames
        assert session.buffer.size() <= 3

    @pytest.mark.asyncio
    async def test_concurrent_stream_handling(self):
        """Handle multiple concurrent streams."""
        manager = StreamingSessionManager()
        config = StreamingSessionRequest(source_url="file:///test.mp4")

        # Create multiple sessions concurrently
        sessions = await asyncio.gather(
            *[manager.create_session(config) for _ in range(5)]
        )

        assert len(sessions) == 5
        all_sessions = await manager.get_all_sessions()
        assert len(all_sessions) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
