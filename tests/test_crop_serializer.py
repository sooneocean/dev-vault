"""Tests for CropRegion serialization and checkpoint management."""

import json
import tempfile
from pathlib import Path

import pytest

from src.watermark_removal.core.types import CropRegion
from src.watermark_removal.persistence.crop_serializer import CropRegionSerializer


class TestSerializeCropRegion:
    """Test CropRegion serialization to JSON."""

    def test_serialize_empty(self):
        """Test serializing empty crop dictionary."""
        result = CropRegionSerializer.serialize({})
        assert result == "{}"

    def test_serialize_single_crop(self):
        """Test serializing single CropRegion."""
        crop = CropRegion(
            x=100,
            y=200,
            w=300,
            h=400,
            scale_factor=2.0,
            context_x=50,
            context_y=100,
            context_w=400,
            context_h=600,
            pad_left=10,
            pad_top=20,
            pad_right=30,
            pad_bottom=40,
        )

        crops = {0: crop}
        result = CropRegionSerializer.serialize(crops)

        # Parse back to verify structure
        parsed = json.loads(result)
        assert "0" in parsed
        assert parsed["0"]["x"] == 100
        assert parsed["0"]["w"] == 300
        assert parsed["0"]["scale_factor"] == 2.0

    def test_serialize_multiple_crops(self):
        """Test serializing multiple crops."""
        crops = {}
        for i in range(5):
            crops[i] = CropRegion(
                x=i * 100,
                y=i * 200,
                w=100 + i * 10,
                h=200 + i * 20,
                scale_factor=1.5 + i * 0.1,
                context_x=i * 50,
                context_y=i * 100,
                context_w=200 + i * 20,
                context_h=300 + i * 30,
                pad_left=i * 5,
                pad_top=i * 10,
                pad_right=i * 15,
                pad_bottom=i * 20,
            )

        result = CropRegionSerializer.serialize(crops)
        parsed = json.loads(result)

        assert len(parsed) == 5
        for i in range(5):
            assert str(i) in parsed
            assert parsed[str(i)]["x"] == i * 100
            assert parsed[str(i)]["scale_factor"] == pytest.approx(1.5 + i * 0.1)


class TestDeserializeCropRegion:
    """Test CropRegion deserialization from JSON."""

    def test_deserialize_empty(self):
        """Test deserializing empty JSON."""
        result = CropRegionSerializer.deserialize("{}")
        assert result == {}

    def test_deserialize_empty_string(self):
        """Test deserializing empty string."""
        result = CropRegionSerializer.deserialize("")
        assert result == {}

    def test_deserialize_single_crop(self):
        """Test deserializing single crop."""
        json_str = """{
            "0": {
                "x": 100,
                "y": 200,
                "w": 300,
                "h": 400,
                "scale_factor": 2.0,
                "context_x": 50,
                "context_y": 100,
                "context_w": 400,
                "context_h": 600,
                "pad_left": 10,
                "pad_top": 20,
                "pad_right": 30,
                "pad_bottom": 40
            }
        }"""

        result = CropRegionSerializer.deserialize(json_str)

        assert len(result) == 1
        assert 0 in result
        crop = result[0]
        assert crop.x == 100
        assert crop.y == 200
        assert crop.w == 300
        assert crop.scale_factor == 2.0

    def test_deserialize_multiple_crops(self):
        """Test deserializing multiple crops."""
        crops_orig = {}
        for i in range(3):
            crops_orig[i] = CropRegion(
                x=i * 100,
                y=i * 200,
                w=100,
                h=200,
                scale_factor=1.5,
                context_x=50,
                context_y=100,
                context_w=200,
                context_h=300,
            )

        json_str = CropRegionSerializer.serialize(crops_orig)
        result = CropRegionSerializer.deserialize(json_str)

        assert len(result) == 3
        for i in range(3):
            assert i in result
            assert result[i].x == i * 100

    def test_deserialize_invalid_json(self):
        """Test deserializing invalid JSON."""
        with pytest.raises(json.JSONDecodeError):
            CropRegionSerializer.deserialize("not valid json {")

    def test_deserialize_malformed_crop_missing_field(self):
        """Test deserializing crop with missing required field."""
        json_str = '{"0": {"x": 100}}'  # Missing required fields

        with pytest.raises(ValueError, match="Malformed crop data"):
            CropRegionSerializer.deserialize(json_str)

    def test_deserialize_malformed_crop_wrong_type(self):
        """Test deserializing crop with wrong field type."""
        json_str = """{
            "0": {
                "x": "not_an_int",
                "y": 200,
                "w": 300,
                "h": 400,
                "scale_factor": 2.0,
                "context_x": 50,
                "context_y": 100,
                "context_w": 400,
                "context_h": 600
            }
        }"""

        with pytest.raises(ValueError, match="Malformed crop data"):
            CropRegionSerializer.deserialize(json_str)


