"""Tests for ensemble watermark detection module."""

import numpy as np
import pytest

from src.watermark_removal.detection import BBox, BBoxVoter, EnsembleDetector, VotingResult


class TestBBoxVoterInitialization:
    """Test BBoxVoter initialization."""

    def test_initialization_valid(self):
        """Test BBoxVoter initializes correctly."""
        accuracies = {"yolov5s": 0.85, "yolov5m": 0.90}
        voter = BBoxVoter(model_accuracies=accuracies, iou_threshold=0.3)
        assert voter.model_accuracies == accuracies
        assert voter.iou_threshold == 0.3

    def test_initialization_empty_accuracies(self):
        """Test BBoxVoter rejects empty model_accuracies."""
        with pytest.raises(ValueError, match="must not be empty"):
            BBoxVoter(model_accuracies={}, iou_threshold=0.3)


class TestBBoxIoU:
    """Test IoU computation."""

    def test_iou_identical_boxes(self):
        """Test IoU for identical bboxes (should be 1.0)."""
        bbox1 = BBox(x=0, y=0, w=100, h=100, confidence=0.9)
        bbox2 = BBox(x=0, y=0, w=100, h=100, confidence=0.8)
        voter = BBoxVoter(model_accuracies={"m1": 0.8}, iou_threshold=0.1)
        iou = voter.compute_iou(bbox1, bbox2)
        assert abs(iou - 1.0) < 1e-6

    def test_iou_no_overlap(self):
        """Test IoU for non-overlapping bboxes (should be 0.0)."""
        bbox1 = BBox(x=0, y=0, w=100, h=100, confidence=0.9)
        bbox2 = BBox(x=200, y=200, w=100, h=100, confidence=0.8)
        voter = BBoxVoter(model_accuracies={"m1": 0.8}, iou_threshold=0.1)
        iou = voter.compute_iou(bbox1, bbox2)
        assert iou == 0.0

    def test_iou_partial_overlap(self):
        """Test IoU for partially overlapping bboxes."""
        bbox1 = BBox(x=0, y=0, w=100, h=100, confidence=0.9)
        bbox2 = BBox(x=50, y=50, w=100, h=100, confidence=0.8)
        voter = BBoxVoter(model_accuracies={"m1": 0.8}, iou_threshold=0.1)
        iou = voter.compute_iou(bbox1, bbox2)
        expected = 2500 / 17500
        assert abs(iou - expected) < 1e-6


class TestVoting:
    """Test voting across multiple models."""

    def test_vote_single_model(self):
        """Test voting with single model (no merging)."""
        bbox1 = BBox(x=100, y=100, w=100, h=100, confidence=0.95)
        detections = {"yolov5s": [bbox1]}
        accuracies = {"yolov5s": 0.85}
        voter = BBoxVoter(model_accuracies=accuracies, iou_threshold=0.3)

        results = voter.vote(detections)

        assert len(results) == 1
        assert results[0].num_votes == 1
        assert results[0].source_models == ["yolov5s"]

    def test_vote_two_models_matching_bbox(self):
        """Test voting with two models detecting same bbox."""
        bbox1 = BBox(x=100, y=100, w=100, h=100, confidence=0.95)
        bbox2 = BBox(x=105, y=105, w=95, h=95, confidence=0.90)
        detections = {"yolov5s": [bbox1], "yolov5m": [bbox2]}
        accuracies = {"yolov5s": 0.85, "yolov5m": 0.90}
        voter = BBoxVoter(model_accuracies=accuracies, iou_threshold=0.3)

        results = voter.vote(detections)

        assert len(results) == 1
        assert results[0].num_votes == 2
        assert set(results[0].source_models) == {"yolov5s", "yolov5m"}

    def test_vote_no_detections(self):
        """Test voting with no detections from any model."""
        detections = {"yolov5s": [], "yolov5m": []}
        accuracies = {"yolov5s": 0.85, "yolov5m": 0.90}
        voter = BBoxVoter(model_accuracies=accuracies, iou_threshold=0.3)

        results = voter.vote(detections)

        assert results == []


class TestNMS:
    """Test Non-Maximum Suppression."""

    def test_nms_single_result(self):
        """Test NMS with single result."""
        bbox = BBox(x=100, y=100, w=100, h=100, confidence=0.95)
        result = VotingResult(
            bbox=bbox,
            source_models=["m1"],
            num_votes=1,
            individual_confidences=[0.95],
        )
        voter = BBoxVoter(model_accuracies={"m1": 0.85}, iou_threshold=0.3)

        nms_results = voter.apply_nms([result], nms_threshold=0.45)

        assert len(nms_results) == 1

    def test_nms_empty_list(self):
        """Test NMS with empty list."""
        voter = BBoxVoter(model_accuracies={"m1": 0.85}, iou_threshold=0.3)

        nms_results = voter.apply_nms([], nms_threshold=0.45)

        assert nms_results == []


class TestEnsembleDetectorInitialization:
    """Test EnsembleDetector initialization."""

    def test_initialization_valid(self):
        """Test EnsembleDetector initializes correctly."""
        configs = [
            ("yolov5s", {"confidence_threshold": 0.5}),
            ("yolov5m", {"confidence_threshold": 0.5}),
        ]
        detector = EnsembleDetector(model_configs=configs)
        assert detector.model_configs == configs
        assert detector.iou_threshold == 0.3
        assert detector.nms_threshold == 0.45

    def test_initialization_empty_configs(self):
        """Test EnsembleDetector rejects empty model_configs."""
        with pytest.raises(ValueError, match="must not be empty"):
            EnsembleDetector(model_configs=[])


class TestEnsembleDetectorDetection:
    """Test EnsembleDetector detection methods."""

    def test_detect_frame_empty_input(self):
        """Test detect_frame with empty frame."""
        configs = [("yolov5s", {})]
        detector = EnsembleDetector(model_configs=configs)

        result = detector.detect_frame(None)

        assert result == []

    def test_detect_frame_valid_shape(self):
        """Test detect_frame with valid frame shape."""
        configs = [("yolov5s", {})]
        detector = EnsembleDetector(model_configs=configs)

        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = detector.detect_frame(frame)

        assert isinstance(result, list)

    def test_detect_frames_empty_list(self):
        """Test detect_frames with empty frame list."""
        configs = [("yolov5s", {})]
        detector = EnsembleDetector(model_configs=configs)

        result = detector.detect_frames([])

        assert result == {}
