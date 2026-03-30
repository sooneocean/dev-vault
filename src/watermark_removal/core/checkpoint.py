"""Checkpoint serialization and resumption for long video processing."""

import json
import logging
from pathlib import Path
from typing import Any, Dict

from .types import CropRegion
from ..persistence.crop_serializer import CropRegionSerializer

logger = logging.getLogger(__name__)

# Checkpoint format version for future compatibility
# Aligned with CropRegionSerializer 1.2 for crop metadata
CHECKPOINT_VERSION = "1.0"


class Checkpoint:
    """Save and load processing state for resumption after interruption."""

    def __init__(self, checkpoint_path: Path | str):
        """Initialize checkpoint manager.

        Args:
            checkpoint_path: Path to checkpoint file (JSON format).
        """
        self.checkpoint_path = Path(checkpoint_path)

    def save_preprocessing_state(
        self,
        crop_regions: Dict[int, CropRegion],
        frame_count: int,
    ) -> None:
        """Save state after preprocessing (crop_regions only).

        Args:
            crop_regions: Dictionary mapping frame index to CropRegion.
            frame_count: Total number of frames processed.

        Raises:
            IOError: If checkpoint file cannot be written.
        """
        # Use CropRegionSerializer to build crop_regions part
        crop_regions_json = CropRegionSerializer.serialize(crop_regions)
        crop_regions_data = json.loads(crop_regions_json)

        state = {
            "version": CHECKPOINT_VERSION,
            "stage": "preprocessing",
            "frame_count": frame_count,
            "crop_regions": crop_regions_data,
            "inpaint_results": {},
        }

        try:
            self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.checkpoint_path, "w") as f:
                json.dump(state, f, indent=2)
            logger.info(
                f"Saved preprocessing checkpoint with {len(crop_regions)} crops "
                f"to {self.checkpoint_path}"
            )
        except IOError as e:
            logger.error(f"Failed to save preprocessing checkpoint: {e}")
            raise

    def save_inpaint_state(
        self,
        crop_regions: Dict[int, CropRegion],
        inpaint_results: Dict[int, Any],
        frame_count: int,
    ) -> None:
        """Save state after inpainting (crops + results).

        Args:
            crop_regions: Dictionary mapping frame index to CropRegion.
            inpaint_results: Dictionary mapping frame index to inpaint output.
            frame_count: Total number of frames processed.

        Raises:
            IOError: If checkpoint file cannot be written.
        """
        # Use CropRegionSerializer to build crop_regions part
        crop_regions_json = CropRegionSerializer.serialize(crop_regions)
        crop_regions_data = json.loads(crop_regions_json)

        state = {
            "version": CHECKPOINT_VERSION,
            "stage": "inpaint",
            "frame_count": frame_count,
            "crop_regions": crop_regions_data,
            "inpaint_results": {
                str(k): v.tolist() if hasattr(v, "tolist") else v
                for k, v in inpaint_results.items()
            },
        }

        try:
            self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.checkpoint_path, "w") as f:
                json.dump(state, f, indent=2)
            logger.info(
                f"Saved inpaint checkpoint with {len(inpaint_results)} results "
                f"to {self.checkpoint_path}"
            )
        except IOError as e:
            logger.error(f"Failed to save inpaint checkpoint: {e}")
            raise

    def load(self) -> Dict[str, Any]:
        """Load checkpoint from file.

        Returns:
            Dictionary with checkpoint state:
            - version: Checkpoint format version
            - stage: Processing stage (preprocessing or inpaint)
            - frame_count: Total frames in checkpoint
            - crop_regions: Dict[int, CropRegion]
            - inpaint_results: Dict[int, Any]

        Raises:
            FileNotFoundError: If checkpoint file does not exist.
            ValueError: If checkpoint JSON is corrupted or incompatible.
        """
        if not self.checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint file not found: {self.checkpoint_path}")

        try:
            with open(self.checkpoint_path, "r") as f:
                state = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Corrupted checkpoint file (invalid JSON): {e}") from e
        except IOError as e:
            raise FileNotFoundError(f"Failed to read checkpoint: {e}") from e

        # Version compatibility check
        version = state.get("version", "unknown")
        if version != CHECKPOINT_VERSION:
            logger.warning(
                f"Checkpoint version {version} does not match current {CHECKPOINT_VERSION}. "
                "Starting from scratch."
            )
            # Do not raise; let caller decide to proceed or retry
            raise ValueError(f"Checkpoint version mismatch: {version} vs {CHECKPOINT_VERSION}")

        # Deserialize crop_regions using CropRegionSerializer
        # The crop_regions_data in state includes version/crop_regions structure
        crop_regions_json = json.dumps(state.get("crop_regions", {}))
        crop_regions, _ = CropRegionSerializer.deserialize(crop_regions_json)

        # Parse inpaint results (stored as lists in JSON)
        inpaint_results = {}
        for frame_idx_str, result_data in state.get("inpaint_results", {}).items():
            frame_idx = int(frame_idx_str)
            inpaint_results[frame_idx] = result_data

        return {
            "version": version,
            "stage": state.get("stage", "unknown"),
            "frame_count": state.get("frame_count", 0),
            "crop_regions": crop_regions,
            "inpaint_results": inpaint_results,
        }

    def exists(self) -> bool:
        """Check if checkpoint file exists.

        Returns:
            bool: True if checkpoint file exists, False otherwise.
        """
        return self.checkpoint_path.exists()

    def delete(self) -> None:
        """Delete checkpoint file.

        Raises:
            FileNotFoundError: If checkpoint file does not exist.
        """
        if not self.checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint file not found: {self.checkpoint_path}")
        self.checkpoint_path.unlink()
        logger.info(f"Deleted checkpoint: {self.checkpoint_path}")
