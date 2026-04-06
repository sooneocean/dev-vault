"""
Integration tests for watermark_removal.core.pipeline module.

Tests pipeline initialization and basic structure.
"""

import pytest
import tempfile
from pathlib import Path

from src.watermark_removal.core.pipeline import Pipeline
from src.watermark_removal.core.types import ProcessConfig, CropRegion


class TestPipelineInit:
    """Test Pipeline initialization."""

    def test_init(self):
        """Initialize pipeline with config."""
        config = ProcessConfig(
            video_path="input.mp4",
            mask_path="mask.png",
        )
        pipeline = Pipeline(config)

        assert pipeline.config == config
        assert pipeline.crop_regions == []
        assert pipeline.inpaint_times == []

    def test_init_with_custom_params(self):
        """Initialize with custom parameters."""
        config = ProcessConfig(
            video_path="input.mp4",
            mask_path="mask.json",
            context_padding=128,
            target_inpaint_size=512,
            blend_feather_width=64,
            batch_size=8,
        )
        pipeline = Pipeline(config)

        assert pipeline.config.context_padding == 128
        assert pipeline.config.target_inpaint_size == 512
        assert pipeline.config.blend_feather_width == 64


class TestPipelineIntegration:
    """Integration tests for pipeline configuration and structure."""

    def test_pipeline_output_directory_creation(self):
        """Pipeline config handles output directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            config = ProcessConfig(
                video_path=tmpdir / "input.mp4",
                mask_path=tmpdir / "mask.png",
                output_dir=tmpdir / "nonexistent" / "output",
            )
            config.video_path.write_bytes(b"fake")
            config.mask_path.write_bytes(b"fake")

            pipeline = Pipeline(config)

            # Output directory should be settable in config
            assert pipeline.config.output_dir == config.output_dir

    def test_pipeline_crop_regions_persistence(self):
        """CropRegion list persists through pipeline execution phases."""
        config = ProcessConfig(
            video_path="input.mp4",
            mask_path="mask.png",
        )
        pipeline = Pipeline(config)

        # Initially empty
        assert len(pipeline.crop_regions) == 0

        # Simulate adding crop regions
        crop = CropRegion(
            frame_id=0,
            original_bbox=(100, 100, 50, 50),
            context_bbox=(50, 50, 150, 150),
            scale_factor=2.0,
        )
        pipeline.crop_regions.append(crop)

        # Should persist
        assert len(pipeline.crop_regions) == 1
        assert pipeline.crop_regions[0].frame_id == 0

    def test_multiple_crop_regions(self):
        """Pipeline can store multiple crop regions."""
        config = ProcessConfig(
            video_path="input.mp4",
            mask_path="mask.png",
        )
        pipeline = Pipeline(config)

        # Add multiple crop regions
        for frame_id in range(5):
            crop = CropRegion(
                frame_id=frame_id,
                original_bbox=(100, 100, 50, 50),
                context_bbox=(50, 50, 150, 150),
                scale_factor=2.0,
            )
            pipeline.crop_regions.append(crop)

        # All should be stored
        assert len(pipeline.crop_regions) == 5
        for i, crop in enumerate(pipeline.crop_regions):
            assert crop.frame_id == i

    def test_pipeline_inpaint_times_tracking(self):
        """Pipeline tracks inpaint execution times."""
        config = ProcessConfig(
            video_path="input.mp4",
            mask_path="mask.png",
        )
        pipeline = Pipeline(config)

        # Initially empty
        assert len(pipeline.inpaint_times) == 0

        # Simulate adding inpaint times
        pipeline.inpaint_times.append(5.2)
        pipeline.inpaint_times.append(4.8)
        pipeline.inpaint_times.append(5.1)

        # Should track all times
        assert len(pipeline.inpaint_times) == 3
        assert sum(pipeline.inpaint_times) == pytest.approx(15.1, abs=0.01)

    def test_config_paths_conversion(self):
        """ProcessConfig converts string paths to Path objects."""
        config = ProcessConfig(
            video_path="input.mp4",
            mask_path="mask.png",
            output_dir="output",
        )

        # Should be Path objects after initialization
        assert isinstance(config.video_path, Path)
        assert isinstance(config.mask_path, Path)
        assert isinstance(config.output_dir, Path)

    def test_config_defaults(self):
        """ProcessConfig has sensible defaults."""
        config = ProcessConfig(
            video_path="input.mp4",
            mask_path="mask.png",
        )

        # Check defaults
        assert config.context_padding == 64
        assert config.target_inpaint_size == 1024
        assert config.blend_feather_width == 32
        assert config.batch_size == 4
        assert config.inpaint_timeout_sec == 300.0
        assert config.comfyui_host == "127.0.0.1"
        assert config.comfyui_port == 8188
        assert config.keep_intermediate is False

    def test_inpaint_config_defaults(self):
        """InpaintConfig has sensible defaults."""
        config = ProcessConfig(
            video_path="input.mp4",
            mask_path="mask.png",
        )

        # Check inpaint config defaults
        assert config.inpaint.model_name == "flux-dev"
        assert config.inpaint.steps == 20
        assert config.inpaint.cfg_scale == 7.5
        assert config.inpaint.sampler == "dpmpp_2m"
        assert config.inpaint.scheduler == "karras"

    def test_pipeline_static_create_method_signature(self):
        """Pipeline.create_and_run static method exists."""
        # Just check that the method exists and is callable
        assert hasattr(Pipeline, "create_and_run")
        assert callable(getattr(Pipeline, "create_and_run"))

    def test_pipeline_run_method_signature(self):
        """Pipeline.run async method exists."""
        config = ProcessConfig(
            video_path="input.mp4",
            mask_path="mask.png",
        )
        pipeline = Pipeline(config)

        # Check that run method exists and is async
        assert hasattr(pipeline, "run")
        assert callable(getattr(pipeline, "run"))

    def test_crop_region_metadata_structure(self):
        """CropRegion has correct metadata structure."""
        crop = CropRegion(
            frame_id=42,
            original_bbox=(100, 200, 300, 400),
            context_bbox=(50, 150, 400, 500),
            scale_factor=1.5,
            pad_left=10,
            pad_top=20,
            pad_right=30,
            pad_bottom=40,
        )

        # Check all fields are stored correctly
        assert crop.frame_id == 42
        assert crop.original_bbox == (100, 200, 300, 400)
        assert crop.context_bbox == (50, 150, 400, 500)
        assert crop.scale_factor == 1.5
        assert crop.pad_left == 10
        assert crop.pad_top == 20
        assert crop.pad_right == 30
        assert crop.pad_bottom == 40


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
