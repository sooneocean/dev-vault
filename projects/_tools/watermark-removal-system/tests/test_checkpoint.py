"""
Unit tests for watermark_removal.core.checkpoint module.

Tests checkpoint saving/loading, resumable processing, and state management.
"""

import pytest
import tempfile
import json
from pathlib import Path

from src.watermark_removal.core.types import CropRegion
from src.watermark_removal.core.checkpoint import CheckpointManager, ResumableFrameProcessor


class TestCheckpointManager:
    """Test CheckpointManager class."""

    @pytest.fixture
    def temp_checkpoint_dir(self):
        """Create temporary checkpoint directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def checkpoint_manager(self, temp_checkpoint_dir):
        """Create checkpoint manager with temp directory."""
        return CheckpointManager(temp_checkpoint_dir)

    @pytest.fixture
    def sample_crop_regions(self):
        """Create sample crop regions."""
        return [
            CropRegion(
                frame_id=0,
                original_bbox=(10, 20, 100, 150),
                context_bbox=(0, 0, 120, 180),
                scale_factor=0.85,
                pad_left=5,
                pad_top=10,
            ),
            CropRegion(
                frame_id=1,
                original_bbox=(15, 25, 100, 150),
                context_bbox=(5, 5, 120, 180),
                scale_factor=0.85,
            ),
        ]

    def test_init_creates_directory(self, temp_checkpoint_dir):
        """Initialization creates checkpoint directory."""
        subdir = temp_checkpoint_dir / "checkpoints"
        manager = CheckpointManager(subdir)
        assert subdir.exists()

    def test_get_checkpoint_path(self, checkpoint_manager):
        """Get checkpoint path for video."""
        path = checkpoint_manager.get_checkpoint_path("test_video")
        assert path.name == "test_video_checkpoint.json"
        assert path.parent == checkpoint_manager.checkpoint_dir

    def test_save_crop_regions(self, checkpoint_manager, sample_crop_regions):
        """Save crop regions to checkpoint."""
        path = checkpoint_manager.save_crop_regions("video1", sample_crop_regions)

        assert path.exists()
        assert path.suffix == ".json"

        # Verify JSON structure
        with open(path) as f:
            data = json.load(f)

        assert data["version"] == "1.0"
        assert data["video_name"] == "video1"
        assert len(data["crop_regions"]) == 2
        assert data["crop_regions"][0]["frame_id"] == 0

    def test_save_with_processing_state(self, checkpoint_manager, sample_crop_regions):
        """Save checkpoint with processing state."""
        state = {"processed_frames": [0, 1], "status": "in_progress"}
        path = checkpoint_manager.save_crop_regions("video2", sample_crop_regions, state)

        with open(path) as f:
            data = json.load(f)

        assert data["processing_state"]["processed_frames"] == [0, 1]
        assert data["processing_state"]["status"] == "in_progress"

    def test_load_crop_regions(self, checkpoint_manager, sample_crop_regions):
        """Load crop regions from checkpoint."""
        # Save first
        checkpoint_manager.save_crop_regions("video3", sample_crop_regions)

        # Load
        loaded_crops, state = checkpoint_manager.load_crop_regions("video3")

        assert len(loaded_crops) == 2
        assert loaded_crops[0].frame_id == 0
        assert loaded_crops[0].original_bbox == (10, 20, 100, 150)
        assert loaded_crops[0].pad_left == 5

    def test_load_with_state(self, checkpoint_manager, sample_crop_regions):
        """Load checkpoint with processing state."""
        state = {"processed_frames": [0]}
        checkpoint_manager.save_crop_regions("video4", sample_crop_regions, state)

        loaded_crops, loaded_state = checkpoint_manager.load_crop_regions("video4")

        assert loaded_state["processed_frames"] == [0]

    def test_load_nonexistent_checkpoint(self, checkpoint_manager):
        """Loading nonexistent checkpoint returns empty."""
        crops, state = checkpoint_manager.load_crop_regions("nonexistent")

        assert crops == []
        assert state == {}

    def test_checkpoint_exists(self, checkpoint_manager, sample_crop_regions):
        """Check checkpoint existence."""
        assert not checkpoint_manager.checkpoint_exists("video5")

        checkpoint_manager.save_crop_regions("video5", sample_crop_regions)

        assert checkpoint_manager.checkpoint_exists("video5")

    def test_delete_checkpoint(self, checkpoint_manager, sample_crop_regions):
        """Delete checkpoint file."""
        checkpoint_manager.save_crop_regions("video6", sample_crop_regions)
        assert checkpoint_manager.checkpoint_exists("video6")

        success = checkpoint_manager.delete_checkpoint("video6")
        assert success
        assert not checkpoint_manager.checkpoint_exists("video6")

    def test_delete_nonexistent(self, checkpoint_manager):
        """Deleting nonexistent checkpoint returns False."""
        success = checkpoint_manager.delete_checkpoint("nonexistent")
        assert not success

    def test_list_checkpoints(self, checkpoint_manager, sample_crop_regions):
        """List all available checkpoints."""
        checkpoint_manager.save_crop_regions("video7", sample_crop_regions)
        checkpoint_manager.save_crop_regions("video8", sample_crop_regions)

        checkpoints = checkpoint_manager.list_checkpoints()

        assert "video7" in checkpoints
        assert "video8" in checkpoints
        assert len(checkpoints) >= 2

    def test_checkpoint_data_integrity(self, checkpoint_manager, sample_crop_regions):
        """Checkpoint preserves exact crop region data."""
        original = sample_crop_regions[0]
        checkpoint_manager.save_crop_regions("integrity_test", [original])

        loaded, _ = checkpoint_manager.load_crop_regions("integrity_test")

        assert loaded[0].frame_id == original.frame_id
        assert loaded[0].original_bbox == original.original_bbox
        assert loaded[0].context_bbox == original.context_bbox
        assert loaded[0].scale_factor == original.scale_factor
        assert loaded[0].pad_left == original.pad_left
        assert loaded[0].pad_top == original.pad_top
        assert loaded[0].pad_right == original.pad_right
        assert loaded[0].pad_bottom == original.pad_bottom


class TestResumableFrameProcessor:
    """Test ResumableFrameProcessor class."""

    @pytest.fixture
    def temp_checkpoint_dir(self):
        """Create temporary checkpoint directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def processor(self, temp_checkpoint_dir):
        """Create processor with temp checkpoint manager."""
        manager = CheckpointManager(temp_checkpoint_dir)
        return ResumableFrameProcessor(manager)

    @pytest.fixture
    def sample_crops(self):
        """Sample crop regions."""
        return [
            CropRegion(0, (10, 20, 100, 150), (0, 0, 120, 180), 0.85),
            CropRegion(1, (15, 25, 100, 150), (5, 5, 120, 180), 0.85),
            CropRegion(2, (20, 30, 100, 150), (10, 10, 120, 180), 0.85),
        ]

    def test_init(self, processor):
        """Initialize processor."""
        assert len(processor.processed_frames) == 0

    def test_mark_frame_processed(self, processor):
        """Mark frames as processed."""
        processor.mark_frame_processed(0)
        processor.mark_frame_processed(2)

        assert 0 in processor.processed_frames
        assert 1 not in processor.processed_frames
        assert 2 in processor.processed_frames

    def test_is_frame_processed(self, processor):
        """Check if frame was processed."""
        processor.mark_frame_processed(0)

        assert processor.is_frame_processed(0)
        assert not processor.is_frame_processed(1)

    def test_load_checkpoint(self, processor, sample_crops):
        """Load checkpoint with processed frames."""
        # First save checkpoint
        state = {"processed_frames": [0, 2]}
        processor.checkpoint_manager.save_crop_regions("video", sample_crops, state)

        # Load
        crops, processed = processor.load_checkpoint("video")

        assert len(crops) == 3
        assert processed == {0, 2}
        assert processor.is_frame_processed(0)
        assert processor.is_frame_processed(2)
        assert not processor.is_frame_processed(1)

    def test_save_checkpoint(self, processor, sample_crops):
        """Save checkpoint with processed frames."""
        processor.mark_frame_processed(0)
        processor.mark_frame_processed(1)

        path = processor.save_checkpoint("resume_test", sample_crops)

        # Reload and verify
        loaded_crops, state = processor.checkpoint_manager.load_crop_regions("resume_test")

        assert sorted(state["processed_frames"]) == [0, 1]

    def test_resumable_workflow(self, processor, sample_crops):
        """Simulate resumable processing workflow."""
        # Initial save
        processor.mark_frame_processed(0)
        processor.save_checkpoint("workflow_test", sample_crops)

        # Simulate restart: load checkpoint
        processor2 = ResumableFrameProcessor(processor.checkpoint_manager)
        loaded_crops, processed = processor2.load_checkpoint("workflow_test")

        # Should resume from frame 1
        assert not processor2.is_frame_processed(0) or 0 in processed
        processor2.mark_frame_processed(1)

        # Save progress
        processor2.save_checkpoint("workflow_test", loaded_crops)

        # Load again, should have both frames processed
        processor3 = ResumableFrameProcessor(processor.checkpoint_manager)
        _, processed3 = processor3.load_checkpoint("workflow_test")

        assert 0 in processed3
        assert 1 in processed3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
