"""
Tests for watermark_removal CLI entry point.

Tests command-line argument parsing, config loading, and pipeline execution.
"""

import pytest
import tempfile
from pathlib import Path
import sys
from unittest.mock import patch

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from run_pipeline import parse_arguments, load_config


class TestCLIParsing:
    """Test command-line argument parsing."""

    def test_parse_with_config_only(self):
        """Parse arguments with config file only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text("test")

            test_args = ["--config", str(config_path)]
            with patch.object(sys, "argv", ["run_pipeline.py"] + test_args):
                args = parse_arguments()
                assert args.config == config_path
                assert args.video is None
                assert args.mask is None

    def test_parse_with_video_and_mask(self):
        """Parse arguments with video and mask files."""
        test_args = [
            "--video", "input.mp4",
            "--mask", "mask.png",
            "--output", "output",
        ]
        with patch.object(sys, "argv", ["run_pipeline.py"] + test_args):
            args = parse_arguments()
            assert args.video == Path("input.mp4")
            assert args.mask == Path("mask.png")
            assert args.output == Path("output")

    def test_parse_with_processing_parameters(self):
        """Parse arguments with processing parameters."""
        test_args = [
            "--video", "input.mp4",
            "--mask", "mask.png",
            "--context-padding", "128",
            "--target-inpaint-size", "512",
            "--blend-feather-width", "64",
            "--batch-size", "8",
            "--inpaint-timeout", "600",
        ]
        with patch.object(sys, "argv", ["run_pipeline.py"] + test_args):
            args = parse_arguments()
            assert args.context_padding == 128
            assert args.target_inpaint_size == 512
            assert args.blend_feather_width == 64
            assert args.batch_size == 8
            assert args.inpaint_timeout == 600.0

    def test_parse_with_comfyui_parameters(self):
        """Parse arguments with ComfyUI parameters."""
        test_args = [
            "--video", "input.mp4",
            "--mask", "mask.png",
            "--comfyui-host", "192.168.1.100",
            "--comfyui-port", "9000",
        ]
        with patch.object(sys, "argv", ["run_pipeline.py"] + test_args):
            args = parse_arguments()
            assert args.comfyui_host == "192.168.1.100"
            assert args.comfyui_port == 9000

    def test_parse_with_flags(self):
        """Parse arguments with boolean flags."""
        test_args = [
            "--video", "input.mp4",
            "--mask", "mask.png",
            "--keep-intermediate",
            "--verbose",
        ]
        with patch.object(sys, "argv", ["run_pipeline.py"] + test_args):
            args = parse_arguments()
            assert args.keep_intermediate is True
            assert args.verbose is True

    def test_parse_defaults(self):
        """Parse arguments and check defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "input.mp4"
            mask_path = Path(tmpdir) / "mask.png"
            video_path.write_text("test")
            mask_path.write_text("test")

            test_args = ["--video", str(video_path), "--mask", str(mask_path)]
            with patch.object(sys, "argv", ["run_pipeline.py"] + test_args):
                args = parse_arguments()
                assert args.context_padding is None
                assert args.target_inpaint_size is None
                assert args.batch_size is None
                assert args.keep_intermediate is False
                assert args.verbose is False

    def test_parse_with_phase2_parameters(self):
        """Parse arguments with Phase 2 parameters."""
        test_args = [
            "--video", "input.mp4",
            "--mask", "mask.png",
            "--use-yolo-detection",
            "--yolo-model-size", "small",
            "--yolo-confidence-threshold", "0.5",
            "--temporal-smooth-alpha", "0.3",
            "--use-adaptive-temporal-smoothing",
            "--adaptive-motion-threshold", "0.05",
            "--use-poisson-blending",
            "--poisson-max-iterations", "50",
            "--use-watermark-tracker",
            "--use-checkpoints",
            "--resume-from-checkpoint",
        ]
        with patch.object(sys, "argv", ["run_pipeline.py"] + test_args):
            args = parse_arguments()
            assert args.use_yolo_detection is True
            assert args.yolo_model_size == "small"
            assert args.yolo_confidence_threshold == 0.5
            assert args.temporal_smooth_alpha == 0.3
            assert args.use_adaptive_temporal_smoothing is True
            assert args.adaptive_motion_threshold == 0.05
            assert args.use_poisson_blending is True
            assert args.poisson_max_iterations == 50
            assert args.use_watermark_tracker is True
            assert args.use_checkpoints is True
            assert args.resume_from_checkpoint is True


