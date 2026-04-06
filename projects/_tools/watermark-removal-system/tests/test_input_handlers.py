"""
Unit tests for streaming input handlers.

Tests various input sources: files, RTMP, RTSP, HLS.
"""

import pytest
import numpy as np
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock

from src.api.input_handler import (
    InputHandler,
    FileInputHandler,
    RTMPInputHandler,
    RTSPInputHandler,
    HLSInputHandler,
    create_input_handler,
)


class TestFileInputHandler:
    """Test file-based input handler."""

    def test_initialization(self):
        """FileInputHandler initializes correctly."""
        handler = FileInputHandler("file:///path/to/video.mp4")

        assert handler.source_url == "file:///path/to/video.mp4"
        assert handler.file_path == "/path/to/video.mp4"
        assert handler.is_connected is False
        assert handler.fps == 30.0
        assert handler.width == 1920
        assert handler.height == 1080

    def test_file_path_extraction_with_file_scheme(self):
        """FileInputHandler extracts file path from file:// URL."""
        handler = FileInputHandler("file:///test/video.mp4")
        assert handler.file_path == "/test/video.mp4"

    def test_file_path_extraction_without_scheme(self):
        """FileInputHandler handles direct file paths."""
        handler = FileInputHandler("/path/to/video.mp4")
        assert handler.file_path == "/path/to/video.mp4"

    @pytest.mark.asyncio
    async def test_connect_nonexistent_file(self):
        """connect() fails for nonexistent file."""
        handler = FileInputHandler("/nonexistent/path/video.mp4")
        result = await handler.connect()

        assert result is False
        assert handler.is_connected is False

    @pytest.mark.asyncio
    async def test_connect_without_cv2(self):
        """connect() handles missing OpenCV gracefully."""
        with patch.dict("sys.modules", {"cv2": None}):
            handler = FileInputHandler("file:///test.mp4")

            # Create temporary test file
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
                temp_path = f.name
                handler.file_path = temp_path

            try:
                result = await handler.connect()
                assert result is True
                assert handler.is_connected is True
            finally:
                Path(temp_path).unlink()
                await handler.disconnect()

    @pytest.mark.asyncio
    async def test_read_frame_simulated(self):
        """read_frame() returns synthetic frames when cv2 unavailable."""
        handler = FileInputHandler("/test.mp4")
        handler.is_connected = True
        handler.reader = None  # Simulate no cv2

        frame = await handler.read_frame()

        assert frame is not None
        assert frame.shape == (1080, 1920, 3)
        assert frame.dtype == np.uint8
        assert handler.frame_count == 1

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """disconnect() closes handler."""
        handler = FileInputHandler("/test.mp4")
        handler.is_connected = True
        handler.reader = None

        await handler.disconnect()

        assert handler.is_connected is False

    @pytest.mark.asyncio
    async def test_get_properties(self):
        """get_properties() returns stream properties."""
        handler = FileInputHandler("/test.mp4")
        handler.is_connected = True

        props = await handler.get_properties()

        assert props["fps"] == 30.0
        assert props["width"] == 1920
        assert props["height"] == 1080
        assert props["connected"] is True


class TestRTMPInputHandler:
    """Test RTMP input handler."""

    def test_initialization(self):
        """RTMPInputHandler initializes correctly."""
        handler = RTMPInputHandler("rtmp://example.com/live/stream")

        assert handler.source_url == "rtmp://example.com/live/stream"
        assert handler.is_connected is False
        assert handler.reader is None

    @pytest.mark.asyncio
    async def test_read_frame_simulated(self):
        """read_frame() returns frames when cv2 unavailable."""
        handler = RTMPInputHandler("rtmp://example.com/live")
        handler.is_connected = True
        handler.reader = None

        frame = await handler.read_frame()

        assert frame is not None
        assert frame.shape == (1080, 1920, 3)
        assert frame.dtype == np.uint8
        assert handler.frame_count == 1

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """disconnect() closes handler."""
        handler = RTMPInputHandler("rtmp://example.com/live")
        handler.is_connected = True
        handler.reader = None

        await handler.disconnect()

        assert handler.is_connected is False


class TestRTSPInputHandler:
    """Test RTSP input handler (IP cameras)."""

    def test_initialization(self):
        """RTSPInputHandler initializes correctly."""
        handler = RTSPInputHandler("rtsp://camera.example.com/stream")

        assert handler.source_url == "rtsp://camera.example.com/stream"
        assert handler.is_connected is False
        assert handler.reconnect_attempts == 0
        assert handler.max_reconnect_attempts == 3

    @pytest.mark.asyncio
    async def test_read_frame_simulated(self):
        """read_frame() returns frames when cv2 unavailable."""
        handler = RTSPInputHandler("rtsp://camera.example.com")
        handler.is_connected = True
        handler.reader = None

        frame = await handler.read_frame()

        assert frame is not None
        assert frame.shape == (1080, 1920, 3)
        assert frame.dtype == np.uint8

    @pytest.mark.asyncio
    async def test_reconnect_attempts_increment(self):
        """read_frame() increments reconnect_attempts on failure."""
        handler = RTSPInputHandler("rtsp://camera.example.com")
        handler.is_connected = True

        # Mock reader that returns False
        mock_reader = Mock()
        mock_reader.read.return_value = (False, None)
        handler.reader = mock_reader

        # Mock connect to prevent actual connection
        with patch.object(handler, "connect", new_callable=AsyncMock, return_value=False):
            result = await handler.read_frame()

        assert result is None
        assert handler.reconnect_attempts == 1

    @pytest.mark.asyncio
    async def test_max_reconnect_attempts_exceeded(self):
        """read_frame() stops retrying after max attempts."""
        handler = RTSPInputHandler("rtsp://camera.example.com")
        handler.is_connected = True
        handler.reconnect_attempts = 3  # Already at max

        mock_reader = Mock()
        mock_reader.read.return_value = (False, None)
        handler.reader = mock_reader

        result = await handler.read_frame()

        # Should return None without further attempts
        assert result is None


