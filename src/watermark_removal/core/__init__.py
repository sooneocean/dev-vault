"""Core types and checkpoint management for the watermark removal system."""

from .checkpoint import Checkpoint, CHECKPOINT_VERSION
from .config_manager import ConfigManager
from .types import (
    CropRegion,
    Frame,
    InpaintConfig,
    Mask,
    MaskType,
    ProcessConfig,
)

__all__ = [
    "Checkpoint",
    "CHECKPOINT_VERSION",
    "ConfigManager",
    "CropRegion",
    "Frame",
    "InpaintConfig",
    "Mask",
    "MaskType",
    "ProcessConfig",
]
