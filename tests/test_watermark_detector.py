"""Tests for watermark detection module."""

import numpy as np
import pytest

from src.watermark_removal.detection import BBox, WatermarkDetector


class TestBBoxDataclass:
    """Test BBox dataclass functionality."""

    def test_bbox_creation(self):
        """Test creating a BBox instance."""
        bbox = BBox(x=100, y=200, w=300, h=400, confidence=0.95)
        assert bbox.x == 100
        assert bbox.y == 200
        assert bbox.w == 300
        assert bbox.h == 400
        assert bbox.confidence == 0.95

    def test_bbox_to_dict(self):
        """Test BBox serialization to dict."""
        bbox = BBox(x=50, y=100, w=200, h=250, confidence=0.87)
        d = bbox.to_dict()
        assert d == {"x": 50, "y": 100, "w": 200, "h": 250, "confidence": 0.87}

    def test_bbox_from_dict(self):
        """Test BBox deserialization from dict."""
        d = {"x": 75, "y": 150, "w": 250, "h": 300, "confidence": 0.92}
        bbox = BBox.from_dict(d)
        assert bbox.x == 75
        assert bbox.y == 150
        assert bbox.w == 250
        assert bbox.h == 300
        assert bbox.confidence == 0.92

    def test_bbox_from_dict_missing_confidence(self):
        """Test BBox from dict with missing confidence (default to 1.0)."""
        d = {"x": 10, "y": 20, "w": 30, "h": 40}
        bbox = BBox.from_dict(d)
        assert bbox.confidence == 1.0

    def test_bbox_round_trip(self):
        """Test BBox serialization round-trip."""
        original = BBox(x=123, y=456, w=789, h=321, confidence=0.75)
        serialized = original.to_dict()
        restored = BBox.from_dict(serialized)
        assert restored.x == original.x
        assert restored.y == original.y
        assert restored.w == original.w
        assert restored.h == original.h
        assert restored.confidence == original.confidence


class TestWatermarkDetectorInitialization:
    """Test WatermarkDetector initialization."""

    def test_initialization_default(self):
        """Test WatermarkDetector initializes with defaults."""
        detector = WatermarkDetector()
        assert detector.model_name == "yolov5s"
        assert detector.confidence_threshold == 0.5
        assert detector.nms_threshold == 0.45
        assert detector.model is None
        assert detector._model_loaded is False

    def test_initialization_custom_model(self):
        """Test initialization with custom model."""
        detector = WatermarkDetector(
            model_name="yolov5m",
            confidence_threshold=0.6,
            nms_threshold=0.4,
        )
        assert detector.model_name == "yolov5m"
        assert detector.confidence_threshold == 0.6
        assert detector.nms_threshold == 0.4

    def test_initialization_invalid_confidence(self):
        """Test initialization rejects invalid confidence."""
        with pytest.raises(ValueError, match="confidence_threshold must be 0.0-1.0"):
            WatermarkDetector(confidence_threshold=1.5)

    def test_initialization_invalid_nms(self):
        """Test initialization rejects invalid NMS threshold."""
        with pytest.raises(ValueError, match="nms_threshold must be 0.0-1.0"):
            WatermarkDetector(nms_threshold=-0.1)

    def test_initialization_boundary_values(self):
        """Test initialization with boundary confidence/nms values."""
        detector1 = WatermarkDetector(confidence_threshold=0.0)
        assert detector1.confidence_threshold == 0.0

        detector2 = WatermarkDetector(confidence_threshold=1.0)
        assert detector2.confidence_threshold == 1.0

        detector3 = WatermarkDetector(nms_threshold=0.0, confidence_threshold=0.5)
        assert detector3.nms_threshold == 0.0


class TestDetectFrameEdgeCases:
    """Test detect_frame method edge cases."""

    def test_detect_frame_empty_input(self):
        """Test detection with empty/None frame."""
        detector = WatermarkDetector()
        result = detector.detect_frame(None)
        assert result == []

    def test_detect_frame_empty_array(self):
        """Test detection with empty numpy array."""
        detector = WatermarkDetector()
        frame = np.array([], dtype=np.uint8)
        result = detector.detect_frame(frame)
        assert result == []

    def test_detect_frame_valid_shape(self):
        """Test detect_frame accepts valid frame shape."""
        detector = WatermarkDetector()
        # Create a dummy frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Detection may fail if model can't load, but should return empty list gracefully
        result = detector.detect_frame(frame)
        assert isinstance(result, list)

    def test_detect_frame_different_sizes(self):
        """Test detect_frame with various frame sizes."""
        detector = WatermarkDetector()

        for h, w in [(240, 320), (480, 640), (720, 1280)]:
            frame = np.zeros((h, w, 3), dtype=np.uint8)
            result = detector.detect_frame(frame)
            assert isinstance(result, list)


