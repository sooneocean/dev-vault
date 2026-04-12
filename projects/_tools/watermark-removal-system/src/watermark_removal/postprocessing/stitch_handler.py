"""
Stitch inpainted crops back to original frames with feather blending.

Handles rescaling, padding removal, and seamless compositing.
"""

import logging
from typing import Tuple
import numpy as np

from ..core.types import CropRegion

logger = logging.getLogger(__name__)


class StitchHandler:
    """Stitch inpainted crops back to original frames."""

    def __init__(self, blend_feather_width: int = 32):
        """
        Initialize stitch handler.

        Args:
            blend_feather_width: Width of feather mask at crop edges (pixels)
        """
        self.blend_feather_width = blend_feather_width
        logger.info(f"StitchHandler: feather_width={blend_feather_width}px")

    def stitch_back(
        self,
        original_frame: np.ndarray,
        inpainted_crop: np.ndarray,
        crop_region: CropRegion,
    ) -> np.ndarray:
        """
        Stitch inpainted crop back to original frame.

        Args:
            original_frame: Original frame (H, W, 3), uint8
            inpainted_crop: Inpainted crop (1024, 1024, 3), uint8
            crop_region: CropRegion metadata with transformation info

        Returns:
            Stitched frame (H, W, 3), uint8
        """
        try:
            import cv2
        except ImportError:
            logger.error("OpenCV not available for stitch operation")
            return original_frame

        # Step 1: Remove padding from inpainted crop
        unpadded = self._remove_padding(inpainted_crop, crop_region)

        # Step 2: Rescale to original crop size
        rescaled = self._rescale_to_original(unpadded, crop_region)

        # Step 3: Create feather mask
        feather_mask = self._create_feather_mask(rescaled)

        # Step 4: Composite onto original frame
        result = original_frame.copy()
        context_x, context_y, context_w, context_h = crop_region.context_bbox

        # Clamp to frame bounds
        result_x = max(0, context_x)
        result_y = max(0, context_y)
        result_w = min(result.shape[1] - result_x, rescaled.shape[1])
        result_h = min(result.shape[0] - result_y, rescaled.shape[0])

        if result_w <= 0 or result_h <= 0:
            logger.warning(f"Invalid stitch region: {result_x}, {result_y}, {result_w}, {result_h}")
            return original_frame

        # Extract valid regions
        rescaled_crop = rescaled[:result_h, :result_w, :]
        feather_crop = feather_mask[:result_h, :result_w]
        original_crop = result[result_y : result_y + result_h, result_x : result_x + result_w, :]

        # Composite with feather mask (expand mask to 3 channels)
        feather_3ch = np.repeat(feather_crop[:, :, np.newaxis], 3, axis=2)
        composited = (
            original_crop.astype(np.float32) * (1.0 - feather_3ch)
            + rescaled_crop.astype(np.float32) * feather_3ch
        )
        result[result_y : result_y + result_h, result_x : result_x + result_w, :] = np.clip(
            composited, 0, 255
        ).astype(np.uint8)

        logger.debug(f"Stitched crop at ({context_x}, {context_y}) size {context_w}x{context_h}")

        return result

    def _remove_padding(
        self,
        padded_crop: np.ndarray,
        crop_region: CropRegion,
    ) -> np.ndarray:
        """
        Remove zero-padding from inpainted crop.

        Args:
            padded_crop: Padded crop (1024, 1024, 3)
            crop_region: CropRegion with padding info

        Returns:
            Unpadded crop
        """
        pad_top = crop_region.pad_top
        pad_bottom = crop_region.pad_bottom
        pad_left = crop_region.pad_left
        pad_right = crop_region.pad_right

        h_end = padded_crop.shape[0] - pad_bottom if pad_bottom > 0 else padded_crop.shape[0]
        w_end = padded_crop.shape[1] - pad_right if pad_right > 0 else padded_crop.shape[1]

        unpadded = padded_crop[pad_top:h_end, pad_left:w_end, :]

        logger.debug(
            f"Removed padding: {pad_top}, {pad_bottom}, {pad_left}, {pad_right} -> {unpadded.shape}"
        )

        return unpadded

    def _rescale_to_original(
        self,
        crop: np.ndarray,
        crop_region: CropRegion,
    ) -> np.ndarray:
        """
        Rescale crop to original context size.

        Args:
            crop: Unpadded crop
            crop_region: CropRegion with scale_factor

        Returns:
            Rescaled crop (context_h, context_w, 3)
        """
        try:
            import cv2

            scale_factor = crop_region.scale_factor
            _, _, context_w, context_h = crop_region.context_bbox

            # Target size after rescaling
            target_h = context_h
            target_w = context_w

            # Resize to target size
            rescaled = cv2.resize(crop, (target_w, target_h), interpolation=cv2.INTER_CUBIC)

            logger.debug(
                f"Rescaled: {crop.shape} -> {rescaled.shape} (scale={1/scale_factor:.2f})"
            )

            return rescaled
        except ImportError:
            logger.warning("OpenCV not available, returning crop as-is")
            return crop

    def _create_feather_mask(
        self,
        crop: np.ndarray,
    ) -> np.ndarray:
        """
        Create feather mask with soft edges.

        Uses distance transform to create a gradient from edges to center.

        Args:
            crop: Crop image (H, W, 3)

        Returns:
            Feather mask (H, W), float32 in [0, 1]
        """
        try:
            from scipy.ndimage import distance_transform_edt
        except ImportError:
            logger.warning("SciPy not available, using uniform mask")
            return np.ones((crop.shape[0], crop.shape[1]), dtype=np.float32)

        h, w = crop.shape[:2]

        # Create binary mask (all ones inside)
        binary_mask = np.ones((h, w), dtype=np.uint8)

        # Distance transform from edges
        distance = distance_transform_edt(binary_mask)

        # Normalize to [0, 1] with feathering at edges
        feather_width = min(self.blend_feather_width, min(h, w) // 4)
        if feather_width > 0:
            mask = np.clip(distance / feather_width, 0.0, 1.0)
        else:
            mask = np.ones((h, w), dtype=np.float32)

        logger.debug(f"Created feather mask: shape={mask.shape}, width={feather_width}")

        return mask.astype(np.float32)

    @staticmethod
    def compose_with_mask(
        background: np.ndarray,
        foreground: np.ndarray,
        mask: np.ndarray,
        offset_x: int = 0,
        offset_y: int = 0,
    ) -> np.ndarray:
        """
        Composite foreground onto background using mask.

        Args:
            background: Background image (H, W, 3), uint8
            foreground: Foreground image (h, w, 3), uint8
            mask: Alpha mask (h, w), float32 in [0, 1]
            offset_x: X offset for foreground
            offset_y: Y offset for foreground

        Returns:
            Composited image (H, W, 3), uint8
        """
        result = background.copy()
        h, w = foreground.shape[:2]

        # Clamp to background bounds
        x_start = max(0, offset_x)
        y_start = max(0, offset_y)
        x_end = min(background.shape[1], offset_x + w)
        y_end = min(background.shape[0], offset_y + h)

        fg_x_start = max(0, -offset_x)
        fg_y_start = max(0, -offset_y)
        fg_x_end = fg_x_start + (x_end - x_start)
        fg_y_end = fg_y_start + (y_end - y_start)

        if x_end <= x_start or y_end <= y_start or fg_x_end <= fg_x_start or fg_y_end <= fg_y_start:
            return result

        # Extract regions
        bg_region = result[y_start:y_end, x_start:x_end, :]
        fg_region = foreground[fg_y_start:fg_y_end, fg_x_start:fg_x_end, :]
        mask_region = mask[fg_y_start:fg_y_end, fg_x_start:fg_x_end]

        # Expand mask to 3 channels
        mask_3ch = np.repeat(mask_region[:, :, np.newaxis], 3, axis=2)

        # Composite
        composited = (
            bg_region.astype(np.float32) * (1.0 - mask_3ch)
            + fg_region.astype(np.float32) * mask_3ch
        )
        result[y_start:y_end, x_start:x_end, :] = np.clip(composited, 0, 255).astype(np.uint8)

        return result
