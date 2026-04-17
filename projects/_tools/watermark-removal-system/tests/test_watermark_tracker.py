"""
Unit tests for watermark_removal.preprocessing.watermark_tracker module.

Tests bbox detection, interpolation, smoothing, and trajectory tracking.
"""

import pytest
import numpy as np

from src.watermark_removal.preprocessing.watermark_tracker import (
    BboxDetection,
    BboxTrajectory,
    BboxTracker,
    YOLOTrackerWrapper,
)


class TestBboxDetection:
    """Test BboxDetection dataclass."""

    def test_init_valid(self):
        """Create detection with valid parameters."""
        det = BboxDetection(frame_id=0, bbox=(10, 20, 100, 150), confidence=0.95)
        assert det.frame_id == 0
        assert det.bbox == (10, 20, 100, 150)
        assert det.confidence == 0.95

    def test_init_confidence_boundaries(self):
        """Test confidence boundaries."""
        det_min = BboxDetection(0, (10, 20, 100, 150), 0.0)
        assert det_min.confidence == 0.0

        det_max = BboxDetection(0, (10, 20, 100, 150), 1.0)
        assert det_max.confidence == 1.0


class TestBboxTrajectory:
    """Test BboxTrajectory dataclass."""

    def test_init_empty(self):
        """Create empty trajectory."""
        traj = BboxTrajectory([], [])
        assert len(traj.frame_ids) == 0
        assert len(traj.bboxes) == 0

    def test_init_with_frames(self):
        """Create trajectory with frames."""
        frames = [0, 1, 2]
        bboxes = [(10, 20, 100, 150), (12, 22, 100, 150), (14, 24, 100, 150)]
        traj = BboxTrajectory(frames, bboxes)
        assert traj.frame_ids == frames
        assert traj.bboxes == bboxes