class TestDetectFrames:
    """Test detect_frames method."""

    def test_detect_frames_empty_list(self):
        """Test detecting empty frame list."""
        detector = WatermarkDetector()
        result = detector.detect_frames([])
        assert result == {}

    def test_detect_frames_multiple_frames(self):
        """Test detecting multiple frames."""
        detector = WatermarkDetector()
        frames = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(5)]
        result = detector.detect_frames(frames)
        assert isinstance(result, dict)
        # Without watermarks in frames, should return empty dict (or may fail gracefully)
        # Result depends on whether model loads successfully

    def test_detect_frames_return_type(self):
        """Test detect_frames returns correct type."""
        detector = WatermarkDetector()
        frames = [np.ones((100, 100, 3), dtype=np.uint8) * i for i in range(3)]
        result = detector.detect_frames(frames)
        assert isinstance(result, dict)
        # Keys should be ints (frame indices)
        for key in result.keys():
            assert isinstance(key, int)
        # Values should be lists of BBox
        for value in result.values():
            assert isinstance(value, list)


class TestFilterMethods:
    """Test filtering methods."""

    def test_filter_by_area_empty_list(self):
        """Test filtering empty bbox list."""
        detector = WatermarkDetector()
        result = detector.filter_by_area([])
        assert result == []

    def test_filter_by_area_all_pass(self):
        """Test filter_by_area where all pass."""
        detector = WatermarkDetector()
        bboxes = [
            BBox(x=0, y=0, w=50, h=50, confidence=0.9),  # Area: 2500
            BBox(x=100, y=100, w=100, h=100, confidence=0.8),  # Area: 10000
        ]
        result = detector.filter_by_area(bboxes, min_area=1000)
        assert len(result) == 2

    def test_filter_by_area_some_filtered(self):
        """Test filter_by_area where some are filtered out."""
        detector = WatermarkDetector()
        bboxes = [
            BBox(x=0, y=0, w=10, h=10, confidence=0.9),  # Area: 100
            BBox(x=100, y=100, w=50, h=50, confidence=0.8),  # Area: 2500
        ]
        result = detector.filter_by_area(bboxes, min_area=500)
        assert len(result) == 1
        assert result[0].w == 50

    def test_filter_by_confidence_empty_list(self):
        """Test filtering empty confidence list."""
        detector = WatermarkDetector()
        result = detector.filter_by_confidence([], 0.7)
        assert result == []

    def test_filter_by_confidence_all_pass(self):
        """Test filter_by_confidence where all pass."""
        detector = WatermarkDetector()
        bboxes = [
            BBox(x=0, y=0, w=50, h=50, confidence=0.95),
            BBox(x=100, y=100, w=100, h=100, confidence=0.85),
        ]
        result = detector.filter_by_confidence(bboxes, 0.7)
        assert len(result) == 2

    def test_filter_by_confidence_some_filtered(self):
        """Test filter_by_confidence where some are filtered out."""
        detector = WatermarkDetector()
        bboxes = [
            BBox(x=0, y=0, w=50, h=50, confidence=0.95),
            BBox(x=100, y=100, w=100, h=100, confidence=0.60),
        ]
        result = detector.filter_by_confidence(bboxes, 0.7)
        assert len(result) == 1
        assert result[0].confidence == 0.95


class TestGetLargestBBox:
    """Test largest bbox selection."""

    def test_get_largest_bbox_empty(self):
        """Test get_largest_bbox with empty list."""
        detector = WatermarkDetector()
        result = detector.get_largest_bbox([])
        assert result is None

    def test_get_largest_bbox_single(self):
        """Test get_largest_bbox with single bbox."""
        detector = WatermarkDetector()
        bbox = BBox(x=100, y=200, w=300, h=400, confidence=0.9)
        result = detector.get_largest_bbox([bbox])
        assert result == bbox

    def test_get_largest_bbox_multiple(self):
        """Test get_largest_bbox selects largest by area."""
        detector = WatermarkDetector()
        bboxes = [
            BBox(x=0, y=0, w=50, h=50, confidence=0.9),  # Area: 2500
            BBox(x=100, y=100, w=100, h=100, confidence=0.8),  # Area: 10000 (largest)
            BBox(x=200, y=200, w=75, h=60, confidence=0.85),  # Area: 4500
        ]
        result = detector.get_largest_bbox(bboxes)
        assert result.w == 100
        assert result.h == 100

    def test_get_largest_bbox_same_area(self):
        """Test get_largest_bbox when multiple have same area."""
        detector = WatermarkDetector()
        bboxes = [
            BBox(x=0, y=0, w=100, h=100, confidence=0.9),  # Area: 10000
            BBox(x=100, y=100, w=50, h=200, confidence=0.8),  # Area: 10000
        ]
        result = detector.get_largest_bbox(bboxes)
        # Should return one with largest area (both have same, so first encountered)
        assert result.w * result.h == 10000


