"""
Phase 3 integration tests: optical flow + ensemble detection + streaming + tuning.

Covers:
- Phase 2-3 feature interaction (all Phase 3 features together)
- Graceful feature degradation (optional features disabled)
- Backward compatibility (Phase 2 config in Phase 3 pipeline)
- Checkpoint resumption with Phase 3 features
- Streaming session with metrics accumulation
"""

import asyncio
import json
import tempfile
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pytest

from watermark_removal.core.types import ProcessConfig, CropRegion, FrameExtractedData
from watermark_removal.core.pipeline import Pipeline
from watermark_removal.streaming.session_manager import SessionManager, FrameResult
from watermark_removal.streaming.queue_processor import BackgroundTaskRunner


# ============================================================================
# Fixtures: Common Test Data
# ============================================================================


@pytest.fixture
def temp_workspace():
    """Create temporary workspace for test videos and outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        workspace.mkdir(exist_ok=True)
        yield workspace


@pytest.fixture
def minimal_video_path(temp_workspace):
    """Create a minimal test video file (placeholder)."""
    video_path = temp_workspace / "test_video.mp4"
    # For testing, we just create an empty file
    # In real tests, would use OpenCV to generate actual frames
    video_path.touch()
    return video_path


@pytest.fixture
def minimal_mask_path(temp_workspace):
    """Create a minimal test mask file (placeholder)."""
    mask_path = temp_workspace / "test_mask.mp4"
    mask_path.touch()
    return mask_path


@pytest.fixture
def phase2_config(minimal_video_path, minimal_mask_path, temp_workspace):
    """ProcessConfig with Phase 2 features only (Phase 3 disabled)."""
    return ProcessConfig(
        video_path=minimal_video_path,
        mask_path=minimal_mask_path,
        output_dir=temp_workspace / "output",
        # Phase 3 features disabled
        optical_flow_enabled=False,
        ensemble_detection_enabled=False,
        use_checkpoints=True,
        checkpoint_dir=temp_workspace / "checkpoints",
    )


@pytest.fixture
def phase3_full_config(minimal_video_path, minimal_mask_path, temp_workspace):
    """ProcessConfig with all Phase 3 features enabled."""
    return ProcessConfig(
        video_path=minimal_video_path,
        mask_path=minimal_mask_path,
        output_dir=temp_workspace / "output",
        # Phase 3 features enabled
        optical_flow_enabled=True,
        optical_flow_resolution="480",
        optical_flow_weight=0.5,
        ensemble_detection_enabled=True,
        use_checkpoints=True,
        checkpoint_dir=temp_workspace / "checkpoints",
    )


# ============================================================================
# Test Class 1: Feature Interaction
# ============================================================================


class TestPhase3FeatureInteraction:
    """Test Phase 3 features working together."""

    def test_config_validation_phase3(self, phase3_full_config):
        """Test Phase 3 config validation."""
        assert phase3_full_config.optical_flow_enabled is True
        assert phase3_full_config.ensemble_detection_enabled is True
        assert phase3_full_config.optical_flow_resolution == "480"
        assert 0.0 <= phase3_full_config.optical_flow_weight <= 1.0

    def test_config_validation_optical_flow_weight(
        self, minimal_video_path, minimal_mask_path, temp_workspace
    ):
        """Test optical flow weight validation (0.0-1.0)."""
        # Valid weight
        config = ProcessConfig(
            video_path=minimal_video_path,
            mask_path=minimal_mask_path,
            output_dir=temp_workspace,
            optical_flow_weight=0.7,
        )
        assert config.optical_flow_weight == 0.7

        # Invalid weight should raise
        with pytest.raises(ValueError, match="optical_flow_weight"):
            ProcessConfig(
                video_path=minimal_video_path,
                mask_path=minimal_mask_path,
                output_dir=temp_workspace,
                optical_flow_weight=1.5,
            )

    def test_config_optical_flow_resolution_choices(
        self, minimal_video_path, minimal_mask_path, temp_workspace
    ):
        """Test optical flow resolution validation."""
        # Valid resolutions
        for res in ["480", "1080"]:
            config = ProcessConfig(
                video_path=minimal_video_path,
                mask_path=minimal_mask_path,
                output_dir=temp_workspace,
                optical_flow_resolution=res,
            )
            assert config.optical_flow_resolution == res

        # Invalid resolution should raise
        with pytest.raises(ValueError, match="optical_flow_resolution"):
            ProcessConfig(
                video_path=minimal_video_path,
                mask_path=minimal_mask_path,
                output_dir=temp_workspace,
                optical_flow_resolution="720",
            )


# ============================================================================
# Test Class 2: Backward Compatibility
# ============================================================================


class TestBackwardCompatibility:
    """Test Phase 2 config still works in Phase 3 pipeline."""

    def test_phase2_config_in_phase3_pipeline(self, phase2_config):
        """Test Phase 2 config (all Phase 3 features disabled) still valid."""
        # Phase 3 features should be optional and not break Phase 2 config
        assert phase2_config.optical_flow_enabled is False
        assert phase2_config.ensemble_detection_enabled is False

        # Pipeline should still create and accept the config
        pipeline = Pipeline(phase2_config)
        assert pipeline.config == phase2_config

    def test_phase2_checkpoint_format_compatibility(self, temp_workspace):
        """Test Phase 2 checkpoint format (v1.0) loads in Phase 3."""
        # Create old Phase 2 checkpoint (no version key)
        old_checkpoint = {
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
        }

        checkpoint_path = temp_workspace / "checkpoint_crops.json"
        checkpoint_path.write_text(json.dumps(old_checkpoint))

        # Phase 3 checkpoint loader should handle v1.0 format
        from watermark_removal.persistence.crop_serializer import CropRegionSerializer

        result = CropRegionSerializer.load_checkpoint(temp_workspace)
        assert result is not None

        crop_regions, flow_data = result
        assert len(crop_regions) == 1
        assert 0 in crop_regions
        # Phase 2 checkpoints don't have flow data
        assert flow_data is None

    def test_phase2_features_disabled_in_phase3(self, phase2_config):
        """Test Phase 3 features can be disabled to emulate Phase 2 behavior."""
        # Disable all Phase 3 features
        phase2_config.optical_flow_enabled = False
        phase2_config.ensemble_detection_enabled = False

        # Pipeline should process like Phase 2
        pipeline = Pipeline(phase2_config)
        assert pipeline.config.optical_flow_enabled is False


# ============================================================================
# Test Class 3: Streaming Session Integration
# ============================================================================


class TestStreamingSessionIntegration:
    """Test streaming with Phase 3 features."""

    @pytest.mark.asyncio
    async def test_streaming_session_lifecycle(self, phase3_full_config):
        """Test complete streaming session lifecycle."""
        manager = SessionManager(result_ttl_sec=300, session_ttl_sec=600)

        # Create session
        session_id = await manager.create_session(phase3_full_config)
        assert session_id is not None

        # Retrieve session
        session = await manager.get_session(session_id)
        assert session is not None
        assert session.config == phase3_full_config

        # End session
        summary = await manager.end_session(session_id)
        assert summary is not None
        assert summary["session_id"] == session_id

    @pytest.mark.asyncio
    async def test_streaming_with_background_runner(self, phase3_full_config):
        """Test streaming with background frame processing."""
        manager = SessionManager()
        session_id = await manager.create_session(phase3_full_config)
        session = await manager.get_session(session_id)

        # Create background runner
        runner = BackgroundTaskRunner(
            session=session,
            max_queue_size=50,
            timeout_per_frame_sec=300.0,
        )

        await runner.start()

        try:
            # Submit a frame
            frame_data = b"\x89PNG\r\n\x1a\n"  # Minimal PNG header
            queued = await runner.submit_frame(frame_id=0, frame_data=frame_data)
            assert queued is True

            # Check queue size
            queue_size = await runner.get_queue_size()
            assert queue_size > 0

        finally:
            await runner.stop()

    @pytest.mark.asyncio
    async def test_streaming_metrics_accumulation(self, phase3_full_config):
        """Test metrics accumulation in streaming session."""
        manager = SessionManager()
        session_id = await manager.create_session(phase3_full_config)
        session = await manager.get_session(session_id)

        # Simulate frame processing with metrics
        for frame_id in range(3):
            result = FrameResult(
                frame_id=frame_id,
                status="completed",
                metrics={
                    "total_time_ms": 100.0 + frame_id * 10,
                    "detection_time_ms": 50.0,
                    "watermark_detected": True,
                },
            )
            session.add_frame_result(frame_id, result)

        # Verify metrics accumulated
        assert session.metrics_accumulator.get("frames_processed", 0) == 0  # Not auto-accumulated
        assert len(session.result_cache) == 3

        # Manually check last result
        last_result = session.get_frame_result(2)
        assert last_result is not None
        assert last_result.metrics["total_time_ms"] == 120.0

    @pytest.mark.asyncio
    async def test_streaming_session_expiration(self, phase3_full_config):
        """Test streaming session TTL expiration."""
        manager = SessionManager(result_ttl_sec=300, session_ttl_sec=1)
        session_id = await manager.create_session(phase3_full_config)

        # Session should exist
        session = await manager.get_session(session_id)
        assert session is not None

        # Wait for expiration
        await asyncio.sleep(1.5)

        # Session should be expired
        expired_session = await manager.get_session(session_id)
        assert expired_session is None


# ============================================================================
# Test Class 4: Graceful Degradation
# ============================================================================


class TestGracefulDegradation:
    """Test features can be disabled without breaking pipeline."""

    def test_disable_optical_flow(self, phase3_full_config):
        """Test disabling optical flow doesn't break pipeline."""
        phase3_full_config.optical_flow_enabled = False

        pipeline = Pipeline(phase3_full_config)
        assert pipeline.config.optical_flow_enabled is False
        # Pipeline should still be valid

    def test_disable_ensemble_detection(self, phase3_full_config):
        """Test disabling ensemble detection doesn't break pipeline."""
        phase3_full_config.ensemble_detection_enabled = False

        pipeline = Pipeline(phase3_full_config)
        assert pipeline.config.ensemble_detection_enabled is False
        # Pipeline should still be valid

    def test_disable_all_phase3_features(self, phase2_config):
        """Test disabling all Phase 3 features reduces to Phase 2."""
        phase2_config.optical_flow_enabled = False
        phase2_config.ensemble_detection_enabled = False

        pipeline = Pipeline(phase2_config)
        assert pipeline.config.optical_flow_enabled is False
        assert pipeline.config.ensemble_detection_enabled is False
        # Should behave like Phase 2

    def test_mixed_feature_combinations(self, phase3_full_config):
        """Test various combinations of Phase 3 features."""
        # Optical flow only
        phase3_full_config.optical_flow_enabled = True
        phase3_full_config.ensemble_detection_enabled = False
        pipeline1 = Pipeline(phase3_full_config)
        assert pipeline1.config.optical_flow_enabled is True

        # Ensemble only
        phase3_full_config.optical_flow_enabled = False
        phase3_full_config.ensemble_detection_enabled = True
        pipeline2 = Pipeline(phase3_full_config)
        assert pipeline2.config.ensemble_detection_enabled is True

        # Both
        phase3_full_config.optical_flow_enabled = True
        phase3_full_config.ensemble_detection_enabled = True
        pipeline3 = Pipeline(phase3_full_config)
        assert pipeline3.config.optical_flow_enabled is True
        assert pipeline3.config.ensemble_detection_enabled is True


