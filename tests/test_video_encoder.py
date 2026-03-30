"""Tests for video encoder."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest

from src.watermark_removal.core.types import ProcessConfig
from src.watermark_removal.postprocessing.video_encoder import VideoEncoder


def create_test_frame(path: str, width: int = 1920, height: int = 1080) -> None:
    """Create a test PNG frame."""
    image = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        image[y, :] = [y % 256, (y // 2) % 256, (y // 3) % 256]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(path, image)


@pytest.fixture
def default_process_config() -> ProcessConfig:
    """Create default process config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        return ProcessConfig(
            video_path="input.mp4",
            mask_path="mask.png",
            output_dir=tmpdir,
        )


class TestVideoEncoderHappyPath:
    """Happy path tests."""

    def test_video_encoder_initialization(self):
        """Test encoder initialization with explicit path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dummy ffmpeg binary
            ffmpeg_path = f"{tmpdir}/ffmpeg"
            Path(ffmpeg_path).touch()

            encoder = VideoEncoder(ffmpeg_path=ffmpeg_path)
            assert encoder.ffmpeg_path == ffmpeg_path

    def test_video_encoder_initialize_from_path(self):
        """Test encoder initialization searching system PATH."""
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            encoder = VideoEncoder()
            assert encoder.ffmpeg_path == "/usr/bin/ffmpeg"

    @patch("subprocess.run")
    def test_video_encoder_encode_frames_happy_path(self, mock_run):
        """Test encoding frame sequence to video."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = f"{tmpdir}/frames"
            output_path = f"{tmpdir}/output.mp4"

            # Create dummy frames
            Path(input_dir).mkdir(parents=True, exist_ok=True)
            for i in range(3):
                frame_path = f"{input_dir}/frame_{i:06d}.png"
                create_test_frame(frame_path)

            # Create output file for mock
            Path(output_path).touch()

            # Mock FFmpeg
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

            encoder = VideoEncoder(ffmpeg_path="/usr/bin/ffmpeg")
            result = encoder.encode_frames_to_video(
                input_dir=input_dir,
                output_path=output_path,
                fps=30.0,
                codec="h264",
                crf=23,
            )

            assert result == Path(output_path)
            assert result.exists()
            mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_video_encoder_encode_with_different_codecs(self, mock_run):
        """Test encoding with different codecs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = f"{tmpdir}/frames"
            Path(input_dir).mkdir(parents=True, exist_ok=True)
            create_test_frame(f"{input_dir}/frame_000000.png")

            # Mock FFmpeg
            def mock_run_fn(*args, **kwargs):
                cmd = args[0] if args else []
                output_file = cmd[-1] if cmd else ""
                Path(output_file).touch()
                return MagicMock(returncode=0, stderr="", stdout="")

            mock_run.side_effect = mock_run_fn

            encoder = VideoEncoder(ffmpeg_path="/usr/bin/ffmpeg")

            for codec in ["h264", "h265", "vp9"]:
                output_path = f"{tmpdir}/output_{codec}.mp4"
                result = encoder.encode_frames_to_video(
                    input_dir=input_dir,
                    output_path=output_path,
                    fps=24.0,
                    codec=codec,
                    crf=20,
                )
                assert result.exists()

    @patch("subprocess.run")
    def test_video_encoder_encode_with_different_crf(self, mock_run):
        """Test encoding with different CRF values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = f"{tmpdir}/frames"
            Path(input_dir).mkdir(parents=True, exist_ok=True)
            create_test_frame(f"{input_dir}/frame_000000.png")

            def mock_run_fn(*args, **kwargs):
                cmd = args[0] if args else []
                output_file = cmd[-1] if cmd else ""
                Path(output_file).touch()
                return MagicMock(returncode=0, stderr="", stdout="")

            mock_run.side_effect = mock_run_fn

            encoder = VideoEncoder(ffmpeg_path="/usr/bin/ffmpeg")

            for crf in [18, 23, 28, 32]:
                output_path = f"{tmpdir}/output_crf{crf}.mp4"
                result = encoder.encode_frames_to_video(
                    input_dir=input_dir,
                    output_path=output_path,
                    fps=30.0,
                    codec="h264",
                    crf=crf,
                )
                assert result.exists()