class TestConfigLoading:
    """Test configuration loading from files and arguments."""

    def test_load_from_command_line_args(self):
        """Load config from command-line arguments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            video_path = tmpdir / "input.mp4"
            mask_path = tmpdir / "mask.png"
            video_path.write_text("test")
            mask_path.write_text("test")

            class Args:
                config = None
                video = video_path
                mask = mask_path
                output = tmpdir / "output"
                context_padding = None
                target_inpaint_size = None
                blend_feather_width = None
                batch_size = None
                inpaint_timeout = None
                comfyui_host = None
                comfyui_port = None
                keep_intermediate = False

            config = load_config(Args())
            assert config.video_path == video_path
            assert config.mask_path == mask_path

    def test_load_missing_video_file(self):
        """Load config with missing video file raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            mask_path = tmpdir / "mask.png"
            mask_path.write_text("test")

            class Args:
                config = None
                video = tmpdir / "nonexistent.mp4"
                mask = mask_path
                output = tmpdir / "output"
                context_padding = None
                target_inpaint_size = None
                blend_feather_width = None
                batch_size = None
                inpaint_timeout = None
                comfyui_host = None
                comfyui_port = None
                keep_intermediate = False

            with pytest.raises(FileNotFoundError):
                load_config(Args())

    def test_load_missing_mask_file(self):
        """Load config with missing mask file raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            video_path = tmpdir / "input.mp4"
            video_path.write_text("test")

            class Args:
                config = None
                video = video_path
                mask = tmpdir / "nonexistent.png"
                output = tmpdir / "output"
                context_padding = None
                target_inpaint_size = None
                blend_feather_width = None
                batch_size = None
                inpaint_timeout = None
                comfyui_host = None
                comfyui_port = None
                keep_intermediate = False

            with pytest.raises(FileNotFoundError):
                load_config(Args())

    def test_load_missing_config_and_inputs(self):
        """Load config with no config file and missing inputs raises error."""
        class Args:
            config = None
            video = None
            mask = None
            output = None
            context_padding = None
            target_inpaint_size = None
            blend_feather_width = None
            batch_size = None
            inpaint_timeout = None
            comfyui_host = None
            comfyui_port = None
            keep_intermediate = False

        with pytest.raises(ValueError):
            load_config(Args())

    def test_load_with_parameter_overrides(self):
        """Load config and override with command-line parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            video_path = tmpdir / "input.mp4"
            mask_path = tmpdir / "mask.png"
            video_path.write_text("test")
            mask_path.write_text("test")

            class Args:
                config = None
                video = video_path
                mask = mask_path
                output = tmpdir / "output"
                context_padding = 128
                target_inpaint_size = 512
                blend_feather_width = 64
                batch_size = 8
                inpaint_timeout = 600.0
                comfyui_host = "192.168.1.100"
                comfyui_port = 9000
                keep_intermediate = True

            config = load_config(Args())
            assert config.context_padding == 128
            assert config.target_inpaint_size == 512
            assert config.blend_feather_width == 64
            assert config.batch_size == 8
            assert config.inpaint_timeout_sec == 600.0
            assert config.comfyui_host == "192.168.1.100"
            assert config.comfyui_port == 9000
            assert config.keep_intermediate is True

    def test_load_with_phase2_overrides(self):
        """Load config and override with Phase 2 parameters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            video_path = tmpdir / "input.mp4"
            mask_path = tmpdir / "mask.png"
            video_path.write_text("test")
            mask_path.write_text("test")

            class Args:
                config = None
                video = video_path
                mask = mask_path
                output = tmpdir / "output"
                context_padding = None
                target_inpaint_size = None
                blend_feather_width = None
                batch_size = None
                inpaint_timeout = None
                comfyui_host = None
                comfyui_port = None
                keep_intermediate = False
                use_yolo_detection = True
                yolo_model_size = "small"
                yolo_confidence_threshold = 0.5
                temporal_smooth_alpha = 0.3
                use_adaptive_temporal_smoothing = True
                adaptive_motion_threshold = 0.05
                use_poisson_blending = True
                poisson_max_iterations = 50
                use_watermark_tracker = True
                yolo_model_path = None
                use_checkpoints = True
                resume_from_checkpoint = True

            config = load_config(Args())
            assert config.use_yolo_detection is True
            assert config.yolo_model_size == "small"
            assert config.yolo_confidence_threshold == 0.5
            assert config.temporal_smooth_alpha == 0.3
            assert config.use_adaptive_temporal_smoothing is True
            assert config.adaptive_motion_threshold == 0.05
            assert config.use_poisson_blending is True
            assert config.poisson_max_iterations == 50
            assert config.use_watermark_tracker is True
            assert config.use_checkpoints is True
            assert config.resume_from_checkpoint is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
