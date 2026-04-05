"""Automatic watermark detection module."""

from .ensemble_detector import BBoxVoter, EnsembleDetector, VotingResult
from .watermark_detector import BBox, WatermarkDetector
from .detection_orchestrator import DetectionOrchestrator

__all__ = ["BBox", "WatermarkDetector", "EnsembleDetector", "BBoxVoter", "VotingResult", "DetectionOrchestrator"]
