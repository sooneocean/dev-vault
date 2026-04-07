"""Tests for QualityMonitor integration with the pipeline."""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import cv2
import numpy as np
import pytest

from watermark_removal.core.types import CropRegion, ProcessConfig
from watermark_removal.core.pipeline import Pipeline
from watermark_removal.metrics.quality_monitor import QualityMonitor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_test_image(path: str, width: int = 640, height: int = 480) -> None:
    """Write a simple gradient PNG to *path*."""
    image = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        image[y, :] = [y % 256, (y // 2) % 256, (y // 3) % 256]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(path, image)


def _make_process_config(tmpdir: str, **overrides) -> ProcessConfig:
    """Create a ProcessConfig pointing at temp files inside *tmpdir*."""
    video_path = str(Path(tmpdir) / "input.mp4")
    mask_path = str(Path(tmpdir) / "mask.png")
    output_dir = str(Path(tmpdir) / "output")

    # Create minimal mask image
    _create_test_image(mask_path, width=640, height=480)

    # Create minimal MP4 (2 frames)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(video_path, fourcc, 30.0, (640, 480))
    for i in range(2):
        frame = np.full((480, 640, 3), i * 80, dtype=np.uint8)
        out.write(frame)
    out.release()

    defaults = dict(
        video_path=video_path,
        mask_path=mask_path,
        output_dir=output_dir,
    )
    defaults.update(overrides)
    return ProcessConfig(**defaults)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_dir():
    """Yield a fresh temporary directory."""
    with tempfile.TemporaryDirectory() as d:
        yield d


# ---------------------------------------------------------------------------
# Tests — _compute_quality_metrics directly
# ---------------------------------------------------------------------------

class TestComputeQualityMetricsEnabled:
    """quality_metrics_enabled=True should produce quality_report/ files."""

    @pytest.mark.asyncio
    async def test_produces_report_files(self, temp_dir):
        """When enabled, quality_report/metrics.csv and summary.json exist."""
        config = _make_process_config(temp_dir, quality_metrics_enabled=True)
        pipeline = Pipeline(config)

        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create fake original frames
        frames_dir = output_dir / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        original_frames = []
        for i in range(3):
            fp = frames_dir / f"frame_{i:06d}.png"
            _create_test_image(str(fp))
            original_frames.append(fp)

        # Create fake stitched frames
        stitched_dir = output_dir / "stitched"
        stitched_dir.mkdir(parents=True, exist_ok=True)
        stitched_frames = []
        for i in range(3):
            fp = stitched_dir / f"frame_{i:06d}.png"
            _create_test_image(str(fp))
            stitched_frames.append(fp)

        # Create fake inpainted crops
        inpainted_dir = output_dir / "inpainted"
        inpainted_dir.mkdir(parents=True, exist_ok=True)
        inpainted = {}
        for i in range(3):
            fp = inpainted_dir / f"inpainted_{i:06d}.png"
            _create_test_image(str(fp), width=200, height=200)
            inpainted[i] = fp

        # Populate crop_regions so region_bbox can be derived
        for i in range(3):
            pipeline.crop_regions[i] = CropRegion(
                x=100, y=100, w=200, h=200, scale_factor=2.0,
                context_x=50, context_y=50, context_w=300, context_h=300,
            )

        result = await pipeline._compute_quality_metrics(
            original_frames, stitched_frames, inpainted,
        )

        # Assertions: files created
        report_dir = output_dir / "quality_report"
        assert (report_dir / "metrics.csv").exists()
        assert (report_dir / "summary.json").exists()

        # Assertions: return value
        assert result is not None
        assert "frame_count" in result
        assert result["frame_count"] == 3

    @pytest.mark.asyncio
    async def test_return_dict_has_expected_keys(self, temp_dir):
        """Summary dict contains boundary_smoothness, color_consistency, etc."""
        config = _make_process_config(temp_dir, quality_metrics_enabled=True)
        pipeline = Pipeline(config)

        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        frames = []
        stitched = []
        for i in range(2):
            fp_orig = output_dir / f"orig_{i}.png"
            fp_stitch = output_dir / f"stitch_{i}.png"
            _create_test_image(str(fp_orig))
            _create_test_image(str(fp_stitch))
            frames.append(fp_orig)
            stitched.append(fp_stitch)

        result = await pipeline._compute_quality_metrics(frames, stitched, {})

        assert result is not None
        assert "boundary_smoothness" in result
        assert "color_consistency" in result
        assert "inpaint_quality" in result


class TestComputeQualityMetricsDisabled:
    """quality_metrics_enabled=False should skip everything."""

    @pytest.mark.asyncio
    async def test_skips_when_disabled(self, temp_dir):
        """No quality_report/ directory, return value is None."""
        config = _make_process_config(temp_dir, quality_metrics_enabled=False)
        pipeline = Pipeline(config)

        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        result = await pipeline._compute_quality_metrics([], [], {})

        assert result is None
        assert not (output_dir / "quality_report").exists()


class TestQualityMetricsFailureResilience:
    """QualityMonitor failures must never crash the pipeline."""

    @pytest.mark.asyncio
    async def test_monitor_exception_returns_none(self, temp_dir):
        """If QualityMonitor raises, _compute_quality_metrics returns None."""
        config = _make_process_config(temp_dir, quality_metrics_enabled=True)
        pipeline = Pipeline(config)

        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Patch QualityMonitor to explode on instantiation
        with patch(
            "watermark_removal.core.pipeline.QualityMonitor",
            side_effect=RuntimeError("boom"),
        ):
            result = await pipeline._compute_quality_metrics([], [], {})

        assert result is None

    @pytest.mark.asyncio
    async def test_per_frame_error_continues(self, temp_dir):
        """A single bad frame should not abort the rest of the metrics."""
        config = _make_process_config(temp_dir, quality_metrics_enabled=True)
        pipeline = Pipeline(config)

        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create 3 stitched frames — make the middle one unreadable
        stitched = []
        for i in range(3):
            fp = output_dir / f"stitch_{i}.png"
            if i == 1:
                # Write garbage so cv2.imread returns None
                fp.write_text("not an image")
            else:
                _create_test_image(str(fp))
            stitched.append(fp)

        originals = []
        for i in range(3):
            fp = output_dir / f"orig_{i}.png"
            _create_test_image(str(fp))
            originals.append(fp)

        result = await pipeline._compute_quality_metrics(originals, stitched, {})

        # Should still succeed — two good frames processed
        assert result is not None
        assert result["frame_count"] == 2


class TestPipelineReturnDictIncludesQualityMetrics:
    """Pipeline.run() summary must include a quality_metrics key."""

    @pytest.mark.asyncio
    async def test_summary_has_quality_metrics_key(self, temp_dir):
        """Verify the run() return dict contains quality_metrics."""
        config = _make_process_config(temp_dir, quality_metrics_enabled=True)
        pipeline = Pipeline(config)

        # Stub every heavy phase so we only exercise the wiring
        fake_frames = [Path(temp_dir) / "frame_0.png"]
        _create_test_image(str(fake_frames[0]))

        fake_stitched = [Path(temp_dir) / "stitch_0.png"]
        _create_test_image(str(fake_stitched[0]))

        fake_inpainted = {0: Path(temp_dir) / "inpaint_0.png"}
        _create_test_image(str(fake_inpainted[0]))

        fake_output = Path(temp_dir) / "output.mp4"
        fake_output.write_bytes(b"\x00")

        pipeline._extract_frames = AsyncMock(return_value=fake_frames)
        pipeline._preprocess_crops = AsyncMock(return_value={0: fake_frames[0]})
        pipeline._comfyui_preflight = AsyncMock()
        pipeline._inpaint_crops = AsyncMock(return_value=fake_inpainted)
        pipeline._apply_temporal_smoothing = AsyncMock(return_value=fake_inpainted)
        pipeline._compute_optical_flow = AsyncMock()
        pipeline._stitch_frames = AsyncMock(return_value=fake_stitched)
        pipeline._encode_video = AsyncMock(return_value=fake_output)
        pipeline._cleanup = AsyncMock()

        summary = await pipeline.run()

        assert "quality_metrics" in summary

    @pytest.mark.asyncio
    async def test_summary_quality_metrics_none_when_disabled(self, temp_dir):
        """quality_metrics is None when the feature is off."""
        config = _make_process_config(temp_dir, quality_metrics_enabled=False)
        pipeline = Pipeline(config)

        fake_output = Path(temp_dir) / "output.mp4"
        fake_output.write_bytes(b"\x00")

        pipeline._extract_frames = AsyncMock(return_value=[])
        pipeline._preprocess_crops = AsyncMock(return_value={})
        pipeline._comfyui_preflight = AsyncMock()
        pipeline._inpaint_crops = AsyncMock(return_value={})
        pipeline._apply_temporal_smoothing = AsyncMock(return_value={})
        pipeline._compute_optical_flow = AsyncMock()
        pipeline._stitch_frames = AsyncMock(return_value=[])
        pipeline._encode_video = AsyncMock(return_value=fake_output)
        pipeline._cleanup = AsyncMock()

        summary = await pipeline.run()

        assert summary["quality_metrics"] is None


class TestProcessConfigQualityMetricsField:
    """Verify the quality_metrics_enabled field on ProcessConfig."""

    def test_default_is_true(self, temp_dir):
        """quality_metrics_enabled defaults to True."""
        config = _make_process_config(temp_dir)
        assert config.quality_metrics_enabled is True

    def test_can_disable(self, temp_dir):
        """Explicitly setting False works."""
        config = _make_process_config(temp_dir, quality_metrics_enabled=False)
        assert config.quality_metrics_enabled is False