class TestBboxTracker:
    """Test BboxTracker class."""

    def test_init_valid_smoothing(self):
        """Initialize with valid smoothing factors."""
        for factor in [0.0, 0.3, 0.5, 1.0]:
            tracker = BboxTracker(motion_smoothing_factor=factor)
            assert tracker.motion_smoothing_factor == factor

    def test_init_invalid_smoothing(self):
        """Reject invalid smoothing factors."""
        with pytest.raises(ValueError):
            BboxTracker(motion_smoothing_factor=-0.1)

        with pytest.raises(ValueError):
            BboxTracker(motion_smoothing_factor=1.5)

    def test_add_detection_valid(self):
        """Register detections."""
        tracker = BboxTracker()
        tracker.add_detection(0, (10, 20, 100, 150), confidence=0.95)
        assert 0 in tracker.detections
        assert tracker.detections[0].bbox == (10, 20, 100, 150)

    def test_add_detection_invalid_confidence(self):
        """Reject invalid confidence."""
        tracker = BboxTracker()
        with pytest.raises(ValueError):
            tracker.add_detection(0, (10, 20, 100, 150), confidence=1.5)

    def test_interpolate_no_detections(self):
        """Interpolate with no detections returns None."""
        tracker = BboxTracker()
        assert tracker.interpolate(0) is None

    def test_interpolate_exact_match(self):
        """Interpolate at detected frame returns exact bbox."""
        tracker = BboxTracker()
        tracker.add_detection(5, (10, 20, 100, 150))
        result = tracker.interpolate(5)
        assert result == (10, 20, 100, 150)

    def test_interpolate_before_first_detection(self):
        """Extrapolate before first detection returns first bbox."""
        tracker = BboxTracker()
        tracker.add_detection(5, (10, 20, 100, 150))
        tracker.add_detection(10, (20, 30, 100, 150))

        # Before frame 5
        result = tracker.interpolate(0)
        assert result == (10, 20, 100, 150)

    def test_interpolate_after_last_detection(self):
        """Extrapolate after last detection returns last bbox."""
        tracker = BboxTracker()
        tracker.add_detection(5, (10, 20, 100, 150))
        tracker.add_detection(10, (20, 30, 100, 150))

        # After frame 10
        result = tracker.interpolate(15)
        assert result == (20, 30, 100, 150)

    def test_interpolate_linear_between_frames(self):
        """Linear interpolation between detected frames."""
        tracker = BboxTracker()
        tracker.add_detection(0, (0, 0, 100, 100))
        tracker.add_detection(10, (100, 100, 100, 100))

        # At frame 5 (midpoint): should be (50, 50, 100, 100)
        result = tracker.interpolate(5)
        assert result is not None
        assert abs(result[0] - 50.0) < 0.01
        assert abs(result[1] - 50.0) < 0.01
        assert abs(result[2] - 100.0) < 0.01
        assert abs(result[3] - 100.0) < 0.01

    def test_interpolate_quarter_point(self):
        """Interpolation at 1/4 point."""
        tracker = BboxTracker()
        tracker.add_detection(0, (0, 0, 100, 100))
        tracker.add_detection(4, (40, 40, 100, 100))

        # At frame 1 (1/4): should be (10, 10, 100, 100)
        result = tracker.interpolate(1)
        assert result is not None
        assert abs(result[0] - 10.0) < 0.01
        assert abs(result[1] - 10.0) < 0.01

    def test_smooth_trajectory_no_detections(self):
        """Smooth trajectory with no detections returns empty."""
        tracker = BboxTracker()
        traj = tracker.smooth_trajectory([0, 1, 2])
        # When no detections, return completely empty trajectory
        assert len(traj.frame_ids) == 0
        assert len(traj.bboxes) == 0

    def test_smooth_trajectory_single_detection(self):
        """Smooth trajectory with one detection fills all frames."""
        tracker = BboxTracker()
        tracker.add_detection(0, (10, 20, 100, 150))

        traj = tracker.smooth_trajectory([0, 1, 2])
        assert len(traj.frame_ids) == 3
        assert len(traj.bboxes) == 3
        # All should be the same since only one detection
        for bbox in traj.bboxes:
            assert bbox == (10, 20, 100, 150)

    def test_smooth_trajectory_with_smoothing(self):
        """Trajectory smoothing reduces motion between frames."""
        tracker = BboxTracker(motion_smoothing_factor=0.5)
        tracker.add_detection(0, (0, 0, 100, 100))
        tracker.add_detection(10, (100, 100, 100, 100))

        traj = tracker.smooth_trajectory([0, 1, 2, 10])
        smoothed_bboxes = traj.bboxes

        # First frame unchanged
        assert smoothed_bboxes[0] == (0, 0, 100, 100)

        # Subsequent frames should be smoothed (between interpolated and previous smoothed)
        # Without smoothing, frame 1 would be (10, 10, 100, 100)
        # With smoothing: (1-0.5) * 10 + 0.5 * 0 = 5
        assert abs(smoothed_bboxes[1][0] - 5.0) < 0.1

    def test_get_motion_vector_valid(self):
        """Calculate motion vector between frames."""
        tracker = BboxTracker()
        tracker.add_detection(0, (0, 0, 10, 10))      # center at (5, 5)
        tracker.add_detection(5, (10, 10, 10, 10))    # center at (15, 15)

        motion = tracker.get_motion_vector(0, 5)
        assert motion is not None
        assert abs(motion[0] - 10.0) < 0.1
        assert abs(motion[1] - 10.0) < 0.1

    def test_get_motion_vector_with_interpolation(self):
        """Motion vector uses interpolation."""
        tracker = BboxTracker()
        tracker.add_detection(0, (0, 0, 10, 10))      # center at (5, 5)
        tracker.add_detection(10, (100, 100, 10, 10)) # center at (105, 105)

        # At frame 5, interpolated center should be (55, 55)
        # Motion from frame 0 (5,5) to frame 5 (55,55) = (50, 50)
        motion = tracker.get_motion_vector(0, 5)
        assert motion is not None
        assert abs(motion[0] - 50.0) < 0.1
        assert abs(motion[1] - 50.0) < 0.1

    def test_get_motion_vector_no_detections(self):
        """Motion vector with no detections returns None."""
        tracker = BboxTracker()
        assert tracker.get_motion_vector(0, 1) is None

    def test_get_trajectory_confidence_empty(self):
        """Empty tracker has zero confidence."""
        tracker = BboxTracker()
        assert tracker.get_trajectory_confidence() == 0.0

    def test_get_trajectory_confidence_single_detection(self):
        """Single detection has moderate confidence."""
        tracker = BboxTracker()
        tracker.add_detection(0, (10, 20, 100, 150), confidence=0.95)
        confidence = tracker.get_trajectory_confidence()
        assert 0.4 < confidence <= 1.0

    def test_get_trajectory_confidence_multiple_detections(self):
        """Multiple detections increase confidence."""
        tracker = BboxTracker()
        tracker.add_detection(0, (10, 20, 100, 150), confidence=0.95)
        tracker.add_detection(5, (12, 22, 100, 150), confidence=0.9)
        tracker.add_detection(10, (14, 24, 100, 150), confidence=0.85)

        confidence = tracker.get_trajectory_confidence()
        avg_confidence = (0.95 + 0.9 + 0.85) / 3
        assert abs(confidence - avg_confidence) < 0.01


