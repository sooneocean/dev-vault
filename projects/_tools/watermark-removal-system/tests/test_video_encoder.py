"""
Unit tests for watermark_removal.postprocessing.video_encoder module.

Tests FFmpeg encoding for frame sequences.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.watermark_removal.postprocessing.video_encoder import VideoEncoder


class TestVideoEncoder:
    """Test VideoEncoder class."""

    def test_init_default(self):
        """Initialize with default parameters."""
        encoder = VideoEncoder()
        assert encoder.fps == 30.0
        assert encoder.codec == "libx264"
        assert encoder.crf == 23

    def test_init_custom(self):
        """Initialize with custom parameters."""
        encoder = VideoEncoder(fps=24.0, codec="libx265", crf=28)
        assert encoder.fps == 24.0
        assert encoder.codec == "libx265"
        assert encoder.crf == 28

    def test_encode_success(self):
        """Successful encoding."""
        encoder = VideoEncoder()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.mp4"

            # Mock subprocess
            with patch("subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_run.return_value = mock_result

                # Create dummy output file
                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.stat") as mock_stat:
                        mock_stat.return_value.st_size = 1024 * 1024  # 1 MB
                        result = encoder.encode(
                            "frames/*.png", output_path
                        )

                assert result is True
                # Verify FFmpeg command structure
                call_args = mock_run.call_args
                assert call_args[0][0][0] == "ffmpeg"
                assert "-pattern_type" in call_args[0][0]
                assert "glob" in call_args[0][0]

    def test_encode_ffmpeg_failure(self):
        """Encoding fails when FFmpeg returns error."""
        encoder = VideoEncoder()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.mp4"

            with patch("subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 1
                mock_result.stderr = "FFmpeg error message"
                mock_run.return_value = mock_result

                result = encoder.encode("frames/*.png", output_path)

                assert result is False

    def test_encode_ffmpeg_not_found(self):
        """Encoding fails when FFmpeg not installed."""
        encoder = VideoEncoder()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.mp4"

            with patch("subprocess.run", side_effect=FileNotFoundError):
                result = encoder.encode("frames/*.png", output_path)

                assert result is False

    def test_encode_timeout(self):
        """Encoding times out."""
        encoder = VideoEncoder()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.mp4"

            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = TimeoutError

                result = encoder.encode("frames/*.png", output_path)

                assert result is False

    def test_encode_custom_framerate(self):
        """Encode with custom framerate override."""
        encoder = VideoEncoder(fps=30.0)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.mp4"

            with patch("subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_run.return_value = mock_result

                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.stat") as mock_stat:
                        mock_stat.return_value.st_size = 1024 * 1024
                        encoder.encode(
                            "frames/*.png",
                            output_path,
                            framerate=24.0,
                        )

                # Verify 24.0 fps was used, not 30.0
                call_args = mock_run.call_args[0][0]
                fps_index = call_args.index("-framerate") + 1
                assert call_args[fps_index] == "24.0"

    def test_encode_with_bitrate_success(self):
        """Encode with bitrate instead of CRF."""
        encoder = VideoEncoder()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.mp4"

            with patch("subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_run.return_value = mock_result

                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.stat") as mock_stat:
                        mock_stat.return_value.st_size = 5 * 1024 * 1024  # 5 MB
                        result = encoder.encode_with_bitrate(
                            "frames/*.png",
                            output_path,
                            bitrate="5000k",
                        )

                assert result is True
                # Verify bitrate is in command
                call_args = mock_run.call_args[0][0]
                assert "-b:v" in call_args
                assert "5000k" in call_args

    def test_encode_creates_output_directory(self):
        """Encode creates output directory if it doesn't exist."""
        encoder = VideoEncoder()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "output.mp4"
            assert not output_path.parent.exists()

            with patch("subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_run.return_value = mock_result

                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.stat") as mock_stat:
                        mock_stat.return_value.st_size = 1024 * 1024
                        encoder.encode("frames/*.png", output_path)

                # Directory should be created
                assert output_path.parent.exists()

    def test_get_video_info_success(self):
        """Get video information from ffprobe."""
        encoder = VideoEncoder()

        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "1920\n1080\n30/1\n120.5"
            mock_run.return_value = mock_result

            info = encoder.get_video_info("video.mp4")

            assert info is not None
            assert info["width"] == 1920
            assert info["height"] == 1080
            assert info["fps"] == 30.0
            assert info["duration"] == 120.5

    def test_get_video_info_not_found(self):
        """Get video info when ffprobe not installed."""
        encoder = VideoEncoder()

        with patch("subprocess.run", side_effect=FileNotFoundError):
            info = encoder.get_video_info("video.mp4")

            assert info is None

    def test_get_video_info_failure(self):
        """Get video info returns None on error."""
        encoder = VideoEncoder()

        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_run.return_value = mock_result

            info = encoder.get_video_info("video.mp4")

            assert info is None


class TestVideoEncoderIntegration:
    """Integration tests for VideoEncoder."""

    def test_encoder_with_custom_fps_and_codec(self):
        """Create encoder with custom settings."""
        encoder = VideoEncoder(fps=24.0, codec="libx265", crf=28)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.mp4"

            with patch("subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_run.return_value = mock_result

                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.stat") as mock_stat:
                        mock_stat.return_value.st_size = 1024 * 1024
                        encoder.encode("frames/*.png", output_path)

                # Verify codec is in command
                call_args = mock_run.call_args[0][0]
                assert "-c:v" in call_args
                codec_index = call_args.index("-c:v") + 1
                assert call_args[codec_index] == "libx265"
                # Verify CRF is in command
                assert "-crf" in call_args
                crf_index = call_args.index("-crf") + 1
                assert call_args[crf_index] == "28"

    def test_multiple_encodings_independent(self):
        """Multiple encoder instances are independent."""
        encoder1 = VideoEncoder(fps=24.0, crf=23)
        encoder2 = VideoEncoder(fps=60.0, crf=18)

        assert encoder1.fps == 24.0
        assert encoder2.fps == 60.0
        assert encoder1.crf == 23
        assert encoder2.crf == 18

    def test_encode_empty_output_file(self):
        """Encoding fails if output file is empty."""
        encoder = VideoEncoder()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.mp4"

            with patch("subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_run.return_value = mock_result

                with patch("pathlib.Path.exists", return_value=True):
                    with patch("pathlib.Path.stat") as mock_stat:
                        mock_stat.return_value.st_size = 0  # Empty file
                        result = encoder.encode("frames/*.png", output_path)

                assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
