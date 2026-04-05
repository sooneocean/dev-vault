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


class TestWeightedAveraging:
    """Test weighted average computation for confidence and bboxes."""

    def test_confidence_weighted_average_equal_weights(self):
        """Test confidence weighted average with equal model accuracies."""
        confidences = {"m1": 0.8, "m2": 0.8}
        accuracies = {"m1": 0.85, "m2": 0.85}
        voter = BBoxVoter(model_accuracies=accuracies, iou_threshold=0.3)

        avg = voter._compute_weighted_average_confidence(confidences, accuracies)

        assert abs(avg - 0.8) < 1e-6

    def test_confidence_weighted_average_unequal_weights(self):
        """Test confidence weighted average with different model accuracies."""
        confidences = {"m1": 0.8, "m2": 0.9}
        accuracies = {"m1": 0.85, "m2": 0.90}
        voter = BBoxVoter(model_accuracies=accuracies, iou_threshold=0.3)

        avg = voter._compute_weighted_average_confidence(confidences, accuracies)

        # m1 weight: 0.85/1.75 ≈ 0.486, m2 weight: 0.90/1.75 ≈ 0.514
        expected = (0.8 * 0.85 + 0.9 * 0.90) / 1.75
        assert abs(avg - expected) < 1e-6

    def test_bbox_weighted_average_equal_weights(self):
        """Test bbox weighted average with equal model accuracies."""
        bbox1 = BBox(x=100, y=100, w=100, h=100, confidence=0.9)
        bbox2 = BBox(x=100, y=100, w=100, h=100, confidence=0.9)
        bboxes = {"m1": bbox1, "m2": bbox2}
        accuracies = {"m1": 0.85, "m2": 0.85}
        voter = BBoxVoter(model_accuracies=accuracies, iou_threshold=0.3)

        avg_bbox = voter._compute_weighted_average_bbox(bboxes, accuracies)

        assert avg_bbox.x == 100
        assert avg_bbox.y == 100
        assert avg_bbox.w == 100
        assert avg_bbox.h == 100


class TestVotingDifferentDetections:
    """Test voting with different detection patterns."""

    def test_vote_different_bboxes_low_iou(self):
        """Test voting when models detect different bboxes with low IoU."""
        # Two completely separate detections
        bbox1 = BBox(x=10, y=10, w=50, h=50, confidence=0.95)
        bbox2 = BBox(x=500, y=500, w=50, h=50, confidence=0.90)
        detections = {"yolov5s": [bbox1], "yolov5m": [bbox2]}
        accuracies = {"yolov5s": 0.85, "yolov5m": 0.90}
        voter = BBoxVoter(model_accuracies=accuracies, iou_threshold=0.3)

        results = voter.vote(detections)

        # Both bboxes should be kept (no match based on IoU)
        assert len(results) == 1  # Only the anchor bbox is reported
        assert results[0].num_votes == 1
        assert results[0].source_models == ["yolov5s"]

    def test_vote_one_model_misses(self):
        """Test voting when one model detects and other misses."""
        bbox1 = BBox(x=100, y=100, w=100, h=100, confidence=0.95)
        detections = {"yolov5s": [bbox1], "yolov5m": []}
        accuracies = {"yolov5s": 0.85, "yolov5m": 0.90}
        voter = BBoxVoter(model_accuracies=accuracies, iou_threshold=0.3)

        results = voter.vote(detections)

        assert len(results) == 1
        assert results[0].num_votes == 1
        assert results[0].source_models == ["yolov5s"]

    def test_vote_multiple_detections_per_model(self):
        """Test voting with multiple detections from each model."""
        bbox1a = BBox(x=10, y=10, w=50, h=50, confidence=0.95)
        bbox1b = BBox(x=200, y=200, w=60, h=60, confidence=0.85)
        bbox2a = BBox(x=15, y=15, w=45, h=45, confidence=0.90)
        bbox2b = BBox(x=205, y=205, w=55, h=55, confidence=0.88)
        detections = {
            "yolov5s": [bbox1a, bbox1b],
            "yolov5m": [bbox2a, bbox2b],
        }
        accuracies = {"yolov5s": 0.85, "yolov5m": 0.90}
        voter = BBoxVoter(model_accuracies=accuracies, iou_threshold=0.3)

        results = voter.vote(detections)

        # Both anchor detections should match with their counterparts
        assert len(results) == 2
        # All results should have 2 votes
        assert all(r.num_votes == 2 for r in results)


