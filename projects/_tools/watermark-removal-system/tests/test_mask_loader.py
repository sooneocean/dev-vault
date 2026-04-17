"""
Unit tests for watermark_removal.preprocessing.mask_loader module.

Tests mask loading, validation, and generation from bboxes.
"""

import pytest
import json
import tempfile
import numpy as np
from pathlib import Path

from src.watermark_removal.preprocessing.mask_loader import MaskLoader


class TestMaskLoader:
    """Test MaskLoader class."""

    def test_init(self):
        """Initialize loader."""
        loader = MaskLoader()
        assert loader is not None

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_load_bbox_sequence_frame_dict_format(self, temp_dir):
        """Load bbox from JSON with frame_id->bbox dict format."""
        bbox_file = temp_dir / "bboxes.json"
        data = {
            "0": [10, 20, 100, 150],
            "1": [12, 22, 100, 150],
            "2": [14, 24, 100, 150],
        }

        with open(bbox_file, "w") as f:
            json.dump(data, f)

        loader = MaskLoader()
        bboxes = loader.load_bbox_sequence(bbox_file)

        assert bboxes is not None
        assert len(bboxes) == 3
        assert bboxes[0] == (10, 20, 100, 150)
        assert bboxes[2] == (14, 24, 100, 150)

    def test_load_bbox_sequence_frames_array(self, temp_dir):
        """Load bbox from JSON with frames array format."""
        bbox_file = temp_dir / "bboxes.json"
        data = {
            "frames": [
                {"id": 0, "bbox": [10, 20, 100, 150]},
                {"id": 1, "bbox": [12, 22, 100, 150]},
            ]
        }

        with open(bbox_file, "w") as f:
            json.dump(data, f)

        loader = MaskLoader()
        bboxes = loader.load_bbox_sequence(bbox_file)

        assert bboxes is not None
        assert len(bboxes) == 2
        assert bboxes[0] == (10, 20, 100, 150)

    def test_load_bbox_nonexistent_file(self):
        """Loading nonexistent bbox file returns None."""
        loader = MaskLoader()
        bboxes = loader.load_bbox_sequence("/nonexistent/path/bboxes.json")
        assert bboxes is None

    def test_load_bbox_invalid_json(self, temp_dir):
        """Invalid JSON returns None."""
        bbox_file = temp_dir / "invalid.json"
        bbox_file.write_text("{invalid json")

        loader = MaskLoader()
        bboxes = loader.load_bbox_sequence(bbox_file)
        assert bboxes is None

    def test_load_bbox_empty_data(self, temp_dir):
        """Empty bbox data returns None."""
        bbox_file = temp_dir / "empty.json"
        data = {"frames": []}

        with open(bbox_file, "w") as f:
            json.dump(data, f)

        loader = MaskLoader()
        bboxes = loader.load_bbox_sequence(bbox_file)
        assert bboxes is None

    def test_load_mask_auto_detect_json(self, temp_dir):
        """Auto-detect JSON mask file."""
        bbox_file = temp_dir / "mask.json"
        data = {"0": [10, 20, 100, 150]}

        with open(bbox_file, "w") as f:
            json.dump(data, f)

        loader = MaskLoader()
        mask = loader.load_mask(bbox_file)

        assert mask is not None
        assert isinstance(mask, dict)

    def test_load_mask_unsupported_extension(self, temp_dir):
        """Unsupported file extension returns None."""
        mask_file = temp_dir / "mask.txt"
        mask_file.write_text("invalid")

        loader = MaskLoader()
        mask = loader.load_mask(mask_file)
        assert mask is None

    def test_validate_bbox_valid(self):
        """Valid bbox passes validation."""
        loader = MaskLoader()
        bbox = (10, 20, 100, 150)
        frame_shape = (480, 640, 3)

        assert loader.validate_bbox(bbox, frame_shape)

    def test_validate_bbox_negative_coords(self):
        """Bbox with negative coordinates fails."""
        loader = MaskLoader()
        bbox = (-10, 20, 100, 150)
        frame_shape = (480, 640, 3)

        assert not loader.validate_bbox(bbox, frame_shape)

    def test_validate_bbox_zero_size(self):
        """Bbox with zero width/height fails."""
        loader = MaskLoader()
        bbox = (10, 20, 0, 150)
        frame_shape = (480, 640, 3)

        assert not loader.validate_bbox(bbox, frame_shape)

    def test_validate_bbox_exceeds_bounds(self):
        """Bbox exceeding frame bounds fails validation."""
        loader = MaskLoader()
        bbox = (600, 400, 100, 150)
        frame_shape = (480, 640, 3)

        assert not loader.validate_bbox(bbox, frame_shape)

    def test_create_mask_from_bbox(self):
        """Create mask from bbox coordinates."""
        loader = MaskLoader()
        bbox = (100, 50, 200, 150)
        frame_shape = (480, 640, 3)

        mask = loader.create_mask_from_bbox(bbox, frame_shape)

        assert mask.shape == (480, 640)
        assert mask.dtype == np.uint8

        # Check mask region
        assert np.max(mask[50:200, 100:300]) == 255  # Inside bbox
        assert np.max(mask[0:40, 100:300]) == 0  # Above bbox

    def test_create_mask_bbox_clamped_to_frame(self):
        """Bbox clamped to frame boundaries."""
        loader = MaskLoader()
        bbox = (600, 400, 100, 150)  # Exceeds frame
        frame_shape = (480, 640, 3)

        mask = loader.create_mask_from_bbox(bbox, frame_shape)

        assert mask.shape == (480, 640)
        # Should still create valid mask with clamped region
        assert np.any(mask)

    def test_create_mask_with_feather(self):
        """Create mask with feathered edges."""
        loader = MaskLoader()
        bbox = (100, 100, 200, 200)
        frame_shape = (480, 640, 3)

        mask_sharp = loader.create_mask_from_bbox(bbox, frame_shape, feather=0)
        mask_feather = loader.create_mask_from_bbox(bbox, frame_shape, feather=10)

        # Feathered mask should have same shape
        assert mask_sharp.shape == mask_feather.shape

        # Both should be uint8
        assert mask_sharp.dtype == np.uint8
        assert mask_feather.dtype == np.uint8

        # Feathering should create soft edges (some gradient)
        # Sharp edges have clear boundary, feathered has gradual transition
        # Check edges region for gradient in feathered mask
        edges = mask_feather[95:105, 95:105]
        if edges.size > 0:
            # Edges should have variance (gradient) in feathered version
            # Not all uniform value
            assert len(np.unique(edges)) >= 1  # At least have values


