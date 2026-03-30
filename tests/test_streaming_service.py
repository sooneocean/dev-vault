"""Tests for FastAPI streaming service (Unit 23)."""

import asyncio
import base64
import json
import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from src.watermark_removal.streaming.server import create_app
from src.watermark_removal.streaming.queue_processor import BackgroundTaskRunner
from src.watermark_removal.streaming.session_manager import (
    StreamingSession,
    SessionManager,
    ProcessingResult,
)
from src.watermark_removal.core.types import ProcessConfig

logger = logging.getLogger(__name__)


# ============================================================================
# UNIT TESTS: Session Management (8 tests)
# ============================================================================


class TestStreamingSession:
    """Unit tests for StreamingSession dataclass."""

    def test_session_creation(self):
        """Happy path: create new session."""
        session = StreamingSession()
        assert session.session_id
        assert session.created_at > 0
        assert session.last_activity == session.created_at
        assert len(session.result_cache) == 0
        assert session.frame_count == 0

    def test_session_with_config(self):
        """Happy path: create session with config."""
        config = ProcessConfig(
            video_path="/tmp/test.mp4",
            mask_path="/tmp/mask.png",
            output_dir="/tmp/output",
        )
        session = StreamingSession(config=config)
        assert session.config == config

    def test_cache_result(self):
        """Happy path: cache and retrieve result."""
        session = StreamingSession()
        result = ProcessingResult(
            frame_id=0,
            session_id=session.session_id,
            status="completed",
            output_frame=np.zeros((480, 640, 3), dtype=np.uint8),
            metrics={"quality": 0.95},
        )
        session.cache_result(result)
        assert 0 in session.result_cache
        assert session.result_cache[0].status == "completed"

    def test_get_result_not_expired(self):
        """Happy path: retrieve non-expired result."""
        session = StreamingSession()
        result = ProcessingResult(
            frame_id=0,
            session_id=session.session_id,
            status="completed",
        )
        session.cache_result(result)
        retrieved = session.get_result(0, ttl_sec=300)
        assert retrieved is not None
        assert retrieved.frame_id == 0

    def test_get_result_expired(self):
        """Edge case: expired result returns None."""
        session = StreamingSession()
        result = ProcessingResult(
            frame_id=0,
            session_id=session.session_id,
            status="completed",
        )
        session.cache_result(result)
        # Simulate expiration by reducing TTL
        retrieved = session.get_result(0, ttl_sec=0)  # Expired immediately
        assert retrieved is None

    def test_metrics_accumulation(self):
        """Happy path: accumulate and summarize metrics."""
        session = StreamingSession()
        session.add_metric("quality", 0.95)
        session.add_metric("quality", 0.92)
        session.add_metric("quality", 0.98)
        summary = session.get_metrics_summary()
        assert "quality" in summary
        assert abs(summary["quality"] - 0.95) < 0.01  # Mean of 0.95, 0.92, 0.98

    def test_session_inactivity(self):
        """Edge case: session inactivity timeout detection."""
        session = StreamingSession()
        # Should not be inactive immediately
        assert not session.is_inactive(timeout_sec=600)
        # Manually set last_activity to simulate timeout
        session.last_activity = 0
        assert session.is_inactive(timeout_sec=600)

    def test_checkpoint_save_and_load(self, tmp_path):
        """Integration: checkpoint persistence."""
        session = StreamingSession()
        session.frame_count = 50
        session.processing_errors = 2
        session.add_metric("quality", 0.95)
        checkpoint_path = tmp_path / "checkpoint.json"
        session.save_checkpoint(checkpoint_path)
        assert checkpoint_path.exists()
        # Load and verify
        session2 = StreamingSession()
        assert session2.load_checkpoint(checkpoint_path)
        assert session2.frame_count == 50


# ============================================================================
# UNIT TESTS: Session Manager (8 tests)
# ============================================================================