class TestYOLOTrackerWrapper:
    """Test YOLOTrackerWrapper class."""

    def test_init_no_model(self):
        """Initialize without model path."""
        wrapper = YOLOTrackerWrapper()
        assert wrapper.model_path is None
        assert wrapper.model is None

    def test_init_with_threshold(self):
        """Initialize with confidence threshold."""
        for threshold in [0.3, 0.5, 0.9]:
            wrapper = YOLOTrackerWrapper(confidence_threshold=threshold)
            assert wrapper.confidence_threshold == threshold

    def test_detect_no_model(self):
        """Detection with no model returns empty."""
        wrapper = YOLOTrackerWrapper()
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128

        bboxes = wrapper.detect(image)
        assert bboxes == []

    def test_detect_on_frames_empty(self):
        """Detect on empty frame list."""
        wrapper = YOLOTrackerWrapper()
        tracker = wrapper.detect_on_frames([])
        assert len(tracker.detections) == 0

    def test_detect_on_frames_sparse_interval(self):
        """Sparse sampling skips frames."""
        wrapper = YOLOTrackerWrapper()
        frames = [np.ones((100, 100, 3), dtype=np.uint8) for _ in range(10)]

        # With sparse_interval=3, should only try frames 0, 3, 6, 9
        tracker = wrapper.detect_on_frames(frames, sparse_interval=3)

        # Since no model, should have 0 detections, but that's OK
        assert len(tracker.detections) == 0


class TestIntegrationTracking:
    """Integration tests for full tracking workflow."""

    def test_full_sparse_tracking_workflow(self):
        """End-to-end sparse detection and smoothing."""
        tracker = BboxTracker(motion_smoothing_factor=0.3)

        # Simulate sparse detections: every 5 frames
        tracker.add_detection(0, (0, 0, 50, 50), confidence=0.9)
        tracker.add_detection(5, (10, 10, 50, 50), confidence=0.85)
        tracker.add_detection(10, (20, 20, 50, 50), confidence=0.9)

        # Get smooth trajectory for all 10 frames
        traj = tracker.smooth_trajectory([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

        # Verify trajectory structure
        assert len(traj.frame_ids) == 11
        assert len(traj.bboxes) == 11

        # First frame should match detection
        assert traj.bboxes[0] == (0, 0, 50, 50)

        # Frame 5 should match detection
        assert traj.bboxes[5] == (10, 10, 50, 50)

        # Frame 10 should match detection
        assert traj.bboxes[10] == (20, 20, 50, 50)

        # Intermediate frames should be interpolated and smoothed
        # Frame 1 should be between 0 and interpolated frame 1
        assert traj.bboxes[1] is not None

    def test_motion_tracking_sequence(self):
        """Track moving watermark."""
        tracker = BboxTracker(motion_smoothing_factor=0.2)

        # Watermark moving from (0,0) to (100,100)
        tracker.add_detection(0, (0, 0, 50, 50))
        tracker.add_detection(20, (100, 100, 50, 50))

        # Check motion vector
        motion = tracker.get_motion_vector(0, 20)
        assert motion is not None
        # Center moves from (25,25) to (125,125) = (100,100)
        assert abs(motion[0] - 100.0) < 1.0
        assert abs(motion[1] - 100.0) < 1.0

        # Confidence should be high
        confidence = tracker.get_trajectory_confidence()
        assert confidence > 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
