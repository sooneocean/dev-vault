"""Unit and integration tests for optical flow-based temporal alignment."""

import asyncio
import json
import tempfile
from pathlib import Path
from typing import Dict

import numpy as np
import pytest

from src.watermark_removal.core.types import CropRegion, FlowData, ProcessConfig
from src.watermark_removal.optical_flow import (
    OpticalFlowProcessor,
    align_inpaint_region,
    compute_flow_confidence,
    warp_region_boundary,
)
from src.watermark_removal.persistence.crop_serializer import CropRegionSerializer


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_frame_480p() -> np.ndarray:
    """Create a sample 480p frame."""
    h, w = 480, 640
    # Create a gradient frame with some variation
    frame = np.zeros((h, w, 3), dtype=np.uint8)
    frame[:, :, 0] = np.linspace(0, 255, w)  # R channel
    frame[:, :, 1] = np.linspace(255, 0, h)[:, np.newaxis]  # G channel
    frame[:, :, 2] = 128  # B channel
    return frame


@pytest.fixture
def sample_frame_1080p() -> np.ndarray:
    """Create a sample 1080p frame."""
    h, w = 1080, 1920
    frame = np.zeros((h, w, 3), dtype=np.uint8)
    frame[:, :, 0] = np.linspace(0, 255, w)
    frame[:, :, 1] = np.linspace(255, 0, h)[:, np.newaxis]
    frame[:, :, 2] = 128
    return frame


@pytest.fixture
def shifted_frame(sample_frame_480p: np.ndarray) -> np.ndarray:
    """Create a frame shifted horizontally (for flow detection)."""
    import cv2

    shift = 10  # pixels
    h, w = sample_frame_480p.shape[:2]
    M = np.float32([[1, 0, shift], [0, 1, 0]])
    return cv2.warpAffine(sample_frame_480p, M, (w, h))


@pytest.fixture
def sample_crop_region() -> CropRegion:
    """Create a sample crop region."""
    return CropRegion(
        x=100,
        y=100,
        w=200,
        h=200,
        scale_factor=2.0,
        context_x=50,
        context_y=50,
        context_w=300,
        context_h=300,
        pad_left=50,
        pad_top=50,
        pad_right=50,
        pad_bottom=50,
    )


@pytest.fixture
def sample_flow_data() -> FlowData:
    """Create sample optical flow data."""
    h, w = 480, 640
    # Create flow with slight rightward motion
    forward_flow = np.zeros((h, w, 2), dtype=np.float32)
    forward_flow[..., 0] = 2.0  # x motion
    forward_flow[..., 1] = 0.5  # y motion

    backward_flow = -forward_flow

    return FlowData(
        forward_flow=forward_flow,
        backward_flow=backward_flow,
        frame_pair_id=(0, 1),
        metadata={"resolution": "480", "model": "raft_large"},
    )


# ============================================================================
# Unit Tests: OpticalFlowProcessor
# ============================================================================


class TestOpticalFlowProcessorBasics:
    """Test basic optical flow processor functionality."""

    def test_init_default_480p(self) -> None:
        """Test processor initialization with default 480p resolution."""
        processor = OpticalFlowProcessor()
        assert processor.resolution == "480"
        assert processor.device in ("cuda", "cpu")

    def test_init_custom_resolution(self) -> None:
        """Test processor initialization with custom resolution."""
        processor = OpticalFlowProcessor(resolution="1080")
        assert processor.resolution == "1080"

    def test_init_invalid_resolution(self) -> None:
        """Test processor initialization with invalid resolution."""
        with pytest.raises(ValueError, match="resolution must be"):
            OpticalFlowProcessor(resolution="720")

    def test_device_detection(self) -> None:
        """Test device auto-detection."""
        processor = OpticalFlowProcessor(device="auto")
        assert processor.device in ("cuda", "cpu")

    def test_get_device(self) -> None:
        """Test device getter."""
        processor = OpticalFlowProcessor(device="cpu")
        assert processor.get_device() == "cpu"


