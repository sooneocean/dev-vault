"""Shared pytest fixtures for watermark removal tests."""

import tempfile
from pathlib import Path

import pytest
import yaml

from src.watermark_removal.core.types import ProcessConfig


@pytest.fixture
def temp_config_dir():
    """Create temporary directory for test configs.

    Yields:
        Path: Temporary directory path.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def base_config_dict():
    """Minimal valid configuration dictionary for Phase 1.

    Returns:
        dict: Base config with required fields.
    """
    return {
        "video_path": "/tmp/video.mp4",
        "mask_path": "/tmp/mask.png",
        "output_dir": "/tmp/output",
    }


@pytest.fixture
def phase2_temporal_config_dict(base_config_dict):
    """Phase 2 temporal smoothing configuration.

    Returns:
        dict: Config with temporal smoothing parameters.
    """
    config = base_config_dict.copy()
    config.update({
        "temporal_smooth_enabled": True,
        "temporal_smooth_alpha": 0.3,
        "use_adaptive_temporal_smoothing": True,
        "adaptive_motion_threshold": 0.05,
    })
    return config


@pytest.fixture
def phase2_tracking_config_dict(base_config_dict):
    """Phase 2 watermark tracking configuration.

    Returns:
        dict: Config with YOLO tracking parameters.
    """
    config = base_config_dict.copy()
    config.update({
        "use_watermark_tracker": True,
        "yolo_model_path": "/path/to/yolov8n.pt",
        "yolo_confidence_threshold": 0.55,
        "tracker_smoothing_factor": 0.3,
    })
    return config


@pytest.fixture
def phase2_poisson_config_dict(base_config_dict):
    """Phase 2 Poisson blending configuration.

    Returns:
        dict: Config with Poisson blending parameters.
    """
    config = base_config_dict.copy()
    config.update({
        "use_poisson_blending": True,
        "poisson_max_iterations": 100,
        "poisson_tolerance": 0.01,
    })
    return config


@pytest.fixture
def phase2_checkpoint_config_dict(base_config_dict):
    """Phase 2 checkpoint configuration.

    Returns:
        dict: Config with checkpoint parameters.
    """
    config = base_config_dict.copy()
    config.update({
        "use_checkpoints": True,
    })
    return config


@pytest.fixture
def phase2_full_config_dict(base_config_dict):
    """Full Phase 2 configuration with all features enabled.

    Returns:
        dict: Complete Phase 2 config.
    """
    config = base_config_dict.copy()
    config.update({
        "temporal_smooth_enabled": True,
        "temporal_smooth_alpha": 0.4,
        "use_adaptive_temporal_smoothing": True,
        "adaptive_motion_threshold": 0.08,
        "use_poisson_blending": True,
        "poisson_max_iterations": 200,
        "poisson_tolerance": 0.001,
        "use_watermark_tracker": True,
        "yolo_model_path": "/path/to/yolov8n.pt",
        "yolo_confidence_threshold": 0.55,
        "tracker_smoothing_factor": 0.4,
        "use_checkpoints": True,
    })
    return config


@pytest.fixture
def base_process_config():
    """Create a minimal valid ProcessConfig instance.

    Returns:
        ProcessConfig: Minimal valid configuration.
    """
    return ProcessConfig(
        video_path="/tmp/video.mp4",
        mask_path="/tmp/mask.png",
        output_dir="/tmp/output",
    )


@pytest.fixture
def phase2_temporal_process_config():
    """Create ProcessConfig with Phase 2 temporal features.

    Returns:
        ProcessConfig: Config with temporal smoothing enabled.
    """
    return ProcessConfig(
        video_path="/tmp/video.mp4",
        mask_path="/tmp/mask.png",
        output_dir="/tmp/output",
        temporal_smooth_enabled=True,
        temporal_smooth_alpha=0.3,
        use_adaptive_temporal_smoothing=True,
        adaptive_motion_threshold=0.05,
    )


@pytest.fixture
def phase2_tracking_process_config():
    """Create ProcessConfig with Phase 2 tracking features.

    Returns:
        ProcessConfig: Config with YOLO tracking enabled.
    """
    return ProcessConfig(
        video_path="/tmp/video.mp4",
        mask_path="/tmp/mask.png",
        output_dir="/tmp/output",
        use_watermark_tracker=True,
        yolo_model_path="/path/to/yolov8n.pt",
        yolo_confidence_threshold=0.55,
        tracker_smoothing_factor=0.3,
    )


@pytest.fixture
def phase2_poisson_process_config():
    """Create ProcessConfig with Phase 2 Poisson features.

    Returns:
        ProcessConfig: Config with Poisson blending enabled.
    """
    return ProcessConfig(
        video_path="/tmp/video.mp4",
        mask_path="/tmp/mask.png",
        output_dir="/tmp/output",
        use_poisson_blending=True,
        poisson_max_iterations=100,
        poisson_tolerance=0.01,
    )


@pytest.fixture
def phase2_checkpoint_process_config():
    """Create ProcessConfig with Phase 2 checkpoint feature.

    Returns:
        ProcessConfig: Config with checkpointing enabled.
    """
    return ProcessConfig(
        video_path="/tmp/video.mp4",
        mask_path="/tmp/mask.png",
        output_dir="/tmp/output",
        use_checkpoints=True,
    )


@pytest.fixture
def phase2_full_process_config():
    """Create ProcessConfig with all Phase 2 features enabled.

    Returns:
        ProcessConfig: Full Phase 2 configuration.
    """
    return ProcessConfig(
        video_path="/tmp/video.mp4",
        mask_path="/tmp/mask.png",
        output_dir="/tmp/output",
        temporal_smooth_enabled=True,
        temporal_smooth_alpha=0.4,
        use_adaptive_temporal_smoothing=True,
        adaptive_motion_threshold=0.08,
        use_poisson_blending=True,
        poisson_max_iterations=200,
        poisson_tolerance=0.001,
        use_watermark_tracker=True,
        yolo_model_path="/path/to/yolov8n.pt",
        yolo_confidence_threshold=0.55,
        tracker_smoothing_factor=0.4,
        use_checkpoints=True,
    )
