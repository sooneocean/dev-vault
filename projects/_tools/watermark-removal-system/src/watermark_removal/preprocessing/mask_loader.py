"""
Load and validate watermark masks (static images or dynamic bounding box sequences).

Supports JPEG/PNG mask images and JSON bbox sequences for flexible watermark handling.
"""

import logging
import json
from pathlib import Path
from typing import Optional, Union, Dict, List, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class MaskLoader:
    """
    Load watermark masks from file (image or JSON bbox sequence).

    Handles both static masks (JPEG/PNG) and dynamic masks (JSON bbox coordinates).
    """

    def __init__(self):
        """Initialize mask loader."""
        pass

    @staticmethod
    def load_image_mask(mask_path: Union[str, Path]) -> Optional[np.ndarray]:
        """
        Load mask from image file (JPEG/PNG).

        Args:
            mask_path: Path to mask image

        Returns:
            Grayscale mask ndarray (H, W), uint8, or None if load fails
        """
        mask_path = Path(mask_path)

        if not mask_path.exists():
            logger.error(f"Mask file not found: {mask_path}")
            return None

        try:
            import cv2

            # Load as grayscale
            mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)

            if mask is None:
                logger.error(f"Failed to load mask image: {mask_path}")
                return None

            logger.info(f"Loaded image mask: {mask_path} ({mask.shape})")
            return mask

        except ImportError:
            logger.warning("OpenCV not available; cannot load image mask")
            return None
        except Exception as e:
            logger.error(f"Error loading mask image: {e}")
            return None

    @staticmethod
    def load_bbox_sequence(bbox_path: Union[str, Path]) -> Optional[Dict[int, Tuple[float, float, float, float]]]:
        """
        Load bbox sequence from JSON file.

        Expected format: { "frame_id": [x, y, w, h], ... }
        or { "frames": [{"id": frame_id, "bbox": [x, y, w, h]}, ...] }

        Args:
            bbox_path: Path to JSON bbox file

        Returns:
            Dict mapping frame_id -> (x, y, w, h) bbox, or None if load fails
        """
        bbox_path = Path(bbox_path)

        if not bbox_path.exists():
            logger.error(f"Bbox file not found: {bbox_path}")
            return None

        try:
            with open(bbox_path, "r") as f:
                data = json.load(f)

            bboxes = {}

            # Handle different JSON formats
            if "frames" in data:
                # Format: {"frames": [{"id": 0, "bbox": [x, y, w, h]}, ...]}
                for frame_data in data["frames"]:
                    frame_id = frame_data["id"]
                    bbox = tuple(frame_data["bbox"])
                    bboxes[frame_id] = bbox
            else:
                # Format: {"0": [x, y, w, h], "1": [...], ...}
                for frame_id_str, bbox in data.items():
                    try:
                        frame_id = int(frame_id_str)
                        bboxes[frame_id] = tuple(bbox)
                    except (ValueError, TypeError):
                        logger.warning(f"Skipping invalid frame entry: {frame_id_str}")

            if not bboxes:
                logger.error(f"No valid bboxes found in {bbox_path}")
                return None

            logger.info(f"Loaded {len(bboxes)} bbox frames from {bbox_path}")
            return bboxes

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in bbox file: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading bbox file: {e}")
            return None

    def load_mask(self, mask_path: Union[str, Path]) -> Optional[Union[np.ndarray, Dict]]:
        """
        Load mask from file (auto-detect type: image or JSON).

        Args:
            mask_path: Path to mask file (image or JSON)

        Returns:
            Mask data (ndarray for image, dict for bbox), or None
        """
        mask_path = Path(mask_path)

        # Detect file type by extension
        if mask_path.suffix.lower() in [".json"]:
            return self.load_bbox_sequence(mask_path)
        elif mask_path.suffix.lower() in [".png", ".jpg", ".jpeg"]:
            return self.load_image_mask(mask_path)
        else:
            logger.error(f"Unsupported mask file type: {mask_path.suffix}")
            return None

    @staticmethod
    def validate_image_mask(mask: np.ndarray, frame_shape: Tuple[int, int, int]) -> bool:
        """
        Validate image mask against frame dimensions.

        Args:
            mask: Mask ndarray (H, W)
            frame_shape: Frame shape (H, W, C)

        Returns:
            True if mask is valid for frame
        """
        if mask.ndim != 2:
            logger.error(f"Mask must be 2D, got shape {mask.shape}")
            return False

        frame_h, frame_w, _ = frame_shape

        if mask.shape[0] != frame_h or mask.shape[1] != frame_w:
            logger.error(
                f"Mask shape {mask.shape} doesn't match frame {(frame_h, frame_w)}"
            )
            return False

        if mask.dtype != np.uint8:
            logger.warning(f"Mask dtype {mask.dtype} not uint8, will convert")
            return True

        return True

    @staticmethod
    def validate_bbox(bbox: Tuple[float, float, float, float], frame_shape: Tuple[int, int, int]) -> bool:
        """
        Validate bbox coordinates against frame dimensions.

        Args:
            bbox: Bounding box (x, y, w, h)
            frame_shape: Frame shape (H, W, C)

        Returns:
            True if bbox is valid
        """
        x, y, w, h = bbox
        frame_h, frame_w, _ = frame_shape

        if x < 0 or y < 0 or w <= 0 or h <= 0:
            logger.error(f"Invalid bbox coordinates: {bbox}")
            return False

        if x + w > frame_w or y + h > frame_h:
            logger.warning(f"Bbox {bbox} exceeds frame bounds {(frame_w, frame_h)}")
            return False

        return True

    @staticmethod
    def create_mask_from_bbox(
        bbox: Tuple[float, float, float, float],
        frame_shape: Tuple[int, int, int],
        feather: int = 0,
    ) -> np.ndarray:
        """
        Create binary mask from bbox coordinates.

        Args:
            bbox: Bounding box (x, y, w, h)
            frame_shape: Frame shape (H, W, C)
            feather: Feather mask edges by this many pixels

        Returns:
            Binary mask (H, W), uint8
        """
        frame_h, frame_w, _ = frame_shape
        mask = np.zeros((frame_h, frame_w), dtype=np.uint8)

        x, y, w, h = [int(v) for v in bbox]

        # Clamp bbox to frame
        x_start = max(0, x)
        y_start = max(0, y)
        x_end = min(frame_w, x + w)
        y_end = min(frame_h, y + h)

        # Fill bbox region
        mask[y_start:y_end, x_start:x_end] = 255

        # Optional feathering
        if feather > 0:
            try:
                from scipy.ndimage import gaussian_filter

                mask = gaussian_filter(mask.astype(np.float32), sigma=feather)
                mask = (mask * 255).astype(np.uint8)
            except ImportError:
                logger.warning("SciPy not available; feathering skipped")

        return mask
