"""Label Studio integration for annotation workflow.

Consolidated module containing both production HTTP client and session-aware
MVP client, dataset exporters, coordinate converters, and setup utilities.
"""

from .label_studio_client import (
    LabelStudioClient,
    LabelStudioSessionClient,
    PredictionBBox,
    LabelStudioTask,
)
from .dataset_exporter import (
    DatasetExporter,
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
    # Production HTTP client
    "LabelStudioClient",
    # Session-aware in-memory client (streaming/MVP)
    "LabelStudioSessionClient",
    # Dataclasses
    "PredictionBBox",
    "LabelStudioTask",
    # Dataset exporters
    "DatasetExporter",
    "CoordinateConverter",
    "CocoExporter",
    "YoloExporter",
    "BBoxPixel",
    "BBoxPercentage",
    # Setup utilities
    "DockerComposeGenerator",
    "ProjectInitializer",
    "APIKeyManager",
    "LabelStudioSetup",
]