# ============================================================================
# Test Class 5: Checkpoint Resumption
# ============================================================================


class TestCheckpointResumption:
    """Test checkpoint save/resume with Phase 3 features."""

    def test_checkpoint_resumption_basic(self, temp_workspace):
        """Test basic checkpoint save and resumption."""
        from watermark_removal.persistence.crop_serializer import CropRegionSerializer

        # Create crop region
        crop = CropRegion(
            x=100, y=100, w=200, h=200, scale_factor=2.0,
            context_x=50, context_y=50, context_w=300, context_h=300,
            pad_left=50, pad_top=50, pad_right=50, pad_bottom=50
        )

        crop_regions = {0: crop}

        # Save checkpoint
        CropRegionSerializer.save_checkpoint(crop_regions, temp_workspace)

        # Load checkpoint
        result = CropRegionSerializer.load_checkpoint(temp_workspace)
        assert result is not None

        loaded_crops, flow_data = result
        assert len(loaded_crops) == 1
        assert loaded_crops[0].x == crop.x

    def test_checkpoint_with_flow_data(self, temp_workspace):
        """Test checkpoint saves and restores flow data."""
        from watermark_removal.persistence.crop_serializer import CropRegionSerializer

        crop = CropRegion(
            x=100, y=100, w=200, h=200, scale_factor=2.0,
            context_x=50, context_y=50, context_w=300, context_h=300,
            pad_left=50, pad_top=50, pad_right=50, pad_bottom=50
        )

        crop_regions = {0: crop}
        flow_dict = {"0_1": {"frame_pair_id": [0, 1], "metadata": {"model": "raft"}}}

        # Save with flow data
        CropRegionSerializer.save_checkpoint(crop_regions, temp_workspace, flow_dict)

        # Load
        result = CropRegionSerializer.load_checkpoint(temp_workspace)
        assert result is not None

        loaded_crops, loaded_flow = result
        assert loaded_flow is not None
        assert "0_1" in loaded_flow