class TestSessionManager:
    """Unit tests for SessionManager."""

    def test_session_manager_creation(self):
        """Happy path: create session manager."""
        manager = SessionManager()
        assert manager.get_session_count() == 0

    def test_create_session(self):
        """Happy path: create and retrieve session."""
        manager = SessionManager()
        session = manager.create_session()
        assert session.session_id
        retrieved = manager.get_session(session.session_id)
        assert retrieved == session

    def test_invalid_session_id(self):
        """Edge case: get non-existent session returns None."""
        manager = SessionManager()
        assert manager.get_session("invalid_id") is None

    def test_cleanup_inactive_sessions(self):
        """Edge case: cleanup removes inactive sessions."""
        manager = SessionManager(session_timeout_sec=0)  # Immediate timeout
        session = manager.create_session()
        # Mark as inactive
        session.last_activity = 0
        removed_count = manager.cleanup_inactive_sessions()
        assert removed_count == 1
        assert manager.get_session_count() == 0

    def test_multiple_sessions(self):
        """Happy path: manage multiple sessions independently."""
        manager = SessionManager()
        sessions = [manager.create_session() for _ in range(3)]
        assert manager.get_session_count() == 3
        assert all(manager.get_session(s.session_id) for s in sessions)

    def test_session_config_isolation(self):
        """Edge case: each session has independent config."""
        manager = SessionManager()
        config1 = ProcessConfig(
            video_path="/tmp/video1.mp4",
            mask_path="/tmp/mask1.png",
            output_dir="/tmp/out1",
        )
        config2 = ProcessConfig(
            video_path="/tmp/video2.mp4",
            mask_path="/tmp/mask2.png",
            output_dir="/tmp/out2",
        )
        s1 = manager.create_session(config1)
        s2 = manager.create_session(config2)
        assert s1.config.video_path == "/tmp/video1.mp4"
        assert s2.config.video_path == "/tmp/video2.mp4"

    def test_concurrent_sessions_isolated(self):
        """Integration: concurrent sessions don't interfere."""
        manager = SessionManager()
        s1 = manager.create_session()
        s2 = manager.create_session()
        # Add results to different sessions
        r1 = ProcessingResult(frame_id=0, session_id=s1.session_id, status="completed")
        r2 = ProcessingResult(frame_id=0, session_id=s2.session_id, status="completed")
        s1.cache_result(r1)
        s2.cache_result(r2)
        # Verify isolation
        assert s1.get_result(0, ttl_sec=300).session_id == s1.session_id
        assert s2.get_result(0, ttl_sec=300).session_id == s2.session_id


# ============================================================================
# UNIT TESTS: Background Task Runner (8 tests)
# ============================================================================


class TestBackgroundTaskRunner:
    """Unit tests for BackgroundTaskRunner."""

    @pytest.mark.asyncio
    async def test_runner_creation(self):
        """Happy path: create task runner."""
        async def dummy_process(frame, session):
            return frame, {}

        runner = BackgroundTaskRunner(dummy_process)
        assert runner.is_running is False
        assert runner.get_queue_depth() == 0

    @pytest.mark.asyncio
    async def test_start_and_stop(self):
        """Happy path: start and stop runner."""
        async def dummy_process(frame, session):
            return frame, {}

        runner = BackgroundTaskRunner(dummy_process)
        await runner.start()
        assert runner.is_running is True
        await runner.stop()
        assert runner.is_running is False

    @pytest.mark.asyncio
    async def test_enqueue_frame(self):
        """Happy path: enqueue frame for processing."""
        async def dummy_process(frame, session):
            return frame, {}

        runner = BackgroundTaskRunner(dummy_process)
        session = StreamingSession()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        success = await runner.enqueue_frame(session, 0, frame)
        assert success is True
        assert runner.get_queue_depth() == 1

    @pytest.mark.asyncio
    async def test_queue_full(self):
        """Edge case: queue full drops frames."""
        async def dummy_process(frame, session):
            await asyncio.sleep(10)  # Simulate slow processing
            return frame, {}

        runner = BackgroundTaskRunner(dummy_process, queue_size=1)
        await runner.start()
        session = StreamingSession()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # First frame succeeds
        success1 = await runner.enqueue_frame(session, 0, frame)
        assert success1 is True
        # Second frame fails (queue full)
        success2 = await runner.enqueue_frame(session, 1, frame)
        assert success2 is False
        await runner.stop()

    @pytest.mark.asyncio
    async def test_frame_processing_success(self):
        """Happy path: frame processes and result cached."""
        async def dummy_process(frame, session):
            await asyncio.sleep(0.01)
            return frame, {"quality": 0.95}

        runner = BackgroundTaskRunner(dummy_process)
        await runner.start()
        session = StreamingSession()
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        await runner.enqueue_frame(session, 0, frame)
        # Wait for processing
        await asyncio.sleep(0.1)
        result = session.get_result(0, ttl_sec=300)
        assert result is not None
        assert result.status == "completed"
        assert result.metrics.get("quality") == 0.95
        await runner.stop()

    @pytest.mark.asyncio
    async def test_frame_processing_error(self):
        """Error path: processing error caught and logged."""
        async def failing_process(frame, session):
            raise ValueError("Intentional test error")

        runner = BackgroundTaskRunner(failing_process)
        await runner.start()
        session = StreamingSession()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        await runner.enqueue_frame(session, 0, frame)
        await asyncio.sleep(0.1)
        result = session.get_result(0, ttl_sec=300)
        assert result is not None
        assert result.status == "error"
        assert "Intentional test error" in result.error_message
        await runner.stop()

    def test_get_stats(self):
        """Happy path: get runner statistics."""
        async def dummy_process(frame, session):
            return frame, {}

        runner = BackgroundTaskRunner(dummy_process)
        stats = runner.get_stats()
        assert "processed_count" in stats
        assert "error_count" in stats
        assert "queue_depth" in stats
        assert stats["is_running"] is False


# ============================================================================
# INTEGRATION TESTS: FastAPI Server (8 tests)
# ============================================================================


