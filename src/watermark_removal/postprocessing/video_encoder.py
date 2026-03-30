"""Re-encode frame sequence to MP4 using FFmpeg."""

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from ..core.types import ProcessConfig

logger = logging.getLogger(__name__)


class VideoEncoder:
    """Re-encode frame sequence to MP4 output using FFmpeg."""

    def __init__(self, ffmpeg_path: str | None = None) -> None:
        """Initialize video encoder with FFmpeg binary path.

        Args:
            ffmpeg_path: Path to ffmpeg binary. If None, will search in system PATH.

        Raises:
            FileNotFoundError: If ffmpeg binary not found.
        """
        if ffmpeg_path is None:
            ffmpeg_path = shutil.which("ffmpeg")
            if ffmpeg_path is None:
                raise FileNotFoundError(
                    "FFmpeg binary not found in PATH. "
                    "Install FFmpeg or provide explicit path via ffmpeg_path parameter."
                )

        self.ffmpeg_path = ffmpeg_path
        logger.debug(f"Using FFmpeg: {self.ffmpeg_path}")

    def encode_frames_to_video(
        self,
        input_dir: str,
        output_path: str,
        fps: float,
        codec: str = "h264",
        crf: int = 23,
        pattern: str = "frame_%06d.png",
    ) -> Path:
        """Encode frame sequence to MP4 video using FFmpeg.

        Args:
            input_dir: Directory containing frame PNG files.
            output_path: Path to output MP4 file.
            fps: Frames per second for output video.
            codec: Video codec (h264, h265, vp9, etc.).
            crf: Constant rate factor / quality (0-51, lower=better, default 23).
            pattern: Frame filename pattern (e.g., frame_%06d.png).

        Returns:
            Path to output video file.

        Raises:
            FileNotFoundError: If input directory does not exist.
            FileNotFoundError: If no frame files found matching pattern.
            RuntimeError: If FFmpeg encoding fails.
            ValueError: If parameters are invalid.
        """
        # Validate input directory
        input_path = Path(input_dir)
        if not input_path.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        if not input_path.is_dir():
            raise FileNotFoundError(f"Input path is not a directory: {input_dir}")

        # Validate FPS and CRF
        if fps <= 0:
            raise ValueError(f"FPS must be positive, got {fps}")
        if not 0 <= crf <= 51:
            raise ValueError(f"CRF must be in range [0, 51], got {crf}")

        # Check if any frames exist
        frame_files = list(input_path.glob("*.png"))
        if not frame_files:
            raise FileNotFoundError(
                f"No PNG frame files found in {input_dir}"
            )

        logger.info(
            f"Encoding {len(frame_files)} frames to {output_path} "
            f"(fps={fps}, codec={codec}, crf={crf})"
        )

        # Build FFmpeg command
        # Format: ffmpeg -framerate fps -i input_pattern -c:v codec -crf crf output.mp4
        input_pattern = str(input_path / pattern)
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            self.ffmpeg_path,
            "-framerate", str(fps),
            "-i", input_pattern,
            "-c:v", codec,
            "-crf", str(crf),
            "-y",  # Overwrite output file
            str(output_file),
        ]

        logger.debug(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=3600.0,  # 1 hour timeout
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                raise RuntimeError(
                    f"FFmpeg encoding failed with exit code {result.returncode}: {error_msg}"
                )

            if not output_file.exists():
                raise RuntimeError(
                    f"FFmpeg completed but output file not found: {output_file}"
                )

            file_size = output_file.stat().st_size
            logger.info(
                f"Video encoding complete: {output_file} "
                f"({file_size / 1024 / 1024:.2f} MB)"
            )

            return output_file

        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"FFmpeg encoding timeout: {e}") from e
        except Exception as e:
            raise RuntimeError(f"FFmpeg encoding failed: {e}") from e

    def encode_from_config(
        self,
        input_dir: str,
        config: ProcessConfig,
    ) -> Path:
        """Encode frame sequence to video using ProcessConfig parameters.

        Args:
            input_dir: Directory containing frame PNG files.
            config: ProcessConfig with output settings.

        Returns:
            Path to output video file.
        """
        output_path = str(Path(config.output_dir) / "output.mp4")

        return self.encode_frames_to_video(
            input_dir=input_dir,
            output_path=output_path,
            fps=30.0,  # Default FPS (should be read from config if stored)
            codec=config.output_codec,
            crf=config.output_crf,
            pattern="frame_%06d.png",
        )
