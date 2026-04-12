"""
Dynamic watermark tracking using YOLO-based detection with temporal smoothing.

Handles sparse frame detections, bbox interpolation, and trajectory smoothing
for moving watermarks across video frames.
"""

import logging
import numpy as np
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BboxDetection:
    """Single bbox detection for a frame.

    Attributes:
        frame_id: Frame index
        bbox: (x, y, w, h) bounding box in original frame
        confidence: Detection confidence [0.0, 1.0]
    """
    frame_id: int
    bbox: Tuple[float, float, float, float]  # (x, y, w, h)
    confidence: float


@dataclass
class BboxTrajectory:
    """Bounding box trajectory across frame range.

    Attributes:
        frame_ids: List of frame indices
        bboxes: Corresponding bboxes (x, y, w, h)
    """
    frame_ids: List[int]
    bboxes: List[Tuple[float, float, float, float]]


class BboxTracker:
    """
    Track bounding boxes across frames with interpolation and smoothing.

    Handles sparse detections (not all frames detected) and provides:
    - Linear interpolation between detected frames
    - Temporal smoothing of trajectory
    - Motion estimation and adaptive filtering
    """

    def __init__(self, motion_smoothing_factor: float = 0.3):
        """
        Initialize bbox tracker.

        Args:
            motion_smoothing_factor: Alpha for temporal smoothing of trajectory [0.0-1.0]
                                    Higher = more smoothing, lower = more responsive to motion
        """
        if not 0.0 <= motion_smoothing_factor <= 1.0:
            raise ValueError(f"motion_smoothing_factor must be in [0.0, 1.0], got {motion_smoothing_factor}")

        self.motion_smoothing_factor = motion_smoothing_factor
        self.detections: Dict[int, BboxDetection] = {}

    def add_detection(self, frame_id: int, bbox: Tuple[float, float, float, float],
                     confidence: float = 1.0) -> None:
        """
        Register a bbox detection for a frame.

        Args:
            frame_id: Frame index
            bbox: (x, y, w, h) bounding box
            confidence: Detection confidence [0.0, 1.0]
        """
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"confidence must be in [0.0, 1.0], got {confidence}")

        self.detections[frame_id] = BboxDetection(frame_id, bbox, confidence)
        logger.debug(f"Added detection for frame {frame_id}: {bbox}, confidence={confidence:.2f}")

    def interpolate(self, frame_id: int) -> Optional[Tuple[float, float, float, float]]:
        """
        Interpolate bbox for a frame using detected keyframes.

        Linear interpolation between detected frames.

        Args:
            frame_id: Frame index to interpolate

        Returns:
            Interpolated bbox (x, y, w, h) or None if no detections
        """
        if not self.detections:
            return None

        # If exact detection exists, return it
        if frame_id in self.detections:
            return self.detections[frame_id].bbox

        # Find surrounding detected frames
        detected_frames = sorted(self.detections.keys())

        if frame_id < detected_frames[0]:
            # Before first detection: return first detection
            return self.detections[detected_frames[0]].bbox

        if frame_id > detected_frames[-1]:
            # After last detection: return last detection
            return self.detections[detected_frames[-1]].bbox

        # Find frames to interpolate between
        prev_frame = max([f for f in detected_frames if f < frame_id])
        next_frame = min([f for f in detected_frames if f > frame_id])

        prev_bbox = self.detections[prev_frame].bbox
        next_bbox = self.detections[next_frame].bbox

        # Linear interpolation
        t = (frame_id - prev_frame) / (next_frame - prev_frame)
        interpolated = tuple(
            (1 - t) * prev_bbox[i] + t * next_bbox[i]
            for i in range(4)
        )

        return interpolated

    def smooth_trajectory(self, frame_ids: List[int]) -> BboxTrajectory:
        """
        Generate smoothed trajectory for frame range.

        Interpolates all frames, then applies temporal smoothing.
        Uses exact detected bboxes when available, interpolates between detections.

        Args:
            frame_ids: List of frame indices to track

        Returns:
            BboxTrajectory with smoothed bboxes
        """
        if not frame_ids:
            return BboxTrajectory([], [])

        if not self.detections:
            logger.warning("No detections available for smoothing")
            return BboxTrajectory([], [])

        # Step 1: Interpolate all frames
        interpolated = []
        for fid in frame_ids:
            bbox = self.interpolate(fid)
            if bbox is None:
                # Fallback to first detection
                first_bbox = self.detections[min(self.detections.keys())].bbox
                interpolated.append(first_bbox)
            else:
                interpolated.append(bbox)

        # Step 2: Apply temporal smoothing using alpha blending
        # But preserve exact detections (don't smooth detected frames)
        smoothed = []
        for i, bbox in enumerate(interpolated):
            if i == 0:
                # First frame: no previous
                smoothed.append(bbox)
            else:
                # Check if this frame has exact detection
                frame_id = frame_ids[i]
                if frame_id in self.detections:
                    # Use exact detection, no smoothing
                    smoothed.append(bbox)
                else:
                    # Blend with previous smoothed bbox
                    prev_bbox = smoothed[-1]
                    blended = tuple(
                        (1 - self.motion_smoothing_factor) * bbox[j] +
                        self.motion_smoothing_factor * prev_bbox[j]
                        for j in range(4)
                    )
                    smoothed.append(blended)

        logger.info(f"Generated smooth trajectory for {len(frame_ids)} frames")
        return BboxTrajectory(frame_ids, smoothed)

    def get_motion_vector(self, frame_id_1: int, frame_id_2: int) -> Optional[Tuple[float, float]]:
        """
        Estimate motion vector (dx, dy) between two frames.

        Args:
            frame_id_1: First frame
            frame_id_2: Second frame

        Returns:
            (dx, dy) motion vector in pixels, or None
        """
        bbox1 = self.interpolate(frame_id_1)
        bbox2 = self.interpolate(frame_id_2)

        if bbox1 is None or bbox2 is None:
            return None

        # Center of bbox: (x + w/2, y + h/2)
        center1 = (bbox1[0] + bbox1[2] / 2, bbox1[1] + bbox1[3] / 2)
        center2 = (bbox2[0] + bbox2[2] / 2, bbox2[1] + bbox2[3] / 2)

        return (center2[0] - center1[0], center2[1] - center1[1])

    def get_trajectory_confidence(self) -> float:
        """
        Estimate trajectory confidence based on detection density.

        Returns:
            Confidence score [0.0, 1.0] based on detection spacing and count
        """
        if not self.detections:
            return 0.0

        if len(self.detections) == 1:
            return 0.5

        # Average detection confidence
        avg_confidence = np.mean([d.confidence for d in self.detections.values()])

        # Frame coverage metric: how many frames detected vs sparse
        # (This is informational; assumes detections cover most critical frames)
        return float(avg_confidence)


