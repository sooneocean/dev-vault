"""Serialization of CropRegion metadata for checkpoint resumption."""

import json
import logging
from pathlib import Path
from typing import Dict

from ..core.types import CropRegion

logger = logging.getLogger(__name__)


class CropRegionSerializer:
    """Save and load CropRegion metadata to JSON for resumption."""

    @staticmethod
    def serialize(crop_regions: Dict[int, CropRegion]) -> str:
        """Serialize crop regions to JSON string.

        Args:
            crop_regions: Dictionary mapping frame index to CropRegion.

        Returns:
            JSON string representation of crop regions.
        """
        if not crop_regions:
            return json.dumps({})

        # Convert each CropRegion to dict
        serialized = {}
        for frame_idx, crop in crop_regions.items():
            serialized[str(frame_idx)] = {
                "x": crop.x,
                "y": crop.y,
                "w": crop.w,
                "h": crop.h,
                "scale_factor": crop.scale_factor,
                "context_x": crop.context_x,
                "context_y": crop.context_y,
                "context_w": crop.context_w,
                "context_h": crop.context_h,
                "pad_left": crop.pad_left,
                "pad_top": crop.pad_top,
                "pad_right": crop.pad_right,
                "pad_bottom": crop.pad_bottom,
            }

        return json.dumps(serialized, indent=2)

    @staticmethod
    def deserialize(json_str: str) -> Dict[int, CropRegion]:
        """Deserialize crop regions from JSON string.

        Args:
            json_str: JSON string representation of crop regions.

        Returns:
            Dictionary mapping frame index to CropRegion.

        Raises:
            json.JSONDecodeError: If JSON is invalid.
            ValueError: If crop data is malformed.
        """
        if not json_str.strip():
            return {}

        data = json.loads(json_str)
        if not data:
            return {}

        crop_regions = {}
        for frame_idx_str, crop_data in data.items():
            try:
                frame_idx = int(frame_idx_str)

                crop = CropRegion(
                    x=int(crop_data["x"]),
                    y=int(crop_data["y"]),
                    w=int(crop_data["w"]),
                    h=int(crop_data["h"]),
                    scale_factor=float(crop_data["scale_factor"]),
                    context_x=int(crop_data["context_x"]),
                    context_y=int(crop_data["context_y"]),
                    context_w=int(crop_data["context_w"]),
                    context_h=int(crop_data["context_h"]),
                    pad_left=int(crop_data.get("pad_left", 0)),
                    pad_top=int(crop_data.get("pad_top", 0)),
                    pad_right=int(crop_data.get("pad_right", 0)),
                    pad_bottom=int(crop_data.get("pad_bottom", 0)),
                )

                crop_regions[frame_idx] = crop

            except (KeyError, ValueError, TypeError) as e:
                raise ValueError(
                    f"Malformed crop data for frame {frame_idx_str}: {e}"
                ) from e

        return crop_regions

    @staticmethod
    def save_checkpoint(
        crop_regions: Dict[int, CropRegion],
        output_dir: str,
        filename: str = "checkpoint_crops.json",
    ) -> Path:
        """Save crop regions to checkpoint file.

        Args:
            crop_regions: Dictionary mapping frame index to CropRegion.
            output_dir: Output directory for checkpoint file.
            filename: Checkpoint filename (default: checkpoint_crops.json).

        Returns:
            Path to saved checkpoint file.

        Raises:
            IOError: If file write fails.
        """
        output_path = Path(output_dir) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        json_str = CropRegionSerializer.serialize(crop_regions)

        with open(output_path, "w") as f:
            f.write(json_str)

        logger.info(f"Saved crop checkpoint: {output_path} ({len(crop_regions)} regions)")
        return output_path

    @staticmethod
    def load_checkpoint(
        output_dir: str,
        filename: str = "checkpoint_crops.json",
    ) -> Dict[int, CropRegion] | None:
        """Load crop regions from checkpoint file if it exists.

        Args:
            output_dir: Output directory to check for checkpoint file.
            filename: Checkpoint filename (default: checkpoint_crops.json).

        Returns:
            Dictionary of crop regions, or None if checkpoint doesn't exist.

        Raises:
            ValueError: If checkpoint JSON is malformed.
        """
        checkpoint_path = Path(output_dir) / filename

        if not checkpoint_path.exists():
            logger.info(f"No checkpoint found at {checkpoint_path}")
            return None

        try:
            with open(checkpoint_path, "r") as f:
                json_str = f.read()

            crop_regions = CropRegionSerializer.deserialize(json_str)
            logger.info(
                f"Loaded crop checkpoint: {checkpoint_path} ({len(crop_regions)} regions)"
            )
            return crop_regions

        except Exception as e:
            logger.error(f"Failed to load checkpoint {checkpoint_path}: {e}")
            raise
