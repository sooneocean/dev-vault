"""Phase 2 checkpoint serialization and resumption validation tests."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.watermark_removal.core.checkpoint import Checkpoint, CHECKPOINT_VERSION
from src.watermark_removal.core.types import CropRegion
from src.watermark_removal.persistence.crop_serializer import CropRegionSerializer


class TestCheckpointPreprocessingStage:
    """Test checkpoint save/load for preprocessing stage."""

    def test_save_preprocessing_state_happy_path(self, temp_config_dir):
        """Test saving checkpoint after preprocessing."""
        checkpoint_path = temp_config_dir / "checkpoint.json"
        checkpoint = Checkpoint(checkpoint_path)

        # Create test crop regions
        crop_regions = {
            0: CropRegion(
                x=100, y=200, w=300, h=400,
                scale_factor=2.0,
                context_x=50, context_y=100,
                context_w=400, context_h=600,
                pad_left=10, pad_top=20, pad_right=30, pad_bottom=40,
            ),
            1: CropRegion(
                x=150, y=250, w=350, h=450,
                scale_factor=1.8,
                context_x=80, context_y=120,
                context_w=450, context_h=650,
                pad_left=12, pad_top=22, pad_right=32, pad_bottom=42,
            ),
        }

        # Save preprocessing state
        checkpoint.save_preprocessing_state(crop_regions, frame_count=2)

        # Verify file exists and is readable
        assert checkpoint_path.exists()
        with open(checkpoint_path, "r") as f:
            data = json.load(f)

        assert data["version"] == CHECKPOINT_VERSION
        assert data["stage"] == "preprocessing"
        assert data["frame_count"] == 2
        # CropRegionSerializer nests the crop_regions under a "crop_regions" key
        assert "crop_regions" in data["crop_regions"]
        assert len(data["crop_regions"]["crop_regions"]) == 2
        assert data["crop_regions"]["crop_regions"]["0"]["x"] == 100
        assert data["crop_regions"]["crop_regions"]["1"]["w"] == 350

    def test_load_preprocessing_checkpoint_happy_path(self, temp_config_dir):
        """Test loading checkpoint from preprocessing stage."""
        checkpoint_path = temp_config_dir / "checkpoint.json"
        checkpoint = Checkpoint(checkpoint_path)

        # Create and save test state
        original_regions = {
            0: CropRegion(
                x=100, y=200, w=300, h=400,
                scale_factor=2.0,
                context_x=50, context_y=100,
                context_w=400, context_h=600,
            ),
        }
        checkpoint.save_preprocessing_state(original_regions, frame_count=1)

        # Load checkpoint
        loaded = checkpoint.load()

        assert loaded["version"] == CHECKPOINT_VERSION
        assert loaded["stage"] == "preprocessing"
        assert loaded["frame_count"] == 1
        assert len(loaded["crop_regions"]) == 1
        assert loaded["crop_regions"][0].x == 100
        assert loaded["crop_regions"][0].w == 300
        assert loaded["inpaint_results"] == {}

    def test_checkpoint_file_format_human_readable(self, temp_config_dir):
        """Test that checkpoint file format is human-readable JSON."""
        checkpoint_path = temp_config_dir / "checkpoint.json"
        checkpoint = Checkpoint(checkpoint_path)

        crop_regions = {
            0: CropRegion(
                x=10, y=20, w=30, h=40,
                scale_factor=1.5,
                context_x=5, context_y=10,
                context_w=40, context_h=60,
            ),
        }

        checkpoint.save_preprocessing_state(crop_regions, frame_count=1)

        # Read as raw text to verify formatting
        with open(checkpoint_path, "r") as f:
            content = f.read()

        # Check indentation and readability
        assert "version" in content
        assert "stage" in content
        assert "preprocessing" in content
        assert "  " in content  # Has indentation

    def test_checkpoint_records_all_crop_parameters(self, temp_config_dir):
        """Test that checkpoint saves all CropRegion parameters."""
        checkpoint_path = temp_config_dir / "checkpoint.json"
        checkpoint = Checkpoint(checkpoint_path)

        crop = CropRegion(
            x=100, y=200, w=300, h=400,
            scale_factor=2.5,
            context_x=50, context_y=100,
            context_w=400, context_h=600,
            pad_left=11, pad_top=22, pad_right=33, pad_bottom=44,
        )

        checkpoint.save_preprocessing_state({0: crop}, frame_count=1)
        loaded = checkpoint.load()

        loaded_crop = loaded["crop_regions"][0]
        assert loaded_crop.x == 100
        assert loaded_crop.y == 200
        assert loaded_crop.w == 300
        assert loaded_crop.h == 400
        assert loaded_crop.scale_factor == 2.5
        assert loaded_crop.context_x == 50
        assert loaded_crop.context_y == 100
        assert loaded_crop.context_w == 400
        assert loaded_crop.context_h == 600
        assert loaded_crop.pad_left == 11
        assert loaded_crop.pad_top == 22
        assert loaded_crop.pad_right == 33
        assert loaded_crop.pad_bottom == 44


class TestCheckpointInpaintStage:
    """Test checkpoint save/load for inpaint stage."""

    def test_save_inpaint_state_happy_path(self, temp_config_dir):
        """Test saving checkpoint after inpainting."""
        checkpoint_path = temp_config_dir / "checkpoint.json"
        checkpoint = Checkpoint(checkpoint_path)

        crop_regions = {
            0: CropRegion(
                x=100, y=200, w=300, h=400,
                scale_factor=2.0,
                context_x=50, context_y=100,
                context_w=400, context_h=600,
            ),
        }

        # Simulate inpaint results (numpy arrays)
        inpaint_results = {
            0: np.random.randint(0, 256, (400, 300, 3), dtype=np.uint8),
        }

        checkpoint.save_inpaint_state(crop_regions, inpaint_results, frame_count=1)

        assert checkpoint_path.exists()
        with open(checkpoint_path, "r") as f:
            data = json.load(f)

        assert data["stage"] == "inpaint"
        assert data["frame_count"] == 1
        assert "0" in data["inpaint_results"]

    def test_load_inpaint_checkpoint_happy_path(self, temp_config_dir):
        """Test loading checkpoint from inpaint stage."""
        checkpoint_path = temp_config_dir / "checkpoint.json"
        checkpoint = Checkpoint(checkpoint_path)

        crop_regions = {
            0: CropRegion(
                x=100, y=200, w=300, h=400,
                scale_factor=2.0,
                context_x=50, context_y=100,
                context_w=400, context_h=600,
            ),
        }

        original_result = np.ones((400, 300, 3), dtype=np.uint8) * 128
        inpaint_results = {0: original_result}

        checkpoint.save_inpaint_state(crop_regions, inpaint_results, frame_count=1)
        loaded = checkpoint.load()

        assert loaded["stage"] == "inpaint"
        assert len(loaded["crop_regions"]) == 1
        assert len(loaded["inpaint_results"]) == 1
        assert loaded["inpaint_results"][0] == original_result.tolist()

    def test_inpaint_checkpoint_stores_crop_and_results(self, temp_config_dir):
        """Test that inpaint checkpoint includes both crops and results."""
        checkpoint_path = temp_config_dir / "checkpoint.json"
        checkpoint = Checkpoint(checkpoint_path)

        crop_regions = {
            0: CropRegion(
                x=10, y=20, w=30, h=40,
                scale_factor=1.5,
                context_x=5, context_y=10,
                context_w=40, context_h=60,
            ),
            1: CropRegion(
                x=50, y=60, w=70, h=80,
                scale_factor=1.2,
                context_x=40, context_y=50,
                context_w=90, context_h=100,
            ),
        }

        inpaint_results = {
            0: np.ones((40, 30, 3), dtype=np.uint8) * 200,
            1: np.ones((80, 70, 3), dtype=np.uint8) * 100,
        }

        checkpoint.save_inpaint_state(crop_regions, inpaint_results, frame_count=2)
        loaded = checkpoint.load()

        assert len(loaded["crop_regions"]) == 2
        assert len(loaded["inpaint_results"]) == 2
        assert loaded["crop_regions"][0].x == 10
        assert loaded["crop_regions"][1].x == 50


class TestCheckpointEdgeCases:
    """Test edge cases and error conditions."""

    def test_resume_from_nonexistent_checkpoint(self, temp_config_dir):
        """Test resuming from non-existent checkpoint raises FileNotFoundError."""
        checkpoint_path = temp_config_dir / "nonexistent.json"
        checkpoint = Checkpoint(checkpoint_path)

        with pytest.raises(FileNotFoundError):
            checkpoint.load()

    def test_corrupted_checkpoint_truncated_json(self, temp_config_dir):
        """Test loading corrupted checkpoint (truncated JSON) raises ValueError."""
        checkpoint_path = temp_config_dir / "corrupted.json"

        # Write truncated JSON
        with open(checkpoint_path, "w") as f:
            f.write('{"version": "1.0", "stage": "preprocessing"')

        checkpoint = Checkpoint(checkpoint_path)

        with pytest.raises(ValueError, match="Corrupted checkpoint"):
            checkpoint.load()

    def test_corrupted_checkpoint_invalid_json_syntax(self, temp_config_dir):
        """Test loading checkpoint with invalid JSON syntax."""
        checkpoint_path = temp_config_dir / "bad.json"

        with open(checkpoint_path, "w") as f:
            f.write('{"version": "1.0", invalid syntax}')

        checkpoint = Checkpoint(checkpoint_path)

        with pytest.raises(ValueError, match="Corrupted checkpoint"):
            checkpoint.load()

    def test_checkpoint_version_mismatch_raises_error(self, temp_config_dir):
        """Test that version mismatch raises ValueError."""
        checkpoint_path = temp_config_dir / "oldversion.json"

        # Manually write checkpoint with old version
        state = {
            "version": "0.5",
            "stage": "preprocessing",
            "frame_count": 1,
            "crop_regions": {},
            "inpaint_results": {},
        }
        with open(checkpoint_path, "w") as f:
            json.dump(state, f)

        checkpoint = Checkpoint(checkpoint_path)

        with pytest.raises(ValueError, match="version mismatch"):
            checkpoint.load()

    def test_checkpoint_with_empty_crops(self, temp_config_dir):
        """Test checkpoint with no crop regions."""
        checkpoint_path = temp_config_dir / "empty.json"
        checkpoint = Checkpoint(checkpoint_path)

        checkpoint.save_preprocessing_state({}, frame_count=0)
        loaded = checkpoint.load()

        assert loaded["crop_regions"] == {}
        assert loaded["frame_count"] == 0

    def test_checkpoint_exists_check(self, temp_config_dir):
        """Test checkpoint.exists() method."""
        checkpoint_path = temp_config_dir / "test.json"
        checkpoint = Checkpoint(checkpoint_path)

        assert not checkpoint.exists()

        checkpoint.save_preprocessing_state({}, frame_count=0)
        assert checkpoint.exists()

    def test_checkpoint_delete(self, temp_config_dir):
        """Test checkpoint deletion."""
        checkpoint_path = temp_config_dir / "todelete.json"
        checkpoint = Checkpoint(checkpoint_path)

        checkpoint.save_preprocessing_state({}, frame_count=0)
        assert checkpoint_path.exists()

        checkpoint.delete()
        assert not checkpoint_path.exists()

    def test_checkpoint_delete_nonexistent_raises_error(self, temp_config_dir):
        """Test deleting non-existent checkpoint raises FileNotFoundError."""
        checkpoint_path = temp_config_dir / "nonexistent.json"
        checkpoint = Checkpoint(checkpoint_path)

        with pytest.raises(FileNotFoundError):
            checkpoint.delete()


class TestCheckpointStateConsistency:
    """Test consistency between save and load operations."""

    def test_save_and_load_roundtrip_preprocessing(self, temp_config_dir):
        """Test preprocessing checkpoint roundtrip consistency."""
        checkpoint_path = temp_config_dir / "roundtrip.json"
        checkpoint = Checkpoint(checkpoint_path)

        original_crops = {
            0: CropRegion(
                x=100, y=200, w=300, h=400,
                scale_factor=2.0,
                context_x=50, context_y=100,
                context_w=400, context_h=600,
                pad_left=10, pad_top=20, pad_right=30, pad_bottom=40,
            ),
            5: CropRegion(
                x=200, y=300, w=250, h=350,
                scale_factor=1.8,
                context_x=100, context_y=150,
                context_w=350, context_h=550,
                pad_left=15, pad_top=25, pad_right=35, pad_bottom=45,
            ),
        }

        checkpoint.save_preprocessing_state(original_crops, frame_count=6)
        loaded = checkpoint.load()

        # Verify exact match
        assert len(loaded["crop_regions"]) == len(original_crops)
        for frame_idx, original_crop in original_crops.items():
            loaded_crop = loaded["crop_regions"][frame_idx]
            assert loaded_crop.x == original_crop.x
            assert loaded_crop.y == original_crop.y
            assert loaded_crop.w == original_crop.w
            assert loaded_crop.h == original_crop.h
            assert loaded_crop.scale_factor == original_crop.scale_factor
            assert loaded_crop.context_x == original_crop.context_x
            assert loaded_crop.context_y == original_crop.context_y
            assert loaded_crop.context_w == original_crop.context_w
            assert loaded_crop.context_h == original_crop.context_h
            assert loaded_crop.pad_left == original_crop.pad_left
            assert loaded_crop.pad_top == original_crop.pad_top
            assert loaded_crop.pad_right == original_crop.pad_right
            assert loaded_crop.pad_bottom == original_crop.pad_bottom

    def test_save_and_load_roundtrip_inpaint(self, temp_config_dir):
        """Test inpaint checkpoint roundtrip consistency."""
        checkpoint_path = temp_config_dir / "roundtrip_inpaint.json"
        checkpoint = Checkpoint(checkpoint_path)

        crops = {
            0: CropRegion(
                x=10, y=20, w=30, h=40,
                scale_factor=1.5,
                context_x=5, context_y=10,
                context_w=40, context_h=60,
            ),
        }

        # Create deterministic test result
        result_array = np.array(
            [[[100, 150, 200], [110, 160, 210]],
             [[120, 170, 220], [130, 180, 230]]],
            dtype=np.uint8
        )
        results = {0: result_array}

        checkpoint.save_inpaint_state(crops, results, frame_count=1)
        loaded = checkpoint.load()

        # Verify results roundtrip correctly
        loaded_result = loaded["inpaint_results"][0]
        assert loaded_result == result_array.tolist()

    def test_multiple_checkpoints_independent(self, temp_config_dir):
        """Test that multiple checkpoints are independent."""
        checkpoint1_path = temp_config_dir / "checkpoint1.json"
        checkpoint2_path = temp_config_dir / "checkpoint2.json"

        checkpoint1 = Checkpoint(checkpoint1_path)
        checkpoint2 = Checkpoint(checkpoint2_path)

        crops1 = {0: CropRegion(x=10, y=20, w=30, h=40,
                               scale_factor=1.0, context_x=5, context_y=10,
                               context_w=40, context_h=60)}
        crops2 = {0: CropRegion(x=100, y=200, w=300, h=400,
                               scale_factor=2.0, context_x=50, context_y=100,
                               context_w=400, context_h=600)}

        checkpoint1.save_preprocessing_state(crops1, frame_count=1)
        checkpoint2.save_preprocessing_state(crops2, frame_count=1)

        loaded1 = checkpoint1.load()
        loaded2 = checkpoint2.load()

        assert loaded1["crop_regions"][0].x == 10
        assert loaded2["crop_regions"][0].x == 100


@pytest.mark.parametrize("frame_count", [0, 1, 10, 100])
def test_checkpoint_frame_count_parameter(temp_config_dir, frame_count):
    """Test checkpoint with various frame counts."""
    checkpoint_path = temp_config_dir / f"checkpoint_{frame_count}.json"
    checkpoint = Checkpoint(checkpoint_path)

    crops = {i: CropRegion(x=10*i, y=20*i, w=30, h=40,
                          scale_factor=1.0, context_x=5, context_y=10,
                          context_w=40, context_h=60)
            for i in range(min(frame_count, 5))}

    checkpoint.save_preprocessing_state(crops, frame_count=frame_count)
    loaded = checkpoint.load()

    assert loaded["frame_count"] == frame_count


@pytest.mark.parametrize("num_crops", [1, 5, 10, 50])
def test_checkpoint_with_many_crops(temp_config_dir, num_crops):
    """Test checkpoint with many crop regions."""
    checkpoint_path = temp_config_dir / f"checkpoint_{num_crops}.json"
    checkpoint = Checkpoint(checkpoint_path)

    crops = {
        i: CropRegion(
            x=10*i, y=20*i, w=30, h=40,
            scale_factor=1.0+i*0.1,
            context_x=5, context_y=10,
            context_w=40, context_h=60,
        )
        for i in range(num_crops)
    }

    checkpoint.save_preprocessing_state(crops, frame_count=num_crops)
    loaded = checkpoint.load()

    assert len(loaded["crop_regions"]) == num_crops
    for i in range(num_crops):
        assert loaded["crop_regions"][i].x == 10*i


class TestCheckpointFilePathHandling:
    """Test checkpoint file path and directory handling."""

    def test_checkpoint_creates_parent_directories(self, temp_config_dir):
        """Test that checkpoint creates parent directories if needed."""
        nested_path = temp_config_dir / "nested" / "deep" / "checkpoint.json"
        checkpoint = Checkpoint(nested_path)

        crops = {0: CropRegion(x=10, y=20, w=30, h=40,
                             scale_factor=1.0, context_x=5, context_y=10,
                             context_w=40, context_h=60)}

        checkpoint.save_preprocessing_state(crops, frame_count=1)

        assert nested_path.exists()
        assert nested_path.parent.exists()

    def test_checkpoint_path_as_string(self, temp_config_dir):
        """Test checkpoint with path as string."""
        checkpoint_path_str = str(temp_config_dir / "checkpoint.json")
        checkpoint = Checkpoint(checkpoint_path_str)

        crops = {0: CropRegion(x=10, y=20, w=30, h=40,
                             scale_factor=1.0, context_x=5, context_y=10,
                             context_w=40, context_h=60)}

        checkpoint.save_preprocessing_state(crops, frame_count=1)

        assert Path(checkpoint_path_str).exists()

    def test_checkpoint_path_as_pathlib_path(self, temp_config_dir):
        """Test checkpoint with Path object."""
        checkpoint_path = Path(temp_config_dir) / "checkpoint.json"
        checkpoint = Checkpoint(checkpoint_path)

        crops = {0: CropRegion(x=10, y=20, w=30, h=40,
                             scale_factor=1.0, context_x=5, context_y=10,
                             context_w=40, context_h=60)}

        checkpoint.save_preprocessing_state(crops, frame_count=1)

        assert checkpoint_path.exists()
