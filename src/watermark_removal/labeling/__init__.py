"""Label Studio annotation workflow integration for watermark removal."""

from .label_studio_client import (
    LabelStudioClient,
    PredictionBBox,
    LabelStudioTask,
)
from .dataset_exporter import (
    CoordinateConverter,
    CocoExporter,
    YoloExporter,
    BBoxPixel,
    BBoxPercentage,
)
from .label_studio_setup import (
    DockerComposeGenerator,
    ProjectInitializer,
    APIKeyManager,
    LabelStudioSetup,
)

__all__ = [
    "LabelStudioClient",
    "PredictionBBox",
    "LabelStudioTask",
    "CoordinateConverter",
    "CocoExporter",
    "YoloExporter",
    "BBoxPixel",
    "BBoxPercentage",
    "DockerComposeGenerator",
    "ProjectInitializer",
    "APIKeyManager",
    "LabelStudioSetup",
]
