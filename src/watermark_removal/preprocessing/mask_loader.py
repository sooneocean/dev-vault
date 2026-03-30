"""Mask loading and synchronization."""

import json
import logging
from pathlib import Path

import cv2
import numpy as np

from ..core.types import Frame, Mask, MaskType

logger = logging.getLogger(__name__)


class MaskLoader:
    """Load watermark mask from image or JSON bbox file."""

    def __init__(self, mask_path: str) -> None:
        """Initialize mask loader.

        Args:
            mask_path: Path to mask file (PNG/JPEG for image, JSON for bbox).

        Raises:
            FileNotFoundError: If mask file does not exist.
            ValueError: If mask file format is unsupported.
        """
        self.mask_path = Path(mask_path)
        if not self.mask_path.exists():
            raise FileNotFoundError(f"Mask file not found: {self.mask_path}")

        # Detect mask type from extension
        suffix = self.mask_path.suffix.lower()
        if suffix == ".json":
            self.mask_type = MaskType.BBOX
        elif suffix in [".png", ".jpg", ".jpeg"]:
            self.mask_type = MaskType.IMAGE
        else:
            raise ValueError(f"Unsupported mask file format: {suffix}")

        # Cache for loaded mask data
        self._cached_image: np.ndarray | None = None
        self._cached_bbox_data: dict | None = None

        logger.info(f"Mask loader initialized: type={self.mask_type}, path={self.mask_path}")

    def load_for_frame(self, frame: Frame) -> Mask | None:
        """Load mask for a specific frame.

        Args:
            frame: Frame object to get mask for.

        Returns:
            Mask object if mask exists for frame, None otherwise.
        """
        if self.mask_type == MaskType.IMAGE:
            return self._load_image_mask()
        elif self.mask_type == MaskType.BBOX:
            return self._load_bbox_mask(frame.frame_id)
        else:
            raise ValueError(f"Unknown mask type: {self.mask_type}")

    def _load_image_mask(self) -> Mask:
        """Load image mask (cached).

        Returns:
            Mask object with IMAGE type, ndarray data, and valid_frame_range=(0, inf).
        """
        if self._cached_image is None:
            image = cv2.imread(str(self.mask_path), cv2.IMREAD_GRAYSCALE)
            if image is None:
                raise ValueError(f"Failed to read image mask: {self.mask_path}")
            self._cached_image = image
            logger.debug(f"Loaded image mask: {self.mask_path}, shape={image.shape}")

        return Mask(
            type=MaskType.IMAGE,
            data=self._cached_image,
            valid_frame_range=(0, float("inf")),
        )

    def _load_bbox_mask(self, frame_id: int) -> Mask | None:
        """Load bbox mask for specific frame (cached).

        Args:
            frame_id: Frame ID to get bbox for.

        Returns:
            Mask object if bbox exists, None otherwise.
        """
        if self._cached_bbox_data is None:
            with open(self.mask_path, "r") as f:
                data = json.load(f)
            self._cached_bbox_data = data
            logger.debug(f"Loaded bbox mask JSON: {self.mask_path}, frames={list(data.keys())}")

        # Check if frame has a bbox
        frame_key = str(frame_id)
        if frame_key not in self._cached_bbox_data:
            return None

        bbox_dict = self._cached_bbox_data[frame_key]

        return Mask(
            type=MaskType.BBOX,
            data=bbox_dict,
            valid_frame_range=(frame_id, frame_id),
        )