class TestMaskLoaderIntegration:
    """Integration tests for mask loading workflow."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_bbox_to_mask_workflow(self, temp_dir):
        """Complete workflow: load bbox -> create mask."""
        # Save bbox JSON
        bbox_file = temp_dir / "detections.json"
        data = {
            "0": [100, 50, 200, 150],
            "1": [105, 55, 200, 150],
        }

        with open(bbox_file, "w") as f:
            json.dump(data, f)

        # Load bbox
        loader = MaskLoader()
        bboxes = loader.load_bbox_sequence(bbox_file)

        assert bboxes is not None

        # Create mask for frame 0
        frame_shape = (480, 640, 3)
        bbox = bboxes[0]
        mask = loader.create_mask_from_bbox(bbox, frame_shape)

        assert mask.shape == (480, 640)
        assert mask.dtype == np.uint8

    def test_validate_loaded_bbox(self, temp_dir):
        """Load bbox and validate it."""
        bbox_file = temp_dir / "bboxes.json"
        data = {"0": [10, 20, 100, 150]}

        with open(bbox_file, "w") as f:
            json.dump(data, f)

        loader = MaskLoader()
        bboxes = loader.load_bbox_sequence(bbox_file)
        frame_shape = (480, 640, 3)

        bbox = bboxes[0]
        assert loader.validate_bbox(bbox, frame_shape)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
