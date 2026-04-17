"""
Checkpoint management for resumable pipeline execution.

Enables saving/loading pipeline state (CropRegion metadata) for interrupted videos.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import asdict

from .types import CropRegion

logger = logging.getLogger(__name__)


class CheckpointManager:
    """
    Manage pipeline checkpoints for resumable execution.

    Serializes CropRegion data and processing state to JSON for restart capability.
    """

    def __init__(self, checkpoint_dir: Path):
        """
        Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory for checkpoint files
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Checkpoint manager initialized at {self.checkpoint_dir}")

    def get_checkpoint_path(self, video_name: str) -> Path:
        """
        Get checkpoint file path for a video.

        Args:
            video_name: Video filename (without extension)

        Returns:
            Path to checkpoint file
        """
        return self.checkpoint_dir / f"{video_name}_checkpoint.json"

    def save_crop_regions(
        self,
        video_name: str,
        crop_regions: List[CropRegion],
        processing_state: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Save crop regions and processing state to checkpoint.

        Args:
            video_name: Video filename (without extension)
            crop_regions: List of CropRegion objects
            processing_state: Optional dict with processing metadata (e.g., inpainted frames)

        Returns:
            Path to saved checkpoint file
        """
        checkpoint_path = self.get_checkpoint_path(video_name)

        # Serialize CropRegions to JSON-compatible dicts
        crops_data = []
        for crop in crop_regions:
            crops_data.append(asdict(crop))

        checkpoint = {
            "version": "1.0",
            "video_name": video_name,
            "num_frames": len(crop_regions),
            "crop_regions": crops_data,
            "processing_state": processing_state or {},
        }

        # Write to JSON
        with open(checkpoint_path, "w") as f:
            json.dump(checkpoint, f, indent=2)

        logger.info(f"Saved checkpoint: {checkpoint_path} ({len(crop_regions)} regions)")
        return checkpoint_path

    def load_crop_regions(self, video_name: str) -> tuple[List[CropRegion], Dict[str, Any]]:
        """
        Load crop regions and processing state from checkpoint.

        Args:
            video_name: Video filename (without extension)

        Returns:
            (List of CropRegion objects, processing state dict)
            Returns ([], {}) if checkpoint doesn't exist
        """
        checkpoint_path = self.get_checkpoint_path(video_name)

        if not checkpoint_path.exists():
            logger.warning(f"Checkpoint not found: {checkpoint_path}")
            return [], {}

        try:
            with open(checkpoint_path, "r") as f:
                checkpoint = json.load(f)

            # Deserialize CropRegions
            crop_regions = []
            for crop_data in checkpoint.get("crop_regions", []):
                crop = CropRegion(
                    frame_id=crop_data["frame_id"],
                    original_bbox=tuple(crop_data["original_bbox"]),
                    context_bbox=tuple(crop_data["context_bbox"]),
                    scale_factor=crop_data["scale_factor"],
                    pad_left=crop_data.get("pad_left", 0),
                    pad_top=crop_data.get("pad_top", 0),
                    pad_right=crop_data.get("pad_right", 0),
                    pad_bottom=crop_data.get("pad_bottom", 0),
                )
                crop_regions.append(crop)

            processing_state = checkpoint.get("processing_state", {})
            logger.info(f"Loaded checkpoint: {checkpoint_path} ({len(crop_regions)} regions)")
            return crop_regions, processing_state

        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return [], {}

    def checkpoint_exists(self, video_name: str) -> bool:
        """
        Check if checkpoint exists for a video.

        Args:
            video_name: Video filename (without extension)

        Returns:
            True if checkpoint file exists
        """
        return self.get_checkpoint_path(video_name).exists()

    def delete_checkpoint(self, video_name: str) -> bool:
        """
        Delete checkpoint file for a video.

        Args:
            video_name: Video filename (without extension)

        Returns:
            True if deletion successful
        """
        checkpoint_path = self.get_checkpoint_path(video_name)

        if checkpoint_path.exists():
            try:
                checkpoint_path.unlink()
                logger.info(f"Deleted checkpoint: {checkpoint_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete checkpoint: {e}")
                return False

        return False

    def list_checkpoints(self) -> List[str]:
        """
        List all available checkpoints.

        Returns:
            List of video names with checkpoints
        """
        checkpoints = []
        for checkpoint_file in self.checkpoint_dir.glob("*_checkpoint.json"):
            video_name = checkpoint_file.stem.replace("_checkpoint", "")
            checkpoints.append(video_name)

        logger.info(f"Found {len(checkpoints)} checkpoints")
        return checkpoints


class ResumableFrameProcessor:
    """
    Wrapper for resumable frame processing using checkpoints.

    Tracks processed frames and skips already-inpainted regions on resume.
    """

    def __init__(self, checkpoint_manager: CheckpointManager):
        """
        Initialize resumable processor.

        Args:
            checkpoint_manager: Checkpoint manager instance
        """
        self.checkpoint_manager = checkpoint_manager
        self.processed_frames: set = set()

    def load_checkpoint(self, video_name: str) -> tuple[List[CropRegion], set]:
        """
        Load checkpoint and return processed frame IDs.

        Args:
            video_name: Video filename

        Returns:
            (crop_regions, set of processed frame IDs)
        """
        crop_regions, processing_state = self.checkpoint_manager.load_crop_regions(video_name)
        processed_frames = set(processing_state.get("processed_frames", []))
        self.processed_frames = processed_frames

        logger.info(f"Loaded {len(processed_frames)} previously processed frames")
        return crop_regions, processed_frames

    def mark_frame_processed(self, frame_id: int) -> None:
        """
        Mark a frame as processed.

        Args:
            frame_id: Frame index
        """
        self.processed_frames.add(frame_id)

    def is_frame_processed(self, frame_id: int) -> bool:
        """
        Check if frame was already processed.

        Args:
            frame_id: Frame index

        Returns:
            True if frame was processed
        """
        return frame_id in self.processed_frames

    def save_checkpoint(self, video_name: str, crop_regions: List[CropRegion]) -> Path:
        """
        Save checkpoint with current processed frames.

        Args:
            video_name: Video filename
            crop_regions: List of CropRegion objects

        Returns:
            Path to checkpoint file
        """
        processing_state = {"processed_frames": sorted(list(self.processed_frames))}
        return self.checkpoint_manager.save_crop_regions(
            video_name, crop_regions, processing_state
        )