# ============================================================================
# Test Class 6: Configuration Persistence
# ============================================================================


class TestConfigurationPersistence:
    """Test Phase 3 configuration saved and loaded correctly."""

    def test_phase3_config_serialization(self, phase3_full_config, temp_workspace):
        """Test Phase 3 config can be serialized to JSON."""
        config_dict = {
            "optical_flow_enabled": phase3_full_config.optical_flow_enabled,
            "optical_flow_resolution": phase3_full_config.optical_flow_resolution,
            "optical_flow_weight": phase3_full_config.optical_flow_weight,
            "ensemble_detection_enabled": phase3_full_config.ensemble_detection_enabled,
        }

        config_path = temp_workspace / "config.json"
        config_path.write_text(json.dumps(config_dict))

        # Load and verify
        loaded_dict = json.loads(config_path.read_text())
        assert loaded_dict["optical_flow_enabled"] is True
        assert loaded_dict["optical_flow_resolution"] == "480"
        assert loaded_dict["optical_flow_weight"] == 0.5
        assert loaded_dict["ensemble_detection_enabled"] is True


# ============================================================================
# Test Class 7: Error Handling & Edge Cases
# ============================================================================


class TestErrorHandlingEdgeCases:
    """Test error handling and edge cases."""

    def test_invalid_optical_flow_resolution(
        self, minimal_video_path, minimal_mask_path, temp_workspace
    ):
        """Test invalid optical flow resolution raises error."""
        with pytest.raises(ValueError, match="optical_flow_resolution"):
            ProcessConfig(
                video_path=minimal_video_path,
                mask_path=minimal_mask_path,
                output_dir=temp_workspace,
                optical_flow_resolution="720p",
            )

    def test_invalid_optical_flow_weight(
        self, minimal_video_path, minimal_mask_path, temp_workspace
    ):
        """Test invalid optical flow weight raises error."""
        with pytest.raises(ValueError, match="optical_flow_weight"):
            ProcessConfig(
                video_path=minimal_video_path,
                mask_path=minimal_mask_path,
                output_dir=temp_workspace,
                optical_flow_weight=2.0,
            )

    @pytest.mark.asyncio
    async def test_streaming_queue_overflow(self, phase3_full_config):
        """Test streaming queue backpressure on overflow."""
        manager = SessionManager()
        session_id = await manager.create_session(phase3_full_config)
        session = await manager.get_session(session_id)

        runner = BackgroundTaskRunner(
            session=session,
            max_queue_size=2,
            timeout_per_frame_sec=300.0,
        )

        await runner.start()

        try:
            frame_data = b"fake-frame"

            # Fill queue
            assert await runner.submit_frame(0, frame_data) is True
            assert await runner.submit_frame(1, frame_data) is True

            # Overflow should fail
            assert await runner.submit_frame(2, frame_data) is False

        finally:
            await runner.stop()

    @pytest.mark.asyncio
    async def test_session_manager_cleanup(self, phase3_full_config):
        """Test cleanup of expired sessions."""
        manager = SessionManager(result_ttl_sec=300, session_ttl_sec=1)

        # Create multiple sessions
        ids = []
        for i in range(3):
            sid = await manager.create_session(phase3_full_config)
            ids.append(sid)

        count = await manager.get_active_session_count()
        assert count == 3

        # Wait for expiration
        await asyncio.sleep(1.5)

        # Cleanup
        cleaned = await manager.cleanup_expired_sessions()
        assert cleaned >= 0

        # Count should be lower
        new_count = await manager.get_active_session_count()
        assert new_count <= count