class TestRoundTripSerialization:
    """Test round-trip serialization (serialize -> deserialize -> compare)."""

    def test_round_trip_single_crop(self):
        """Test round-trip preserves single crop exactly."""
        original = CropRegion(
            x=123,
            y=456,
            w=789,
            h=321,
            scale_factor=1.75,
            context_x=100,
            context_y=400,
            context_w=850,
            context_h=400,
            pad_left=42,
            pad_top=84,
            pad_right=126,
            pad_bottom=168,
        )

        crops_orig = {0: original}

        # Serialize and deserialize
        json_str = CropRegionSerializer.serialize(crops_orig)
        crops_restored = CropRegionSerializer.deserialize(json_str)

        # Compare all fields
        restored = crops_restored[0]
        assert restored.x == original.x
        assert restored.y == original.y
        assert restored.w == original.w
        assert restored.h == original.h
        assert restored.scale_factor == original.scale_factor
        assert restored.context_x == original.context_x
        assert restored.context_y == original.context_y
        assert restored.context_w == original.context_w
        assert restored.context_h == original.context_h
        assert restored.pad_left == original.pad_left
        assert restored.pad_top == original.pad_top
        assert restored.pad_right == original.pad_right
        assert restored.pad_bottom == original.pad_bottom

    def test_round_trip_large_batch(self):
        """Test round-trip with many crops."""
        crops_orig = {}
        for i in range(100):
            crops_orig[i] = CropRegion(
                x=i * 10,
                y=i * 20,
                w=500 + i,
                h=600 + i,
                scale_factor=1.5 + (i % 10) * 0.1,
                context_x=i * 5,
                context_y=i * 15,
                context_w=600 + i,
                context_h=700 + i,
                pad_left=i % 50,
                pad_top=i % 60,
                pad_right=i % 70,
                pad_bottom=i % 80,
            )

        # Serialize and deserialize
        json_str = CropRegionSerializer.serialize(crops_orig)
        crops_restored = CropRegionSerializer.deserialize(json_str)

        # Verify all crops preserved
        assert len(crops_restored) == 100
        for i in range(100):
            assert i in crops_restored
            assert crops_restored[i].x == crops_orig[i].x
            assert crops_restored[i].scale_factor == crops_orig[i].scale_factor