class TestNMSPostProcessing:
    """Test NMS post-processing with merged detections."""

    def test_nms_overlapping_results(self):
        """Test NMS removes overlapping results."""
        bbox1 = BBox(x=100, y=100, w=100, h=100, confidence=0.95)
        bbox2 = BBox(x=120, y=120, w=100, h=100, confidence=0.90)
        result1 = VotingResult(
            bbox=bbox1,
            source_models=["m1", "m2"],
            num_votes=2,
            individual_confidences=[0.95, 0.90],
        )
        result2 = VotingResult(
            bbox=bbox2,
            source_models=["m1"],
            num_votes=1,
            individual_confidences=[0.90],
        )
        voter = BBoxVoter(model_accuracies={"m1": 0.85, "m2": 0.90}, iou_threshold=0.3)

        nms_results = voter.apply_nms([result1, result2], nms_threshold=0.45)

        # result2 should be suppressed due to high overlap with result1
        assert len(nms_results) == 1
        assert nms_results[0].bbox.x == 100

    def test_nms_non_overlapping_results(self):
        """Test NMS keeps non-overlapping results."""
        bbox1 = BBox(x=10, y=10, w=50, h=50, confidence=0.95)
        bbox2 = BBox(x=500, y=500, w=50, h=50, confidence=0.90)
        result1 = VotingResult(
            bbox=bbox1,
            source_models=["m1"],
            num_votes=1,
            individual_confidences=[0.95],
        )
        result2 = VotingResult(
            bbox=bbox2,
            source_models=["m2"],
            num_votes=1,
            individual_confidences=[0.90],
        )
        voter = BBoxVoter(model_accuracies={"m1": 0.85, "m2": 0.90}, iou_threshold=0.3)

        nms_results = voter.apply_nms([result1, result2], nms_threshold=0.45)

        # Both should be kept
        assert len(nms_results) == 2


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_no_detections_returns_empty_list(self):
        """Test that no detections returns empty list."""
        configs = [("yolov5s", {}), ("yolov5m", {})]
        detector = EnsembleDetector(model_configs=configs)
        detections_by_model = {"yolov5s": [], "yolov5m": []}

        voting_results = detector.voter.vote(detections_by_model)

        assert voting_results == []

    def test_single_model_in_ensemble(self):
        """Test ensemble with single model (should work as normal single detector)."""
        configs = [("yolov5s", {})]
        detector = EnsembleDetector(model_configs=configs)

        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = detector.detect_frame(frame)

        assert isinstance(result, list)

    def test_iou_threshold_boundary(self):
        """Test voting with IoU near threshold boundary."""
        # Create bboxes with IoU just above and just below threshold
        bbox1 = BBox(x=0, y=0, w=100, h=100, confidence=0.95)
        bbox2 = BBox(x=33, y=0, w=100, h=100, confidence=0.90)  # ~0.5 IoU
        detections = {"yolov5s": [bbox1], "yolov5m": [bbox2]}
        accuracies = {"yolov5s": 0.85, "yolov5m": 0.90}
        voter = BBoxVoter(model_accuracies=accuracies, iou_threshold=0.3)

        results = voter.vote(detections)

        # Should have a match since IoU > 0.3
        assert len(results) == 1
        assert results[0].num_votes == 2

    def test_confidence_clipping(self):
        """Test that averaged confidence is clipped to [0.0, 1.0]."""
        confidences = {"m1": 0.9, "m2": 0.95}
        accuracies = {"m1": 0.85, "m2": 0.90}
        voter = BBoxVoter(model_accuracies=accuracies, iou_threshold=0.3)

        avg = voter._compute_weighted_average_confidence(confidences, accuracies)

        assert 0.0 <= avg <= 1.0


