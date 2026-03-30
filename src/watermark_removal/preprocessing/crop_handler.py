"""Crop watermark region with context padding and resizing."""

import logging

import cv2
import numpy as np

from ..core.types import CropRegion, Frame, Mask, MaskType

logger = logging.getLogger(__name__)


class CropHandler:
    """Extract and resize watermark crop region."""

    def __init__(
        self,
        context_padding: int = 50,
        target_inpaint_size: int = 1024,
    ) -> None:
        """Initialize crop handler.

        Args:
            context_padding: Extra pixels to add around bbox on all sides.
            target_inpaint_size: Target size for resized crop (1024x1024 default).
        """
        self.context_padding = context_padding
        self.target_inpaint_size = target_inpaint_size

    def crop_with_context(self, frame: Frame, mask: Mask) -> tuple[np.ndarray, CropRegion]:
        """Extract watermark crop with context padding and resize to inpaint size.

        Args:
            frame: Frame object with image.
            mask: Mask object with watermark location.

        Returns:
            Tuple of (resized_crop_image, CropRegion metadata).

        Raises:
            ValueError: If mask has no valid watermark region.
        """
        # Step 1: Extract bbox from mask
        x, y, w, h = self._extract_bbox_from_mask(frame, mask)

        if w <= 0 or h <= 0:
            raise ValueError("Invalid watermark region: width and height must be positive")

        frame_h, frame_w = frame.image.shape[:2]

        # Step 2: Compute context region (with padding and clamping)
        context_x = max(0, x - self.context_padding)
        context_y = max(0, y - self.context_padding)
        context_w = min(frame_w - context_x, w + 2 * self.context_padding)
        context_h = min(frame_h - context_y, h + 2 * self.context_padding)

        # Step 3: Crop from frame
        cropped = frame.image[context_y : context_y + context_h, context_x : context_x + context_w]

        # Step 4: Resize to target size, maintaining aspect ratio and padding
        resized_crop, scale_factor, pad_left, pad_top = self._resize_and_pad(
            cropped, self.target_inpaint_size
        )

        # Step 5: Generate inpaint mask (0=keep, 255=inpaint)
        inpaint_mask = self._generate_inpaint_mask(
            resized_crop, x - context_x, y - context_y, w, h, scale_factor, pad_left, pad_top
        )

        # Step 6: Record transformation metadata
        crop_region = CropRegion(
            x=x,
            y=y,
            w=w,
            h=h,
            scale_factor=scale_factor,
            context_x=context_x,
            context_y=context_y,
            context_w=context_w,
            context_h=context_h,
            pad_left=pad_left,
            pad_top=pad_top,
            pad_right=self.target_inpaint_size - (pad_left + int(context_w * scale_factor)),
            pad_bottom=self.target_inpaint_size - (pad_top + int(context_h * scale_factor)),
        )

        logger.debug(
            f"Cropped frame {frame.frame_id}: orig=({x},{y},{w},{h}) "
            f"context=({context_x},{context_y},{context_w},{context_h}) "
            f"scale={scale_factor:.3f}"
        )

        return resized_crop, crop_region

    def _extract_bbox_from_mask(self, frame: Frame, mask: Mask) -> tuple[int, int, int, int]:
        """Extract bounding box from mask (either contours or dict).

        Args:
            frame: Frame object (used for image dimensions).
            mask: Mask object.

        Returns:
            Tuple of (x, y, w, h) in original frame coordinates.

        Raises:
            ValueError: If mask has no valid watermark region.
        """
        if mask.type == MaskType.IMAGE:
            return self._extract_bbox_from_image_mask(mask.data)
        elif mask.type == MaskType.BBOX:
            return self._extract_bbox_from_dict(mask.data)
        else:
            raise ValueError(f"Unknown mask type: {mask.type}")

    def _extract_bbox_from_image_mask(self, mask_image: np.ndarray) -> tuple[int, int, int, int]:
        """Extract bbox from binary image mask using contours.

        Args:
            mask_image: Grayscale mask image.

        Returns:
            Tuple of (x, y, w, h).

        Raises:
            ValueError: If no contours found.
        """
        # Ensure binary
        _, binary = cv2.threshold(mask_image, 127, 255, cv2.THRESH_BINARY)

        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            raise ValueError("No watermark contours found in mask image")

        # Get bounding rect of all contours
        x_min, y_min = float("inf"), float("inf")
        x_max, y_max = 0, 0

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            x_min = min(x_min, x)
            y_min = min(y_min, y)
            x_max = max(x_max, x + w)
            y_max = max(y_max, y + h)

        x = int(x_min)
        y = int(y_min)
        w = int(x_max - x_min)
        h = int(y_max - y_min)

        return x, y, w, h

    def _extract_bbox_from_dict(self, bbox_dict: dict) -> tuple[int, int, int, int]:
        """Extract bbox from dict with x, y, w, h keys.

        Args:
            bbox_dict: Dict with keys x, y, w, h.

        Returns:
            Tuple of (x, y, w, h).
        """
        return bbox_dict["x"], bbox_dict["y"], bbox_dict["w"], bbox_dict["h"]

    def _resize_and_pad(
        self, image: np.ndarray, target_size: int
    ) -> tuple[np.ndarray, float, int, int]:
        """Resize image to fit target size, maintaining aspect ratio, and pad to square.

        Args:
            image: Input image.
            target_size: Target output size (default 1024x1024).

        Returns:
            Tuple of (padded_image, scale_factor, pad_left, pad_top).
        """
        h, w = image.shape[:2]
        max_dim = max(h, w)

        # Scale to fit largest dimension into target_size
        scale_factor = target_size / max_dim
        new_w = int(w * scale_factor)
        new_h = int(h * scale_factor)

        # Resize
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        # Pad to square (centered)
        pad_left = (target_size - new_w) // 2
        pad_top = (target_size - new_h) // 2
        pad_right = target_size - new_w - pad_left
        pad_bottom = target_size - new_h - pad_top

        padded = cv2.copyMakeBorder(
            resized,
            pad_top,
            pad_bottom,
            pad_left,
            pad_right,
            cv2.BORDER_CONSTANT,
            value=(0, 0, 0),
        )

        return padded, scale_factor, pad_left, pad_top

    def _generate_inpaint_mask(
        self,
        resized_crop: np.ndarray,
        bbox_x_in_crop: int,
        bbox_y_in_crop: int,
        bbox_w: int,
        bbox_h: int,
        scale_factor: float,
        pad_left: int,
        pad_top: int,
    ) -> np.ndarray:
        """Generate inpaint mask (0=keep, 255=inpaint) in resized space.

        Args:
            resized_crop: Resized crop image.
            bbox_x_in_crop: Bbox x coordinate in cropped (pre-resized) space.
            bbox_y_in_crop: Bbox y coordinate in cropped (pre-resized) space.
            bbox_w: Bbox width.
            bbox_h: Bbox height.
            scale_factor: Scale applied during resize.
            pad_left: Left padding applied.
            pad_top: Top padding applied.

        Returns:
            Binary mask (0/255).
        """
        mask = np.zeros(resized_crop.shape[:2], dtype=np.uint8)

        # Map bbox to resized space
        resized_x = int(bbox_x_in_crop * scale_factor + pad_left)
        resized_y = int(bbox_y_in_crop * scale_factor + pad_top)
        resized_w = int(bbox_w * scale_factor)
        resized_h = int(bbox_h * scale_factor)

        # Clamp to image bounds
        resized_x = max(0, resized_x)
        resized_y = max(0, resized_y)
        resized_x_end = min(mask.shape[1], resized_x + resized_w)
        resized_y_end = min(mask.shape[0], resized_y + resized_h)

        # Draw inpaint region (255 = inpaint)
        mask[resized_y:resized_y_end, resized_x:resized_x_end] = 255

        return mask
