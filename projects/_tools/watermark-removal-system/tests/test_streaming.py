"""
Tests for streaming module (Unit 23).

Covers:
- SessionManager lifecycle and TTL expiration
- BackgroundTaskRunner queue processing
- FastAPI endpoint integration
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

from src.watermark_removal.streaming.session_manager import (
    SessionManager,
    StreamingSession,
    FrameResult,
)
from src.watermark_removal.streaming.queue_processor import BackgroundTaskRunner
from src.watermark_removal.core.types import ProcessConfig


@pytest.fixture
def process_config():
    """Fixture: minimal ProcessConfig for testing."""
    return ProcessConfig(
        video_path=Path("/tmp/test.mp4"),
        mask_path=Path("/tmp/test_mask.mp4"),
        output_dir=Path("/tmp/output"),
    )


@pytest.fixture
async def session_manager():
    """Fixture: SessionManager instance."""
    return SessionManager(result_ttl_sec=300, session_ttl_sec=600)


class TestSessionManager:
    """Tests for SessionManager class."""

    @pytest.mark.asyncio
    async def test_create_session(self, session_manager, process_config):
        """Test session creation."""
        session_id = await session_manager.create_session(process_config)

        assert session_id is not None
        assert len(session_id) > 0

    @pytest.mark.asyncio
    async def test_get_session(self, session_manager, process_config):
        """Test session retrieval."""
        session_id = await session_manager.create_session(process_config)
        session = await session_manager.get_session(session_id)

        assert session is not None
        assert session.session_id == session_id
        assert session.config == process_config

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, session_manager):
        """Test retrieving non-existent session returns None."""
        session = await session_manager.get_session("nonexistent_id")

        assert session is None

    @pytest.mark.asyncio
    async def test_end_session(self, session_manager, process_config):
        """Test session termination."""
        session_id = await session_manager.create_session(process_config)
        summary = await session_manager.end_session(session_id)

        assert summary is not None
        assert summary["session_id"] == session_id

    @pytest.mark.asyncio
    async def test_session_expiration(self, process_config):
        """Test TTL-based session expiration."""
        manager = SessionManager(result_ttl_sec=300, session_ttl_sec=1)
        session_id = await manager.create_session(process_config)

        # Session should exist immediately
        session = await manager.get_session(session_id)
        assert session is not None

        # Wait for expiration
        await asyncio.sleep(1.5)

        # Session should be expired and removed
        session = await manager.get_session(session_id)
        assert session is None

    @pytest.mark.asyncio
    async def test_get_active_session_count(self, session_manager, process_config):
        """Test active session count."""
        initial_count = await session_manager.get_active_session_count()
        assert initial_count == 0

        session_id_1 = await session_manager.create_session(process_config)
        count = await session_manager.get_active_session_count()
        assert count == 1

        session_id_2 = await session_manager.create_session(process_config)
        count = await session_manager.get_active_session_count()
        assert count == 2

        await session_manager.end_session(session_id_1)
        count = await session_manager.get_active_session_count()
        assert count == 1


class TestStreamingSession:
    """Tests for StreamingSession class."""

    def test_frame_result_add_and_retrieve(self, process_config):
        """Test adding and retrieving frame results."""
        session = StreamingSession(session_id="test_id", config=process_config)

        result = FrameResult(
            frame_id=0,
            status="completed",
            metrics={"time_ms": 100},
        )

        session.add_frame_result(0, result)
        retrieved = session.get_frame_result(0)

        assert retrieved is not None
        assert retrieved.frame_id == 0
        assert retrieved.status == "completed"

    def test_session_expiration(self, process_config):
        """Test session TTL expiration."""
        session = StreamingSession(session_id="test_id", config=process_config)

        # Session should not be expired immediately
        assert not session.is_expired(ttl_sec=60)

        # Manually set last_activity to past
        session.last_activity = datetime.now() - timedelta(seconds=61)

        # Session should now be expired
        assert session.is_expired(ttl_sec=60)

    def test_session_serialization(self, process_config):
        """Test session to_dict() serialization."""
        session = StreamingSession(session_id="test_id", config=process_config)

        result = FrameResult(frame_id=0, status="completed", metrics={"time": 100})
        session.add_frame_result(0, result)

        data = session.to_dict()

        assert data["session_id"] == "test_id"
        assert data["frame_count"] == 1
        assert data["error_count"] == 0


class TestBackgroundTaskRunner:
    """Tests for BackgroundTaskRunner class."""

    @pytest.mark.asyncio
    async def test_runner_initialization(self, process_config):
        """Test BackgroundTaskRunner initialization."""
        session = StreamingSession(session_id="test_id", config=process_config)
        runner = BackgroundTaskRunner(session=session, max_queue_size=100)

        assert runner.session == session
        assert await runner.get_queue_size() == 0

    @pytest.mark.asyncio
    async def test_submit_and_process_frame(self, process_config):
        """Test submitting a frame to the runner."""
        session = StreamingSession(session_id="test_id", config=process_config)
        runner = BackgroundTaskRunner(session=session, max_queue_size=100)

        await runner.start()

        try:
            # Submit a frame (minimal dummy data)
            frame_data = b"\x89PNG\r\n\x1a\n"  # PNG header

            queued = await runner.submit_frame(frame_id=0, frame_data=frame_data)
            assert queued is True

            # Check queue size
            queue_size = await runner.get_queue_size()
            assert queue_size > 0

        finally:
            await runner.stop()

    @pytest.mark.asyncio
    async def test_queue_backpressure(self, process_config):
        """Test queue backpressure when full."""
        session = StreamingSession(session_id="test_id", config=process_config)
        runner = BackgroundTaskRunner(session=session, max_queue_size=2)

        await runner.start()

        try:
            # Fill the queue
            frame_data = b"fake_frame_data"

            assert await runner.submit_frame(frame_id=0, frame_data=frame_data) is True
            assert await runner.submit_frame(frame_id=1, frame_data=frame_data) is True

            # Queue is full, next submit should fail
            assert await runner.submit_frame(frame_id=2, frame_data=frame_data) is False

        finally:
            await runner.stop()

    @pytest.mark.asyncio
    async def test_wait_all_done(self, process_config):
        """Test waiting for all queued frames to complete."""
        session = StreamingSession(session_id="test_id", config=process_config)
        runner = BackgroundTaskRunner(session=session, max_queue_size=100)

        await runner.start()

        try:
            # No frames queued, should complete immediately
            done = await runner.wait_all_done(timeout_sec=1.0)
            assert done is True

        finally:
            await runner.stop()


class TestFrameResult:
    """Tests for FrameResult dataclass."""

    def test_frame_result_creation(self):
        """Test FrameResult instantiation."""
        result = FrameResult(
            frame_id=42,
            status="processing",
            metrics={"latency_ms": 150},
        )

        assert result.frame_id == 42
        assert result.status == "processing"
        assert result.metrics["latency_ms"] == 150

    def test_frame_result_default_timestamp(self):
        """Test FrameResult has default timestamp."""
        before = datetime.now()
        result = FrameResult(frame_id=0, status="pending")
        after = datetime.now()

        assert before <= result.timestamp <= after

    def test_frame_result_with_error(self):
        """Test FrameResult with error state."""
        result = FrameResult(
            frame_id=0,
            status="error",
            error_message="Decode failed: invalid PNG",
        )

        assert result.status == "error"
        assert "invalid PNG" in result.error_message


# FastAPI endpoint tests (requires test client)
@pytest.mark.asyncio
async def test_fastapi_health_endpoint():
    """Test /health endpoint."""
    pytest.importorskip("fastapi.testclient")

    from fastapi.testclient import TestClient
    from src.watermark_removal.streaming.server import app

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "active_sessions" in data


@pytest.mark.asyncio
async def test_fastapi_stream_start_endpoint():
    """Test /stream/start endpoint."""
    pytest.importorskip("fastapi.testclient")

    from fastapi.testclient import TestClient
    from src.watermark_removal.streaming.server import app

    client = TestClient(app)
    response = client.post(
        "/stream/start", json={}, headers={"X-API-Key": "sk-test-watermark-removal-phase-3"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["status"] == "active"
