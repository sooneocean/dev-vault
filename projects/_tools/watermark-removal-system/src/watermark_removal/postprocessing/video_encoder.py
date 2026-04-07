"""
Video encoding using FFmpeg.

Re-encodes frame sequences to MP4 with configurable fps, codec, and quality.
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class VideoEncoder:
    """Encode frame sequences to MP4 using FFmpeg."""

    def __init__(
        self,
        fps: float = 30.0,
        codec: str = "libx264",
        crf: int = 23,
    ):
        """
        Initialize video encoder.

        Args:
            fps: Frames per second
            codec: FFmpeg codec (libx264 for h264, libx265 for h265)
            crf: Quality (0=lossless, 23=default, 51=worst)
        """
        self.fps = fps
        self.codec = codec
        self.crf = crf
        logger.info(
            f"VideoEncoder: fps={fps}, codec={codec}, crf={crf}"
        )

    def encode(
        self,
        input_pattern: str | Path,
        output_path: str | Path,
        framerate: Optional[float] = None,
    ) -> bool:
        """
        Encode frame sequence to MP4 using FFmpeg.

        Args:
            input_pattern: Glob pattern for input frames (e.g., "frames/*.png")
            output_path: Path to output MP4 file
            framerate: Override default fps for this encoding

        Returns:
            True if successful, False otherwise
        """
        fps_to_use = framerate if framerate is not None else self.fps
        output_path = Path(output_path)

        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # FFmpeg command
        cmd = [
            "ffmpeg",
            "-framerate", str(fps_to_use),
            "-pattern_type", "glob",
            "-i", str(input_pattern),
            "-c:v", self.codec,
            "-crf", str(self.crf),
            "-y",  # Overwrite output file
            str(output_path),
        ]

        logger.info(f"Encoding frames to {output_path}")
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg failed: {result.stderr}")
                return False

            if output_path.exists() and output_path.stat().st_size > 0:
                logger.info(
                    f"Encoded successfully: {output_path} "
                    f"({output_path.stat().st_size / 1024 / 1024:.1f} MB)"
                )
                return True
            else:
                logger.error("Output file not created or is empty")
                return False

        except FileNotFoundError:
            logger.error("FFmpeg not found. Install FFmpeg and add to PATH.")
            return False
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg encoding timed out (> 1 hour)")
            return False
        except Exception as e:
            logger.error(f"Encoding failed: {e}")
            return False

    def encode_with_bitrate(
        self,
        input_pattern: str | Path,
        output_path: str | Path,
        bitrate: str = "5000k",
        framerate: Optional[float] = None,
    ) -> bool:
        """
        Encode with fixed bitrate instead of CRF.

        Args:
            input_pattern: Glob pattern for input frames
            output_path: Path to output MP4
            bitrate: Target bitrate (e.g., "5000k", "10M")
            framerate: Override default fps

        Returns:
            True if successful
        """
        fps_to_use = framerate if framerate is not None else self.fps
        output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # FFmpeg command with bitrate instead of CRF
        cmd = [
            "ffmpeg",
            "-framerate", str(fps_to_use),
            "-pattern_type", "glob",
            "-i", str(input_pattern),
            "-c:v", self.codec,
            "-b:v", bitrate,
            "-y",
            str(output_path),
        ]

        logger.info(f"Encoding frames to {output_path} at {bitrate}")
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg failed: {result.stderr}")
                return False

            if output_path.exists() and output_path.stat().st_size > 0:
                logger.info(
                    f"Encoded successfully: {output_path} "
                    f"({output_path.stat().st_size / 1024 / 1024:.1f} MB)"
                )
                return True
            else:
                logger.error("Output file not created or is empty")
                return False

        except FileNotFoundError:
            logger.error("FFmpeg not found")
            return False
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg encoding timed out")
            return False
        except Exception as e:
            logger.error(f"Encoding failed: {e}")
            return False

    def get_video_info(self, video_path: str | Path) -> Optional[dict]:
        """
        Get video information using ffprobe.

        Args:
            video_path: Path to video file

        Returns:
            Dict with width, height, fps, duration, or None if ffprobe fails
        """
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries",
                "stream=width,height,r_frame_rate",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1:nokey=1",
                str(video_path),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) >= 4:
                    try:
                        width = int(lines[0])
                        height = int(lines[1])
                        fps_str = lines[2]  # e.g., "30/1"
                        duration = float(lines[3])

                        # Parse fps
                        if "/" in fps_str:
                            num, den = map(float, fps_str.split("/"))
                            fps = num / den if den != 0 else 30.0
                        else:
                            fps = float(fps_str)

                        return {
                            "width": width,
                            "height": height,
                            "fps": fps,
                            "duration": duration,
                        }
                    except (ValueError, IndexError):
                        pass

        except FileNotFoundError:
            logger.warning("ffprobe not found")
        except Exception as e:
            logger.warning(f"Failed to get video info: {e}")

        return None
