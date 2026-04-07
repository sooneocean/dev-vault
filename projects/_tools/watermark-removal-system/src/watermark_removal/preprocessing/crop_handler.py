"""
Intelligent crop region computation from watermark masks.

Generates crop boxes with context padding and handles rescaling for inpaint models.
"""

import logging
from typing import Tuple, Optional
import numpy as np

from ..core.types import CropRegion

logger = logging.getLogger(__name__)


class CropHandler:
    """
    Compute and manage crop regions for inpainted watermark masks.

    Handles context padding, scaling, and precise crop-to-stitch mapping.
    """

    def __init__(
        self,
        context_padding: int = 64,
        target_size: int = 1024,
    ):
        """
        Initialize crop handler.

        Args:
            context_padding: Padding around watermark for context (pixels)
            target_size: Target size for inpaint model (assumes square)
        """
        self.context_padding = context_padding
        self.target_size = target_size
        logger.info(
            f"CropHandler: context={context_padding}px, target={target_size}x{target_size}"
        )

    def compute_crop_region(
        self,
        frame_id: int,
        watermark_bbox: Tuple[float, float, float, float],
        frame_shape: Tuple[int, int, int],
        watermark_id: int = 0,
    ) -> Optional[CropRegion]:
        """
        Compute crop region from watermark bbox.

        Args:
            frame_id: Frame index
            watermark_bbox: Watermark bbox (x, y, w, h)
            frame_shape: Frame shape (H, W, C)
            watermark_id: ID for multi-watermark support (0-indexed, Phase 2)

        Returns:
            CropRegion metadata, or None if bbox invalid
        """
        if not self._validate_bbox(watermark_bbox, frame_shape):
            logger.warning(f"Invalid watermark bbox: {watermark_bbox}")
            return None

        frame_h, frame_w, _ = frame_shape
        x, y, w, h = [float(v) for v in watermark_bbox]

        # Compute context bbox: original + padding
        context_x = max(0, x - self.context_padding)
        context_y = max(0, y - self.context_padding)
        context_x_end = min(frame_w, context_x + w + 2 * self.context_padding)
        context_y_end = min(frame_h, context_y + h + 2 * self.context_padding)
        context_w = context_x_end - context_x
        context_h = context_y_end - context_y

        # Compute scaling factor (target_size = max(context_w, context_h) * scale)
        max_context = max(context_w, context_h)
        scale_factor = self.target_size / max_context if max_context > 0 else 1.0

        # Compute padding for zero-padding if context smaller than target
        resized_w = int(context_w * scale_factor)
        resized_h = int(context_h * scale_factor)

        pad_left = (self.target_size - resized_w) // 2
        pad_top = (self.target_size - resized_h) // 2
        pad_right = self.target_size - resized_w - pad_left
        pad_bottom = self.target_size - resized_h - pad_top

        crop = CropRegion(
            frame_id=frame_id,
            original_bbox=(int(x), int(y), int(w), int(h)),
            context_bbox=(int(context_x), int(context_y), int(context_w), int(context_h)),
            scale_factor=scale_factor,
            watermark_id=watermark_id,
            pad_left=pad_left,
            pad_top=pad_top,
            pad_right=pad_right,
            pad_bottom=pad_bottom,
        )

        logger.debug(
            f"Frame {frame_id}: original={watermark_bbox}, "
            f"context={context_w}x{context_h}, scale={scale_factor:.2f}"
        )

        return crop

    def extract_crop(
        self,
        frame: np.ndarray,
        crop_region: CropRegion,
    ) -> Optional[np.ndarray]:
        """
        Extract and resize crop region from frame.

        Args:
            frame: Input frame (H, W, 3), uint8
            crop_region: CropRegion metadata

        Returns:
            Cropped and resized region (target_size, target_size, 3), or None
        """
        try:
            import cv2
        except ImportError:
            logger.error("OpenCV not available for crop extraction")
            return None

        x, y, w, h = crop_region.context_bbox

        # Extract context region
        crop = frame[y : y + h, x : x + w, :]

        if crop.size == 0:
            logger.error(f"Empty crop region: {crop_region.context_bbox}")
            return None

        # Resize crop
        resized_w = int(w * crop_region.scale_factor)
        resized_h = int(h * crop_region.scale_factor)
        resized = cv2.resize(crop, (resized_w, resized_h), interpolation=cv2.INTER_CUBIC)

        # Zero-pad to target size
        padded = cv2.copyMakeBorder(
            resized,
            crop_region.pad_top,
            crop_region.pad_bottom,
            crop_region.pad_left,
            crop_region.pad_right,
            cv2.BORDER_CONSTANT,
            value=[0, 0, 0],
        )

        if padded.shape[0] != self.target_size or padded.shape[1] != self.target_size:
            logger.warning(
                f"Padded crop {padded.shape} doesn't match target {self.target_size}"
            )

        return padded

    def get_inpaint_region(
        self, crop_region: CropRegion
    ) -> Tuple[int, int, int, int]:
        """
        Get inpainting region bbox within padded crop.

        Region to inpaint in the padded crop (within target_size bounds).

        Args:
            crop_region: CropRegion metadata

        Returns:
            (x_start, y_start, x_end, y_end) in padded crop coordinates
        """
        # Watermark bbox relative to context
        context_x, context_y, _, _ = crop_region.context_bbox
        orig_x, orig_y, orig_w, orig_h = crop_region.original_bbox

        # Offset within context
        offset_x = orig_x - context_x
        offset_y = orig_y - context_y

        # After scaling
        scaled_x = int(offset_x * crop_region.scale_factor)
        scaled_y = int(offset_y * crop_region.scale_factor)
        scaled_w = int(orig_w * crop_region.scale_factor)
        scaled_h = int(orig_h * crop_region.scale_factor)

        # After padding
        x_start = scaled_x + crop_region.pad_left
        y_start = scaled_y + crop_region.pad_top
        x_end = x_start + scaled_w
        y_end = y_start + scaled_h

        return (
            max(0, x_start),
            max(0, y_start),
            min(self.target_size, x_end),
            min(self.target_size, y_end),
        )

    @staticmethod
    def _validate_bbox(
        bbox: Tuple[float, float, float, float],
        frame_shape: Tuple[int, int, int],
    ) -> bool:
        """
        Validate bbox is within frame bounds.

        Args:
            bbox: (x, y, w, h)
            frame_shape: (H, W, C)

        Returns:
            True if valid
        """
        x, y, w, h = bbox
        frame_h, frame_w, _ = frame_shape

        if x < 0 or y < 0 or w <= 0 or h <= 0:
            return False

        if x + w > frame_w or y + h > frame_h:
            return False

        return True