class TestHLSInputHandler:
    """Test HLS stream handler."""

    def test_initialization(self):
        """HLSInputHandler initializes correctly."""
        handler = HLSInputHandler("https://example.com/stream.m3u8")

        assert handler.source_url == "https://example.com/stream.m3u8"
        assert handler.is_connected is False

    @pytest.mark.asyncio
    async def test_read_frame_simulated(self):
        """read_frame() returns frames when cv2 unavailable."""
        handler = HLSInputHandler("https://example.com/stream.m3u8")
        handler.is_connected = True
        handler.reader = None

        frame = await handler.read_frame()

        assert frame is not None
        assert frame.shape == (1080, 1920, 3)
        assert frame.dtype == np.uint8
        assert handler.frame_count == 1


class TestInputHandlerFactory:
    """Test create_input_handler factory function."""

    def test_factory_file_with_file_scheme(self):
        """create_input_handler recognizes file:// URLs."""
        handler = create_input_handler("file:///path/to/video.mp4")
        assert isinstance(handler, FileInputHandler)

    def test_factory_file_with_mp4_extension(self):
        """create_input_handler recognizes .mp4 files."""
        handler = create_input_handler("/path/to/video.mp4")
        assert isinstance(handler, FileInputHandler)

    def test_factory_file_with_avi_extension(self):
        """create_input_handler recognizes .avi files."""
        handler = create_input_handler("/path/to/video.avi")
        assert isinstance(handler, FileInputHandler)

    def test_factory_file_with_mkv_extension(self):
        """create_input_handler recognizes .mkv files."""
        handler = create_input_handler("/path/to/video.mkv")
        assert isinstance(handler, FileInputHandler)

    def test_factory_file_with_mov_extension(self):
        """create_input_handler recognizes .mov files."""
        handler = create_input_handler("/path/to/video.mov")
        assert isinstance(handler, FileInputHandler)

    def test_factory_rtmp(self):
        """create_input_handler recognizes RTMP URLs."""
        handler = create_input_handler("rtmp://example.com/live/stream")
        assert isinstance(handler, RTMPInputHandler)

    def test_factory_rtsp(self):
        """create_input_handler recognizes RTSP URLs."""
        handler = create_input_handler("rtsp://camera.example.com/stream")
        assert isinstance(handler, RTSPInputHandler)

    def test_factory_hls(self):
        """create_input_handler recognizes HLS URLs."""
        handler = create_input_handler("https://example.com/stream.m3u8")
        assert isinstance(handler, HLSInputHandler)

    def test_factory_unknown_defaults_to_file(self):
        """create_input_handler defaults to FileInputHandler for unknown formats."""
        handler = create_input_handler("http://example.com/video")
        assert isinstance(handler, FileInputHandler)


class TestInputHandlerIntegration:
    """Integration tests for input handlers."""

    @pytest.mark.asyncio
    async def test_handler_lifecycle(self):
        """Handler lifecycle: connect → read → disconnect."""
        # Create temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            temp_path = f.name

        try:
            handler = FileInputHandler(temp_path)
            handler.reader = None  # Simulate simulated mode

            # Connect
            result = await handler.connect()
            assert result is True
            assert handler.is_connected is True

            # Read multiple frames
            frame1 = await handler.read_frame()
            frame2 = await handler.read_frame()

            assert frame1 is not None
            assert frame2 is not None
            assert handler.frame_count == 2

            # Disconnect
            await handler.disconnect()
            assert handler.is_connected is False
        finally:
            Path(temp_path).unlink()

    @pytest.mark.asyncio
    async def test_multiple_handlers_concurrent(self):
        """Multiple handlers can operate concurrently."""
        import asyncio

        handlers = [
            FileInputHandler("/test1.mp4"),
            RTMPInputHandler("rtmp://example.com/stream"),
            RTSPInputHandler("rtsp://camera.example.com"),
        ]

        # Set all to simulated mode
        for h in handlers:
            h.reader = None
            h.is_connected = True

        # Read from all concurrently
        tasks = [h.read_frame() for h in handlers]
        frames = await asyncio.gather(*tasks)

        assert len(frames) == 3
        assert all(f is not None for f in frames)
        assert all(f.shape == (1080, 1920, 3) for f in frames)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