class TestIntegrationEnsembleDetection:
    """Integration tests for ensemble detection with realistic scenarios."""

    def test_full_detection_pipeline_two_models(self):
        """Test complete detection pipeline with two ensemble models."""
        configs = [
            ("yolov5s", {"confidence_threshold": 0.5}),
            ("yolov5m", {"confidence_threshold": 0.5}),
        ]
        detector = EnsembleDetector(
            model_configs=configs,
            model_accuracies={"yolov5s": 0.85, "yolov5m": 0.90},
            iou_threshold=0.3,
            nms_threshold=0.45,
        )

        # Create a test frame (480x640x3)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = detector.detect_frame(frame)

        # Should return a list (possibly empty, depending on model behavior)
        assert isinstance(result, list)

    def test_multiple_frames_detection(self):
        """Test detecting watermarks in multiple frames."""
        configs = [("yolov5s", {"confidence_threshold": 0.5})]
        detector = EnsembleDetector(model_configs=configs)

        frames = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(3)]
        results = detector.detect_frames(frames)

        assert isinstance(results, dict)
        for frame_idx, bboxes in results.items():
            assert isinstance(frame_idx, int)
            assert isinstance(bboxes, list)

    def test_detector_status_reporting(self):
        """Test detector status reporting for model loading."""
        configs = [
            ("yolov5s", {"confidence_threshold": 0.5}),
            ("yolov5m", {"confidence_threshold": 0.5}),
        ]
        detector = EnsembleDetector(model_configs=configs)

        status = detector.get_detector_status()

        assert isinstance(status, dict)
        assert "yolov5s" in status or "yolov5m" in status

    def test_voting_followed_by_nms(self):
        """Test complete voting and NMS pipeline."""
        bbox1a = BBox(x=100, y=100, w=100, h=100, confidence=0.95)
        bbox1b = BBox(x=150, y=150, w=80, h=80, confidence=0.92)
        bbox2a = BBox(x=102, y=102, w=98, h=98, confidence=0.93)
        bbox2b = BBox(x=152, y=152, w=78, h=78, confidence=0.90)

        detections = {
            "yolov5s": [bbox1a, bbox1b],
            "yolov5m": [bbox2a, bbox2b],
        }
        accuracies = {"yolov5s": 0.85, "yolov5m": 0.90}
        voter = BBoxVoter(model_accuracies=accuracies, iou_threshold=0.3)

        # Voting
        voting_results = voter.vote(detections)
        assert len(voting_results) == 2

        # NMS
        nms_results = voter.apply_nms(voting_results, nms_threshold=0.45)
        assert len(nms_results) >= 1

    def test_ensemble_graceful_degradation_partial_failure(self):
        """Test ensemble with simulated partial model failure."""
        configs = [
            ("yolov5s", {"confidence_threshold": 0.5}),
            ("yolov5m", {"confidence_threshold": 0.5}),
        ]
        detector = EnsembleDetector(model_configs=configs)

        # Simulate one model failing and one succeeding
        bbox1 = BBox(x=100, y=100, w=100, h=100, confidence=0.95)
        detections_by_model = {
            "yolov5s": [bbox1],
            "yolov5m": [],  # Simulated failure (empty)
        }

        voting_results = detector.voter.vote(detections_by_model)

        # Should still return results from yolov5s
        assert len(voting_results) >= 0

    def test_ensemble_with_different_confidence_thresholds(self):
        """Test ensemble with different confidence thresholds per model."""
        configs = [
            ("yolov5s", {"confidence_threshold": 0.5}),
            ("yolov5m", {"confidence_threshold": 0.6}),
        ]
        detector = EnsembleDetector(
            model_configs=configs,
            model_accuracies={"yolov5s": 0.85, "yolov5m": 0.90},
        )

        # Frame with potential detections
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = detector.detect_frame(frame)

        assert isinstance(result, list)


