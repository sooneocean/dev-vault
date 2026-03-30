"""Image I/O utilities for watermark removal pipeline."""

import logging
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def read_image(image_path: str | Path) -> np.ndarray:
    """Read image file as BGR uint8 ndarray.

    Args:
        image_path: Path to image file.

    Returns:
        Image as numpy array (H, W, 3) in BGR format, uint8 dtype.

    Raises:
        FileNotFoundError: If image file does not exist.
        ValueError: If image cannot be read or has unexpected format.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")

    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Failed to read image: {path}")

    # Ensure BGR format (cv2 uses BGR by default)
    if len(image.shape) != 3 or image.shape[2] != 3:
        raise ValueError(f"Expected BGR image, got shape: {image.shape}")

    return image


def write_image(
    output_path: str | Path, image: np.ndarray, create_dirs: bool = True
) -> None:
    """Write image to disk in PNG format.

    Args:
        output_path: Path to output file (should end in .png).
        image: Image as numpy array (H, W, 3) in BGR format.
        create_dirs: If True, create parent directories if needed.

    Raises:
        ValueError: If image format is invalid or write fails.
    """
    path = Path(output_path)

    if create_dirs:
        path.parent.mkdir(parents=True, exist_ok=True)

    if len(image.shape) != 3 or image.shape[2] != 3:
        raise ValueError(f"Expected BGR image, got shape: {image.shape}")

    success = cv2.imwrite(str(path), image)
    if not success:
        raise ValueError(f"Failed to write image: {path}")

    logger.debug(f"Wrote image: {path}")


def get_image_shape(image_path: str | Path) -> tuple[int, int, int]:
    """Get image dimensions without loading full image.

    Args:
        image_path: Path to image file.

    Returns:
        Tuple of (height, width, channels).

    Raises:
        FileNotFoundError: If image file does not exist.
        ValueError: If image cannot be read.
    """
    image = read_image(image_path)
    return image.shape