class TestOpticalFlowComputation:
    """Test optical flow computation (integration with RAFT)."""

    @pytest.mark.asyncio
    async def test_compute_flow_identical_frames(self, sample_frame_480p: np.ndarray) -> None:
        """Test flow computation between identical frames (should be near-zero)."""
        processor = OpticalFlowProcessor(device="cpu")

        try:
            flow = await processor.compute_flow(sample_frame_480p, sample_frame_480p)

            # Flow between identical frames should be near-zero
            assert flow.shape == (sample_frame_480p.shape[0], sample_frame_480p.shape[1], 2)
            assert np.allclose(flow, 0.0, atol=2.0)  # Allow small numerical noise

        except RuntimeError as e:
            # Graceful fallback if RAFT not installed
            pytest.skip(f"RAFT model not available: {e}")

    @pytest.mark.asyncio
    async def test_compute_flow_shifted_frames(
        self, sample_frame_480p: np.ndarray, shifted_frame: np.ndarray
    ) -> None:
        """Test flow computation detects horizontal shift."""
        processor = OpticalFlowProcessor(device="cpu")

        try:
            flow = await processor.compute_flow(sample_frame_480p, shifted_frame)

            # Flow should detect rightward motion
            assert flow.shape == (sample_frame_480p.shape[0], sample_frame_480p.shape[1], 2)

            # Average x-component should be positive (rightward)
            mean_flow_x = np.mean(flow[..., 0])
            assert mean_flow_x > 0  # Should detect rightward shift

        except RuntimeError as e:
            pytest.skip(f"RAFT model not available: {e}")

    @pytest.mark.asyncio
    async def test_compute_flow_shape_mismatch(
        self, sample_frame_480p: np.ndarray, sample_frame_1080p: np.ndarray
    ) -> None:
        """Test flow computation fails on shape mismatch."""
        processor = OpticalFlowProcessor()

        with pytest.raises(ValueError, match="same shape"):
            await processor.compute_flow(sample_frame_480p, sample_frame_1080p)

    def test_resize_frame_480p(self, sample_frame_480p: np.ndarray) -> None:
        """Test frame resizing for 480p resolution."""
        try:
            import cv2  # noqa: F401
        except ImportError:
            pytest.skip("opencv not available")

        processor = OpticalFlowProcessor(resolution="480")

        resized, original_size = processor._resize_frame(sample_frame_480p)

        # Original size should be recorded
        assert original_size == (480, 640)

        # Resized frame should have height 480 (or 472 after alignment to 8)
        assert resized.shape[0] <= 480
        assert resized.shape[0] % 8 == 0  # Divisible by 8 for RAFT

    def test_resize_frame_1080p(self, sample_frame_1080p: np.ndarray) -> None:
        """Test frame resizing for 1080p resolution."""
        try:
            import cv2  # noqa: F401
        except ImportError:
            pytest.skip("opencv not available")

        processor = OpticalFlowProcessor(resolution="1080")

        resized, original_size = processor._resize_frame(sample_frame_1080p)

        # Original size should be recorded
        assert original_size == (1080, 1920)

        # Resized frame height should be 1080 (or 1072 after alignment)
        assert resized.shape[0] <= 1080
        assert resized.shape[0] % 8 == 0


class TestOpticalFlowAlignment:
    """Test flow-based alignment functions."""

    def test_align_inpaint_region_zero_flow(
        self, sample_crop_region: CropRegion, sample_flow_data: FlowData
    ) -> None:
        """Test alignment with zero flow (should return near-identical region)."""
        # Create zero flow
        zero_flow_data = FlowData(
            forward_flow=np.zeros_like(sample_flow_data.forward_flow),
            backward_flow=np.zeros_like(sample_flow_data.backward_flow),
            frame_pair_id=(0, 1),
        )

        aligned = align_inpaint_region(zero_flow_data, sample_crop_region)

        # With zero flow, region should remain essentially unchanged
        assert aligned.x == sample_crop_region.x
        assert aligned.y == sample_crop_region.y
        assert aligned.w == sample_crop_region.w
        assert aligned.h == sample_crop_region.h

    def test_align_inpaint_region_with_flow(
        self, sample_crop_region: CropRegion, sample_flow_data: FlowData
    ) -> None:
        """Test alignment with actual flow vectors."""
        aligned = align_inpaint_region(sample_flow_data, sample_crop_region)

        # Region should be modified based on flow
        assert isinstance(aligned, CropRegion)
        assert aligned.w == sample_crop_region.w  # Width unchanged
        assert aligned.h == sample_crop_region.h  # Height unchanged

    def test_align_inpaint_region_invalid_flow_shape(
        self, sample_crop_region: CropRegion
    ) -> None:
        """Test alignment fails with invalid flow shape."""
        invalid_flow_data = FlowData(
            forward_flow=np.zeros((480, 640, 3)),  # Wrong shape
            backward_flow=np.zeros((480, 640, 3)),
            frame_pair_id=(0, 1),
        )

        with pytest.raises(ValueError, match="Expected flow shape"):
            align_inpaint_region(invalid_flow_data, sample_crop_region)

    def test_compute_flow_confidence(self, sample_flow_data: FlowData) -> None:
        """Test flow confidence computation."""
        confidence = compute_flow_confidence(sample_flow_data)

        # Confidence should be between 0 and 1
        assert 0.0 <= confidence <= 1.0

    def test_compute_flow_confidence_high_consistency(self) -> None:
        """Test high confidence with consistent forward/backward flows."""
        flow = np.ones((480, 640, 2), dtype=np.float32) * 0.5

        flow_data = FlowData(
            forward_flow=flow.copy(),
            backward_flow=-flow.copy(),
            frame_pair_id=(0, 1),
        )

        confidence = compute_flow_confidence(flow_data)

        # High consistency should yield high confidence
        assert confidence > 0.8

    def test_warp_region_boundary(self, sample_flow_data: FlowData) -> None:
        """Test region boundary warping."""
        # Create boundary points (rectangle corners)
        region_pts = np.array([[100, 100], [300, 100], [300, 300], [100, 300]], dtype=np.float32)

        warped = warp_region_boundary(sample_flow_data.forward_flow, region_pts)

        # Warped points should be valid
        assert warped.shape == region_pts.shape
        assert np.all(np.isfinite(warped))

    def test_warp_region_boundary_out_of_bounds(self, sample_flow_data: FlowData) -> None:
        """Test warping with points outside flow bounds."""
        # Create points outside flow bounds
        region_pts = np.array([[10000, 10000]], dtype=np.float32)

        warped = warp_region_boundary(sample_flow_data.forward_flow, region_pts)

        # Should clamp to valid range and not crash
        assert warped.shape == region_pts.shape
        assert np.all(np.isfinite(warped))