class TestDetectorWithMockData:
    """Test detector behavior with mock detection results."""

    def test_detector_configuration_preservation(self):
        """Test that detector preserves configuration."""
        detector = WatermarkDetector(
            model_name="yolov5m",
            confidence_threshold=0.7,
            nms_threshold=0.5,
        )
        assert detector.model_name == "yolov5m"
        assert detector.confidence_threshold == 0.7
        assert detector.nms_threshold == 0.5

    def test_lazy_loading_flag(self):
        """Test that model is not loaded until needed."""
        detector = WatermarkDetector()
        assert detector._model_loaded is False
        # Just creating detector shouldn't load model
        detector2 = WatermarkDetector(confidence_threshold=0.6)
        assert detector2._model_loaded is False

    def test_multiple_detector_instances(self):
        """Test creating multiple detector instances."""
        d1 = WatermarkDetector(confidence_threshold=0.5)
        d2 = WatermarkDetector(confidence_threshold=0.7)
        assert d1.confidence_threshold == 0.5
        assert d2.confidence_threshold == 0.7
        assert d1.model is d2.model  # Both None initially


class TestDetectorIntegration:
    """Integration tests for detector workflow."""

    def test_workflow_create_detect_filter(self):
        """Test workflow: create detector, handle detection results."""
        detector = WatermarkDetector(confidence_threshold=0.5)

        # Simulate detected bboxes (mock)
        mock_detections = [
            BBox(x=100, y=100, w=200, h=200, confidence=0.95),
            BBox(x=50, y=50, w=50, h=50, confidence=0.3),
        ]

        # Filter by confidence
        high_conf = detector.filter_by_confidence(mock_detections, 0.5)
        assert len(high_conf) == 1
        assert high_conf[0].confidence == 0.95

        # Filter by area
        large_area = detector.filter_by_area(mock_detections, min_area=1000)
        assert len(large_area) == 2  # Both have area >= 1000

    def test_workflow_get_largest_after_filter(self):
        """Test workflow: filter then select largest."""
        detector = WatermarkDetector()

        mock_detections = [
            BBox(x=0, y=0, w=100, h=100, confidence=0.95),  # Area: 10000
            BBox(x=200, y=200, w=30, h=30, confidence=0.85),  # Area: 900
            BBox(x=400, y=400, w=200, h=150, confidence=0.6),  # Area: 30000
        ]

        # Filter by confidence >= 0.7
        filtered = detector.filter_by_confidence(mock_detections, 0.7)
        assert len(filtered) == 2  # 0.95 and 0.85 confidence

        # Get largest
        largest = detector.get_largest_bbox(filtered)
        assert largest.w == 100  # Area: 10000 (largest among filtered)
        assert largest.h == 100

    def test_detector_frame_batch_processing(self):
        """Test processing batch of frames."""
        detector = WatermarkDetector()

        # Create batch of frames
        frames = [
            np.zeros((480, 640, 3), dtype=np.uint8),
            np.ones((480, 640, 3), dtype=np.uint8) * 128,
            np.ones((480, 640, 3), dtype=np.uint8) * 255,
        ]

        # Process batch
        results = detector.detect_frames(frames)

        # Should return dict (may be empty without real model)
        assert isinstance(results, dict)
        assert all(isinstance(k, int) for k in results.keys())
        assert all(isinstance(v, list) for v in results.values())


class TestDetectorErrorHandling:
    """Test error handling in detector."""

    def test_detect_frame_with_invalid_shape_but_nonempty(self):
        """Test detect_frame with unusual but valid shapes."""
        detector = WatermarkDetector()

        # Try with single channel (grayscale)
        frame = np.zeros((480, 640), dtype=np.uint8)
        # Should return empty list gracefully if shape is invalid
        result = detector.detect_frame(frame)
        assert isinstance(result, list)

    def test_detect_frame_wrong_dtype(self):
        """Test detect_frame with float frame."""
        detector = WatermarkDetector()
        frame = np.zeros((480, 640, 3), dtype=np.float32)
        # Should handle gracefully (may return empty or handle dtype conversion)
        result = detector.detect_frame(frame)
        assert isinstance(result, list)

    def test_filter_methods_with_invalid_inputs(self):
        """Test filter methods handle edge cases."""
        detector = WatermarkDetector()

        bboxes = [
            BBox(x=0, y=0, w=100, h=100, confidence=0.9),
        ]

        # Filter with extreme thresholds
        result1 = detector.filter_by_area(bboxes, min_area=999999)
        assert result1 == []

        result2 = detector.filter_by_confidence(bboxes, min_confidence=1.5)
        assert result2 == []