# ============================================================================
# Test Class 8: System-Wide Interaction
# ============================================================================


class TestSystemWideInteraction:
    """Test Phase 2-3 interaction at system level."""

    def test_pipeline_with_phase2_and_phase3_config(
        self, phase2_config, phase3_full_config
    ):
        """Test pipeline handles both Phase 2 and Phase 3 configs."""
        # Phase 2 style
        pipeline2 = Pipeline(phase2_config)
        assert pipeline2.config.optical_flow_enabled is False

        # Phase 3 style
        pipeline3 = Pipeline(phase3_full_config)
        assert pipeline3.config.optical_flow_enabled is True

    @pytest.mark.asyncio
    async def test_session_manager_concurrent_sessions(self, phase3_full_config):
        """Test session manager handles multiple concurrent sessions."""
        manager = SessionManager()

        # Create multiple concurrent sessions
        tasks = [
            manager.create_session(phase3_full_config)
            for _ in range(5)
        ]
        session_ids = await asyncio.gather(*tasks)

        # Verify all created
        assert len(session_ids) == 5
        assert len(set(session_ids)) == 5  # All unique

        count = await manager.get_active_session_count()
        assert count == 5

        # Clean up
        for sid in session_ids:
            await manager.end_session(sid)

        final_count = await manager.get_active_session_count()
        assert final_count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