class YOLOTrackerWrapper:
    """
    Wrapper for YOLO-based watermark detection.

    Encapsulates YOLO model loading and inference for bbox detection.
    Deferred: Actual YOLO integration pending model availability.
    """

    def __init__(self, model_path: Optional[str] = None, confidence_threshold: float = 0.5):
        """
        Initialize YOLO tracker wrapper.

        Args:
            model_path: Path to YOLO model weights (e.g., "yolov8n.pt")
            confidence_threshold: Min confidence for detections [0.0, 1.0]
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.model = None

        if model_path:
            self._load_model()

    def _load_model(self) -> None:
        """Load YOLO model from path."""
        try:
            import yolov8
            logger.info(f"Loading YOLO model from {self.model_path}")
            self.model = yolov8.load(self.model_path)
        except ImportError:
            logger.warning("YOLOv8 not available; inference disabled. Install: pip install ultralytics")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")

    def detect(self, image: np.ndarray) -> List[Tuple[float, float, float, float]]:
        """
        Detect watermark bboxes in image.

        Args:
            image: BGR ndarray (H, W, 3), uint8

        Returns:
            List of (x, y, w, h) bboxes detected
        """
        if self.model is None:
            logger.warning("YOLO model not loaded; returning empty detections")
            return []

        try:
            results = self.model.predict(image, conf=self.confidence_threshold)
            bboxes = []

            for result in results:
                for box in result.boxes:
                    # Extract bbox in (x, y, w, h) format
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    x, y, w, h = x1, y1, (x2 - x1), (y2 - y1)
                    bboxes.append((float(x), float(y), float(w), float(h)))

            return bboxes
        except Exception as e:
            logger.error(f"YOLO inference failed: {e}")
            return []

    def detect_on_frames(self, frames: List[np.ndarray],
                        sparse_interval: int = 1) -> BboxTracker:
        """
        Run detection on frame sequence with optional sparse sampling.

        Args:
            frames: List of BGR ndarrays
            sparse_interval: Detect every Nth frame (>1 for sparse detection)

        Returns:
            BboxTracker with detections registered
        """
        tracker = BboxTracker()

        for frame_id, frame in enumerate(frames):
            if frame_id % sparse_interval != 0:
                continue

            bboxes = self.detect(frame)

            if bboxes:
                # Register best (highest confidence or all?)
                # For now, register first/primary bbox
                bbox = bboxes[0]
                tracker.add_detection(frame_id, bbox, confidence=0.9)  # Placeholder confidence
                logger.debug(f"Frame {frame_id}: detected bbox {bbox}")
            else:
                logger.debug(f"Frame {frame_id}: no detection")

        return tracker