class TestFastAPIServer:
    """Integration tests for FastAPI streaming server."""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        app, _, _ = create_app(queue_size=100, result_ttl_sec=300)
        return TestClient(app)

    def test_health_check(self, client):
        """Happy path: health check endpoint returns status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "queue_depth" in data
        assert "active_sessions" in data

    def test_stream_start(self, client):
        """Happy path: POST /stream/start creates session."""
        response = client.post("/stream/start")
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "active"

    def test_stream_start_with_config(self, client):
        """Happy path: POST /stream/start with config."""
        config_data = {
            "video_path": "/tmp/test.mp4",
            "mask_path": "/tmp/mask.png",
            "output_dir": "/tmp/output",
            "streaming_queue_size": 50,
            "streaming_result_ttl_sec": 600,
        }
        response = client.post("/stream/start", json=config_data)
        assert response.status_code == 200

    def test_stream_frame_invalid_session(self, client):
        """Edge case: POST /stream/frame with invalid session_id returns 400."""
        # Create a dummy PNG file
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        _, png_data = cv2.imencode(".png", frame)
        response = client.post(
            "/stream/frame/invalid_session_id",
            files={"file": ("frame.png", png_data.tobytes(), "image/png")},
        )
        assert response.status_code == 400

    def test_stream_frame_valid_session(self, client):
        """Happy path: POST /stream/frame queues frame."""
        # Create session
        start_response = client.post("/stream/start")
        session_id = start_response.json()["session_id"]
        # Post frame
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        _, png_data = cv2.imencode(".png", frame)
        response = client.post(
            f"/stream/frame/{session_id}",
            files={"file": ("frame.png", png_data.tobytes(), "image/png")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "frame_id" in data
        assert data["session_id"] == session_id

    def test_stream_result_not_found(self, client):
        """Edge case: GET /stream/result with non-existent frame returns not_found."""
        start_response = client.post("/stream/start")
        session_id = start_response.json()["session_id"]
        response = client.get(f"/stream/result/{session_id}/999")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_found"

    def test_stream_stop(self, client):
        """Happy path: POST /stream/stop finalizes session and saves checkpoint."""
        start_response = client.post("/stream/start")
        session_id = start_response.json()["session_id"]
        response = client.post(f"/stream/stop/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert "metrics" in data
        assert "checkpoint_path" in data

    @pytest.mark.asyncio
    async def test_full_streaming_pipeline(self, client):
        """Integration: full start → frame → result → stop pipeline."""
        # Create session
        start_response = client.post("/stream/start")
        session_id = start_response.json()["session_id"]
        assert start_response.status_code == 200

        # Post frame
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        _, png_data = cv2.imencode(".png", frame)
        frame_response = client.post(
            f"/stream/frame/{session_id}",
            files={"file": ("frame.png", png_data.tobytes(), "image/png")},
        )
        assert frame_response.status_code == 200
        frame_id = frame_response.json()["frame_id"]

        # Wait for processing
        await asyncio.sleep(0.2)

        # Poll result
        result_response = client.get(f"/stream/result/{session_id}/{frame_id}")
        assert result_response.status_code == 200
        # Result may still be processing, but endpoint should respond

        # Stop session
        stop_response = client.post(f"/stream/stop/{session_id}")
        assert stop_response.status_code == 200
        assert stop_response.json()["frame_count"] == 1


# ============================================================================
# INTEGRATION TESTS: Concurrent Sessions (additional tests)
# ============================================================================


class TestConcurrentSessions:
    """Integration tests for concurrent session isolation."""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        app, _, _ = create_app(queue_size=100, result_ttl_sec=300)
        return TestClient(app)

    @pytest.mark.asyncio
    async def test_concurrent_sessions_isolated(self, client):
        """Integration: two concurrent sessions remain isolated."""
        # Create two sessions
        s1_response = client.post("/stream/start")
        s2_response = client.post("/stream/start")
        s1_id = s1_response.json()["session_id"]
        s2_id = s2_response.json()["session_id"]
        assert s1_id != s2_id

        # Post frames to each session
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 100
        _, png_data = cv2.imencode(".png", frame)

        s1_frame_response = client.post(
            f"/stream/frame/{s1_id}",
            files={"file": ("frame.png", png_data.tobytes(), "image/png")},
        )
        s1_frame_id = s1_frame_response.json()["frame_id"]

        s2_frame_response = client.post(
            f"/stream/frame/{s2_id}",
            files={"file": ("frame.png", png_data.tobytes(), "image/png")},
        )
        s2_frame_id = s2_frame_response.json()["frame_id"]

        # Verify frame IDs are separate per session
        assert s1_frame_id == 0
        assert s2_frame_id == 0  # Both start at 0 within their sessions

        # Stop both sessions
        s1_stop = client.post(f"/stream/stop/{s1_id}")
        s2_stop = client.post(f"/stream/stop/{s2_id}")
        assert s1_stop.status_code == 200
        assert s2_stop.status_code == 200