class TestVideoEncoderEdgeCases:
    """Edge case tests."""

    def test_video_encoder_single_frame(self):
        """Test encoding with single frame."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = f"{tmpdir}/frames"
            output_path = f"{tmpdir}/output.mp4"

            Path(input_dir).mkdir(parents=True, exist_ok=True)
            create_test_frame(f"{input_dir}/frame_000000.png")

            with patch("subprocess.run") as mock_run:
                Path(output_path).touch()
                mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

                encoder = VideoEncoder(ffmpeg_path="/usr/bin/ffmpeg")
                result = encoder.encode_frames_to_video(
                    input_dir=input_dir,
                    output_path=output_path,
                    fps=30.0,
                )

                assert result.exists()

    def test_video_encoder_many_frames(self):
        """Test encoding with many frames."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = f"{tmpdir}/frames"
            output_path = f"{tmpdir}/output.mp4"

            Path(input_dir).mkdir(parents=True, exist_ok=True)

            # Create many frames
            for i in range(100):
                frame_path = f"{input_dir}/frame_{i:06d}.png"
                create_test_frame(frame_path)

            with patch("subprocess.run") as mock_run:
                Path(output_path).touch()
                mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

                encoder = VideoEncoder(ffmpeg_path="/usr/bin/ffmpeg")
                result = encoder.encode_frames_to_video(
                    input_dir=input_dir,
                    output_path=output_path,
                    fps=30.0,
                )

                assert result.exists()

    @patch("subprocess.run")
    def test_video_encoder_various_fps(self, mock_run):
        """Test encoding with various FPS values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = f"{tmpdir}/frames"
            Path(input_dir).mkdir(parents=True, exist_ok=True)
            create_test_frame(f"{input_dir}/frame_000000.png")

            def mock_run_fn(*args, **kwargs):
                cmd = args[0] if args else []
                output_file = cmd[-1] if cmd else ""
                Path(output_file).touch()
                return MagicMock(returncode=0, stderr="", stdout="")

            mock_run.side_effect = mock_run_fn

            encoder = VideoEncoder(ffmpeg_path="/usr/bin/ffmpeg")

            for fps in [23.976, 24.0, 25.0, 29.97, 30.0, 60.0]:
                output_path = f"{tmpdir}/output_fps{fps}.mp4"
                result = encoder.encode_frames_to_video(
                    input_dir=input_dir,
                    output_path=output_path,
                    fps=fps,
                )
                assert result.exists()


class TestVideoEncoderErrors:
    """Error handling tests."""

    def test_video_encoder_missing_ffmpeg(self):
        """Test error when FFmpeg not found."""
        with patch("shutil.which", return_value=None):
            with pytest.raises(FileNotFoundError, match="FFmpeg binary not found"):
                VideoEncoder()

    def test_video_encoder_missing_input_directory(self):
        """Test error when input directory does not exist."""
        encoder = VideoEncoder(ffmpeg_path="/usr/bin/ffmpeg")

        with pytest.raises(FileNotFoundError, match="Input directory not found"):
            encoder.encode_frames_to_video(
                input_dir="/nonexistent/directory",
                output_path="/tmp/output.mp4",
                fps=30.0,
            )

    def test_video_encoder_input_is_file_not_directory(self):
        """Test error when input path is a file not directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = f"{tmpdir}/file.txt"
            Path(file_path).touch()

            encoder = VideoEncoder(ffmpeg_path="/usr/bin/ffmpeg")

            with pytest.raises(FileNotFoundError, match="not a directory"):
                encoder.encode_frames_to_video(
                    input_dir=file_path,
                    output_path="/tmp/output.mp4",
                    fps=30.0,
                )

    def test_video_encoder_no_frames_found(self):
        """Test error when no frame files found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            encoder = VideoEncoder(ffmpeg_path="/usr/bin/ffmpeg")

            with pytest.raises(FileNotFoundError, match="No PNG frame files found"):
                encoder.encode_frames_to_video(
                    input_dir=tmpdir,
                    output_path="/tmp/output.mp4",
                    fps=30.0,
                )

    def test_video_encoder_invalid_fps(self):
        """Test error with invalid FPS value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = f"{tmpdir}/frames"
            Path(input_dir).mkdir(parents=True, exist_ok=True)
            create_test_frame(f"{input_dir}/frame_000000.png")

            encoder = VideoEncoder(ffmpeg_path="/usr/bin/ffmpeg")

            with pytest.raises(ValueError, match="FPS must be positive"):
                encoder.encode_frames_to_video(
                    input_dir=input_dir,
                    output_path="/tmp/output.mp4",
                    fps=-1.0,
                )

    def test_video_encoder_invalid_crf(self):
        """Test error with invalid CRF value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = f"{tmpdir}/frames"
            Path(input_dir).mkdir(parents=True, exist_ok=True)
            create_test_frame(f"{input_dir}/frame_000000.png")

            encoder = VideoEncoder(ffmpeg_path="/usr/bin/ffmpeg")

            with pytest.raises(ValueError, match="CRF must be in range"):
                encoder.encode_frames_to_video(
                    input_dir=input_dir,
                    output_path="/tmp/output.mp4",
                    fps=30.0,
                    crf=100,
                )

    @patch("subprocess.run")
    def test_video_encoder_ffmpeg_failure(self, mock_run):
        """Test error when FFmpeg fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = f"{tmpdir}/frames"
            output_path = f"{tmpdir}/output.mp4"

            Path(input_dir).mkdir(parents=True, exist_ok=True)
            create_test_frame(f"{input_dir}/frame_000000.png")

            # Mock FFmpeg failure
            mock_run.return_value = MagicMock(
                returncode=1,
                stderr="Error: invalid codec",
                stdout="",
            )

            encoder = VideoEncoder(ffmpeg_path="/usr/bin/ffmpeg")

            with pytest.raises(RuntimeError, match="FFmpeg encoding failed"):
                encoder.encode_frames_to_video(
                    input_dir=input_dir,
                    output_path=output_path,
                    fps=30.0,
                )

    @patch("subprocess.run")
    def test_video_encoder_output_file_not_created(self, mock_run):
        """Test error when FFmpeg doesn't create output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = f"{tmpdir}/frames"
            output_path = f"{tmpdir}/output.mp4"

            Path(input_dir).mkdir(parents=True, exist_ok=True)
            create_test_frame(f"{input_dir}/frame_000000.png")

            # Mock FFmpeg success but no output file
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

            encoder = VideoEncoder(ffmpeg_path="/usr/bin/ffmpeg")

            with pytest.raises(RuntimeError, match="output file not found"):
                encoder.encode_frames_to_video(
                    input_dir=input_dir,
                    output_path=output_path,
                    fps=30.0,
                )

    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired("ffmpeg", 3600))
    def test_video_encoder_timeout(self, mock_run):
        """Test error when FFmpeg times out."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = f"{tmpdir}/frames"
            Path(input_dir).mkdir(parents=True, exist_ok=True)
            create_test_frame(f"{input_dir}/frame_000000.png")

            encoder = VideoEncoder(ffmpeg_path="/usr/bin/ffmpeg")

            with pytest.raises(RuntimeError, match="timeout"):
                encoder.encode_frames_to_video(
                    input_dir=input_dir,
                    output_path="/tmp/output.mp4",
                    fps=30.0,
                )


class TestVideoEncoderIntegration:
    """Integration tests."""

    @patch("subprocess.run")
    def test_video_encoder_encode_from_config(self, mock_run):
        """Test encoding using ProcessConfig."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = f"{tmpdir}/frames"
            Path(input_dir).mkdir(parents=True, exist_ok=True)
            create_test_frame(f"{input_dir}/frame_000000.png")

            config = ProcessConfig(
                video_path="input.mp4",
                mask_path="mask.png",
                output_dir=tmpdir,
                output_codec="h264",
                output_crf=25,
            )

            def mock_run_fn(*args, **kwargs):
                cmd = args[0] if args else []
                output_file = cmd[-1] if cmd else ""
                Path(output_file).touch()
                return MagicMock(returncode=0, stderr="", stdout="")

            mock_run.side_effect = mock_run_fn

            encoder = VideoEncoder(ffmpeg_path="/usr/bin/ffmpeg")
            result = encoder.encode_from_config(input_dir, config)

            assert result.exists()
            assert result.name == "output.mp4"