class TestCheckpointFileOperations:
    """Test saving and loading checkpoint files."""

    def test_save_checkpoint(self):
        """Test saving crops to checkpoint file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            crop = CropRegion(
                x=100, y=200, w=300, h=400, scale_factor=2.0,
                context_x=50, context_y=100, context_w=400, context_h=600,
            )
            crops = {0: crop}

            checkpoint_path = CropRegionSerializer.save_checkpoint(crops, tmpdir)

            # Verify file created
            assert checkpoint_path.exists()
            assert checkpoint_path.name == "checkpoint_crops.json"

            # Verify contents
            with open(checkpoint_path) as f:
                data = json.load(f)
            assert "0" in data
            assert data["0"]["x"] == 100

    def test_save_checkpoint_custom_filename(self):
        """Test saving checkpoint with custom filename."""
        with tempfile.TemporaryDirectory() as tmpdir:
            crop = CropRegion(
                x=50, y=100, w=200, h=300, scale_factor=1.5,
                context_x=25, context_y=50, context_w=250, context_h=350,
            )
            crops = {0: crop}

            checkpoint_path = CropRegionSerializer.save_checkpoint(
                crops, tmpdir, filename="custom_checkpoint.json"
            )

            assert checkpoint_path.name == "custom_checkpoint.json"
            assert checkpoint_path.exists()

    def test_load_checkpoint_exists(self):
        """Test loading checkpoint when file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            crop = CropRegion(
                x=100, y=200, w=300, h=400, scale_factor=2.0,
                context_x=50, context_y=100, context_w=400, context_h=600,
            )
            crops_orig = {0: crop}

            # Save checkpoint
            CropRegionSerializer.save_checkpoint(crops_orig, tmpdir)

            # Load checkpoint
            crops_loaded = CropRegionSerializer.load_checkpoint(tmpdir)

            assert crops_loaded is not None
            assert len(crops_loaded) == 1
            assert crops_loaded[0].x == 100

    def test_load_checkpoint_not_exists(self):
        """Test loading checkpoint when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = CropRegionSerializer.load_checkpoint(tmpdir)
            assert result is None

    def test_load_checkpoint_malformed_json(self):
        """Test loading checkpoint with malformed JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_path = Path(tmpdir) / "checkpoint_crops.json"
            checkpoint_path.write_text("not valid json {")

            with pytest.raises(Exception):  # json.JSONDecodeError or ValueError
                CropRegionSerializer.load_checkpoint(tmpdir)

    def test_checkpoint_round_trip(self):
        """Test save and load checkpoint round-trip."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create crops
            crops_orig = {}
            for i in range(10):
                crops_orig[i] = CropRegion(
                    x=i * 100,
                    y=i * 200,
                    w=500,
                    h=600,
                    scale_factor=1.5,
                    context_x=i * 50,
                    context_y=i * 100,
                    context_w=600,
                    context_h=700,
                )

            # Save
            CropRegionSerializer.save_checkpoint(crops_orig, tmpdir)

            # Load
            crops_loaded = CropRegionSerializer.load_checkpoint(tmpdir)

            # Verify
            assert crops_loaded is not None
            assert len(crops_loaded) == 10
            for i in range(10):
                assert crops_loaded[i].x == crops_orig[i].x
                assert crops_loaded[i].context_w == crops_orig[i].context_w


class TestCheckpointIntegration:
    """Integration tests for checkpoint workflow."""

    def test_checkpoint_resumption_workflow(self):
        """Test typical checkpoint save/load workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Simulate preprocessing phase: generate crops
            crops_phase1 = {}
            for frame_idx in range(5):
                crops_phase1[frame_idx] = CropRegion(
                    x=frame_idx * 100,
                    y=frame_idx * 50,
                    w=200,
                    h=300,
                    scale_factor=2.0,
                    context_x=frame_idx * 80,
                    context_y=frame_idx * 40,
                    context_w=250,
                    context_h=350,
                )

            # Save checkpoint after preprocessing
            checkpoint_path = CropRegionSerializer.save_checkpoint(crops_phase1, tmpdir)
            assert checkpoint_path.exists()

            # Later: load checkpoint and skip preprocessing
            crops_phase2 = CropRegionSerializer.load_checkpoint(tmpdir)
            assert crops_phase2 is not None
            assert len(crops_phase2) == 5

            # Verify no preprocessing needed: crops are identical
            for frame_idx in range(5):
                assert crops_phase2[frame_idx].x == crops_phase1[frame_idx].x
                assert crops_phase2[frame_idx].w == crops_phase1[frame_idx].w

    def test_checkpoint_with_large_float_precision(self):
        """Test checkpoint preserves float precision."""
        with tempfile.TemporaryDirectory() as tmpdir:
            crop = CropRegion(
                x=100,
                y=200,
                w=300,
                h=400,
                scale_factor=1.3333333,  # High precision float
                context_x=50,
                context_y=100,
                context_w=400,
                context_h=600,
            )

            crops = {0: crop}

            # Save and load
            CropRegionSerializer.save_checkpoint(crops, tmpdir)
            crops_loaded = CropRegionSerializer.load_checkpoint(tmpdir)

            # Float precision should be preserved (JSON round-trip)
            assert crops_loaded[0].scale_factor == pytest.approx(1.3333333)
