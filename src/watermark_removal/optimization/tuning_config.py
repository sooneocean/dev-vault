"""Tuning configuration management."""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Optional


@dataclass
class TuningSearchSpace:
    """Search space definitions for hyperparameter tuning."""

    # Model weights (should sum to 1.0 after normalization)
    weight_yolov5s: tuple = (0.1, 1.0)
    weight_yolov5m: tuple = (0.1, 1.0)
    weight_yolov5l: tuple = (0.1, 1.0)

    # Detection thresholds
    confidence_threshold: tuple = (0.05, 0.95)  # Min detection confidence
    iou_threshold: tuple = (0.3, 0.7)  # IoU matching threshold
    nms_threshold: tuple = (0.3, 0.7)  # Non-max suppression threshold

    # Data augmentation
    augmentation_intensity: tuple = (0.0, 1.0)  # 0=none, 1=max augmentation

    def to_dict(self) -> Dict[str, tuple]:
        """Convert to dict for Optuna."""
        return {
            "weight_yolov5s": self.weight_yolov5s,
            "weight_yolov5m": self.weight_yolov5m,
            "weight_yolov5l": self.weight_yolov5l,
            "confidence_threshold": self.confidence_threshold,
            "iou_threshold": self.iou_threshold,
            "nms_threshold": self.nms_threshold,
            "augmentation_intensity": self.augmentation_intensity,
        }


@dataclass
class TuningParameters:
    """Tuned hyperparameters."""

    weight_yolov5s: float
    weight_yolov5m: float
    weight_yolov5l: float
    confidence_threshold: float
    iou_threshold: float
    nms_threshold: float
    augmentation_intensity: float

    def validate(self) -> bool:
        """Validate parameter ranges."""
        if not (0.0 <= self.weight_yolov5s <= 1.0):
            return False
        if not (0.0 <= self.weight_yolov5m <= 1.0):
            return False
        if not (0.0 <= self.weight_yolov5l <= 1.0):
            return False

        # Weights should sum to 1.0 (allowing small tolerance)
        weight_sum = self.weight_yolov5s + self.weight_yolov5m + self.weight_yolov5l
        if not (0.99 <= weight_sum <= 1.01):
            return False

        if not (0.0 <= self.confidence_threshold <= 1.0):
            return False
        if not (0.0 <= self.iou_threshold <= 1.0):
            return False
        if not (0.0 <= self.nms_threshold <= 1.0):
            return False
        if not (0.0 <= self.augmentation_intensity <= 1.0):
            return False

        return True

    def to_dict(self) -> dict:
        """Convert to dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "TuningParameters":
        """Create from dict."""
        return cls(**data)

    def save(self, path: str) -> bool:
        """Save to JSON file."""
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w") as f:
                json.dump(self.to_dict(), f, indent=2)

            return True
        except Exception:
            return False

    @classmethod
    def load(cls, path: str) -> Optional["TuningParameters"]:
        """Load from JSON file."""
        try:
            path = Path(path)
            if not path.exists():
                return None

            with open(path, "r") as f:
                data = json.load(f)

            return cls.from_dict(data)

        except Exception:
            return None