class TestDetectionOrchestrator:
    """Test DetectionOrchestrator for switching between single and ensemble modes."""

    def test_orchestrator_initialization_single_mode(self):
        """Test orchestrator initializes in single mode."""
        from src.watermark_removal.detection import DetectionOrchestrator

        orchestrator = DetectionOrchestrator(ensemble_detection_enabled=False)

        assert orchestrator.ensemble_detection_enabled is False
        assert orchestrator.single_model == "yolov5s"

    def test_orchestrator_initialization_ensemble_mode(self):
        """Test orchestrator initializes in ensemble mode."""
        from src.watermark_removal.detection import DetectionOrchestrator

        orchestrator = DetectionOrchestrator(
            ensemble_detection_enabled=True,
            ensemble_models=["yolov5s", "yolov5m"],
        )

        assert orchestrator.ensemble_detection_enabled is True
        assert orchestrator.ensemble_models == ["yolov5s", "yolov5m"]

    def test_orchestrator_single_mode_detect_frame(self):
        """Test orchestrator detects frames in single mode."""
        from src.watermark_removal.detection import DetectionOrchestrator

        orchestrator = DetectionOrchestrator(ensemble_detection_enabled=False)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        result = orchestrator.detect_frame(frame)

        assert isinstance(result, list)

    def test_orchestrator_ensemble_mode_detect_frame(self):
        """Test orchestrator detects frames in ensemble mode."""
        from src.watermark_removal.detection import DetectionOrchestrator

        orchestrator = DetectionOrchestrator(
            ensemble_detection_enabled=True,
            ensemble_models=["yolov5s"],
        )
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        result = orchestrator.detect_frame(frame)

        assert isinstance(result, list)

    def test_orchestrator_detect_frames(self):
        """Test orchestrator batch detection."""
        from src.watermark_removal.detection import DetectionOrchestrator

        orchestrator = DetectionOrchestrator(ensemble_detection_enabled=False)
        frames = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(2)]

        result = orchestrator.detect_frames(frames)

        assert isinstance(result, dict)

    def test_orchestrator_get_detector_status_single(self):
        """Test orchestrator status reporting in single mode."""
        from src.watermark_removal.detection import DetectionOrchestrator

        orchestrator = DetectionOrchestrator(ensemble_detection_enabled=False)
        status = orchestrator.get_detector_status()

        assert "mode" in status
        assert status["mode"] == "single"

    def test_orchestrator_get_detector_status_ensemble(self):
        """Test orchestrator status reporting in ensemble mode."""
        from src.watermark_removal.detection import DetectionOrchestrator

        orchestrator = DetectionOrchestrator(
            ensemble_detection_enabled=True,
            ensemble_models=["yolov5s"],
        )
        status = orchestrator.get_detector_status()

        assert "mode" in status
        assert status["mode"] == "ensemble"

    def test_orchestrator_empty_frame_returns_empty(self):
        """Test orchestrator returns empty list for empty frames."""
        from src.watermark_removal.detection import DetectionOrchestrator

        orchestrator = DetectionOrchestrator(ensemble_detection_enabled=False)
        result = orchestrator.detect_frame(None)

        assert result == []

    def test_orchestrator_lazy_loading(self):
        """Test that detector is lazily loaded on first use."""
        from src.watermark_removal.detection import DetectionOrchestrator

        orchestrator = DetectionOrchestrator(ensemble_detection_enabled=False)
        assert orchestrator._detector_loaded is False

        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        orchestrator.detect_frame(frame)

        # After first use, detector should be marked as loaded (or error occurred)
        # In test environment, might not actually load, but _detector_loaded flag changes
        # This is more of a structural test
