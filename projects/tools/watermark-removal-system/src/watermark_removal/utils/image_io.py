"""
Image I/O utilities for reading and writing images.
"""

import cv2
import numpy as np
from pathlib import Path


def read_image(image_path: str | Path) -> np.ndarray:
    """
    Read image from file (BGR format, as per OpenCV convention).

    Args:
        image_path: Path to image file

    Returns:
        BGR ndarray (H, W, 3), uint8

    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If image cannot be read
    """
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Failed to read image: {image_path}")

    return image


def write_image(image_path: str | Path, image: np.ndarray) -> None:
    """
    Write image to file in PNG format.

    Args:
        image_path: Output path
        image: BGR ndarray (H, W, 3), uint8

    Raises:
        IOError: If write fails
    """
    image_path = Path(image_path)
    image_path.parent.mkdir(parents=True, exist_ok=True)

    success = cv2.imwrite(str(image_path), image)
    if not success:
        raise IOError(f"Failed to write image: {image_path}")


def get_image_shape(image_path: str | Path) -> tuple[int, int, int]:
    """
    Get image dimensions without loading full image data.

    Args:
        image_path: Path to image file

    Returns:
        Tuple (height, width, channels)
    """
    image = read_image(image_path)
    return image.shape


def get_video_metadata(video_path: str | Path) -> dict:
    """
    Extract video metadata without reading frames.

    Args:
        video_path: Path to video file

    Returns:
        Dict with keys: fps, width, height, frame_count, duration_sec
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Failed to open video: {video_path}")

    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_sec = frame_count / fps if fps > 0 else 0

        return {
            "fps": fps,
            "width": width,
            "height": height,
            "frame_count": frame_count,
            "duration_sec": duration_sec,
        }
    finally:
        cap.release()