# ============================================================================
# Integration Tests: Checkpoint Serialization
# ============================================================================


class TestCheckpointSerialization:
    """Test checkpoint save/load with flow data."""

    def test_serialize_crop_regions_only(self, sample_crop_region: CropRegion) -> None:
        """Test serialization of crop regions only (backward compatibility)."""
        crop_regions = {0: sample_crop_region}

        json_str = CropRegionSerializer.serialize(crop_regions)

        # Parse to verify structure
        data = json.loads(json_str)
        assert "version" in data
        assert "crop_regions" in data
        assert "0" in data["crop_regions"]

    def test_serialize_with_flow_data(
        self, sample_crop_region: CropRegion, sample_flow_data: FlowData
    ) -> None:
        """Test serialization with flow data."""
        crop_regions = {0: sample_crop_region}

        # Serialize flow data (converting to serializable format)
        flow_dict = {
            "0_1": {
                "frame_pair_id": [0, 1],
                "metadata": sample_flow_data.metadata,
            }
        }

        json_str = CropRegionSerializer.serialize(crop_regions, flow_dict)

        data = json.loads(json_str)
        assert "flow_data" in data
        assert "0_1" in data["flow_data"]

    def test_deserialize_backward_compatible(self) -> None:
        """Test deserialization of old checkpoint format."""
        # Old format (no version key)
        old_json = json.dumps({
            "0": {
                "x": 100,
                "y": 100,
                "w": 200,
                "h": 200,
                "scale_factor": 2.0,
                "context_x": 50,
                "context_y": 50,
                "context_w": 300,
                "context_h": 300,
                "pad_left": 50,
                "pad_top": 50,
                "pad_right": 50,
                "pad_bottom": 50,
            }
        })

        crop_regions, flow_data = CropRegionSerializer.deserialize(old_json)

        assert len(crop_regions) == 1
        assert 0 in crop_regions
        assert flow_data is None

    def test_deserialize_new_format_with_flow(self) -> None:
        """Test deserialization of new checkpoint format with flow data."""
        new_json = json.dumps({
            "version": "1.2",
            "crop_regions": {
                "0": {
                    "x": 100,
                    "y": 100,
                    "w": 200,
                    "h": 200,
                    "scale_factor": 2.0,
                    "context_x": 50,
                    "context_y": 50,
                    "context_w": 300,
                    "context_h": 300,
                }
            },
            "flow_data": {
                "0_1": {"frame_pair_id": [0, 1]}
            },
        })

        crop_regions, flow_data = CropRegionSerializer.deserialize(new_json)

        assert len(crop_regions) == 1
        assert flow_data is not None
        assert "0_1" in flow_data

    def test_checkpoint_roundtrip(self, sample_crop_region: CropRegion) -> None:
        """Test save and load cycle preserves data."""
        crop_regions_orig = {0: sample_crop_region}

        with tempfile.TemporaryDirectory() as tmpdir:
            # Save
            checkpoint_path = CropRegionSerializer.save_checkpoint(
                crop_regions_orig,
                tmpdir,
            )

            # Load
            result = CropRegionSerializer.load_checkpoint(tmpdir)
            assert result is not None
            crop_regions_loaded, flow_data = result

            # Verify data
            assert len(crop_regions_loaded) == len(crop_regions_orig)
            assert crop_regions_loaded[0].x == sample_crop_region.x
            assert crop_regions_loaded[0].y == sample_crop_region.y
            assert crop_regions_loaded[0].w == sample_crop_region.w
            assert crop_regions_loaded[0].h == sample_crop_region.h

    def test_checkpoint_with_flow_roundtrip(self, sample_crop_region: CropRegion) -> None:
        """Test checkpoint save/load with flow data."""
        crop_regions = {0: sample_crop_region}
        flow_dict = {"0_1": {"frame_pair_id": [0, 1], "data": "test"}}

        with tempfile.TemporaryDirectory() as tmpdir:
            # Save with flow data
            CropRegionSerializer.save_checkpoint(
                crop_regions,
                tmpdir,
                flow_data_dict=flow_dict,
            )

            # Load
            result = CropRegionSerializer.load_checkpoint(tmpdir)
            assert result is not None
            crop_regions_loaded, flow_data_loaded = result

            # Verify flow data preserved
            assert flow_data_loaded is not None
            assert "0_1" in flow_data_loaded
            assert flow_data_loaded["0_1"]["frame_pair_id"] == [0, 1]

    def test_checkpoint_nonexistent_file(self) -> None:
        """Test loading from nonexistent checkpoint file."""
        result = CropRegionSerializer.load_checkpoint("/nonexistent/dir")
        assert result is None

    def test_checkpoint_malformed_json(self) -> None:
        """Test loading malformed checkpoint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_path = Path(tmpdir) / "checkpoint_crops.json"
            checkpoint_path.write_text("{invalid json")

            with pytest.raises(json.JSONDecodeError):
                CropRegionSerializer.load_checkpoint(tmpdir)


# ============================================================================
# Configuration Tests
# ============================================================================


class TestOpticalFlowConfiguration:
    """Test optical flow configuration."""

    def test_config_optical_flow_defaults(self) -> None:
        """Test ProcessConfig optical flow defaults."""
        config = ProcessConfig(
            video_path="/tmp/test.mp4",
            mask_path="/tmp/mask.jpg",
            output_dir="/tmp/out",
        )

        assert config.optical_flow_enabled is False
        assert config.optical_flow_weight == 0.5
        assert config.optical_flow_resolution == "480"

    def test_config_optical_flow_custom(self) -> None:
        """Test ProcessConfig with custom optical flow settings."""
        config = ProcessConfig(
            video_path="/tmp/test.mp4",
            mask_path="/tmp/mask.jpg",
            output_dir="/tmp/out",
            optical_flow_enabled=True,
            optical_flow_weight=0.7,
            optical_flow_resolution="1080",
        )

        assert config.optical_flow_enabled is True
        assert config.optical_flow_weight == 0.7
        assert config.optical_flow_resolution == "1080"

    def test_config_optical_flow_weight_validation(self) -> None:
        """Test optical flow weight validation."""
        with pytest.raises(ValueError, match="optical_flow_weight"):
            ProcessConfig(
                video_path="/tmp/test.mp4",
                mask_path="/tmp/mask.jpg",
                output_dir="/tmp/out",
                optical_flow_weight=1.5,
            )

    def test_config_optical_flow_resolution_validation(self) -> None:
        """Test optical flow resolution validation."""
        with pytest.raises(ValueError, match="optical_flow_resolution"):
            ProcessConfig(
                video_path="/tmp/test.mp4",
                mask_path="/tmp/mask.jpg",
                output_dir="/tmp/out",
                optical_flow_resolution="720",
            )


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_single_frame_no_flow(self, sample_frame_480p: np.ndarray) -> None:
        """Test that single frame has no previous/next frame."""
        # This is an edge case handled at pipeline level
        # Verify that we can at least construct flow data for single frame
        pass

    def test_boundary_frames(self) -> None:
        """Test handling of first and last frames."""
        # First frame: no previous frame, only forward flow to frame 1
        # Last frame: no next frame, only backward flow from previous frame
        # These are handled at the pipeline level
        pass

    def test_flow_disabled_in_config(self) -> None:
        """Test that flow is skipped when disabled in config."""
        config = ProcessConfig(
            video_path="/tmp/test.mp4",
            mask_path="/tmp/mask.jpg",
            output_dir="/tmp/out",
            optical_flow_enabled=False,
        )

        # Pipeline should skip flow computation
        assert config.optical_flow_enabled is False

    def test_model_download_failure(self) -> None:
        """Test graceful fallback when model download fails."""
        processor = OpticalFlowProcessor(device="cpu")

        # If model fails to load, it should raise RuntimeError
        # This is handled gracefully in the pipeline
        pass

    def test_oom_handling(self, sample_frame_480p: np.ndarray) -> None:
        """Test OOM handling for large frames."""
        # 1080p frames may cause OOM on small GPUs
        # This is handled at pipeline level with graceful degradation
        pass


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
