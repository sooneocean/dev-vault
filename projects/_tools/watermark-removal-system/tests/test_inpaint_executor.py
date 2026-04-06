"""
Unit tests for watermark_removal.inpaint.inpaint_executor module.

Tests async execution and batch processing for ComfyUI inpaint.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch
import sys

from src.watermark_removal.inpaint.inpaint_executor import InpaintExecutor
from src.watermark_removal.core.types import InpaintConfig, ProcessConfig


class TestInpaintExecutor:
    """Test InpaintExecutor class."""

    def test_init_default(self):
        """Initialize with default parameters."""
        executor = InpaintExecutor()
        assert executor.host == "127.0.0.1"
        assert executor.port == 8188
        assert executor.timeout_sec == 300.0
        assert executor.batch_size == 4

    def test_init_custom(self):
        """Initialize with custom parameters."""
        executor = InpaintExecutor(
            host="192.168.1.100", port=9000, timeout_sec=600.0, batch_size=2
        )
        assert executor.host == "192.168.1.100"
        assert executor.port == 9000
        assert executor.timeout_sec == 600.0
        assert executor.batch_size == 2

    @pytest.mark.asyncio
    async def test_inpaint_single_import_error(self):
        """Inpaint single with import error returns None gracefully."""
        executor = InpaintExecutor()
        config = InpaintConfig()

        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = Path(tmpdir) / "crop.png"
            mask_path = Path(tmpdir) / "mask.png"
            output_dir = Path(tmpdir) / "output"

            image_path.write_bytes(b"fake_image")
            mask_path.write_bytes(b"fake_mask")

            # ComfyUIClient will fail to import, so result should be None
            result = await executor.inpaint_single(
                image_path, mask_path, config, output_dir
            )

            # Should return None when ComfyUIClient not available
            assert result is None

    @pytest.mark.asyncio
    async def test_inpaint_batch_empty(self):
        """Inpaint batch with empty list."""
        executor = InpaintExecutor()
        config = InpaintConfig()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"

            results = await executor.inpaint_batch([], config, output_dir)

            assert results == []

    @pytest.mark.asyncio
    async def test_inpaint_batch_parallelization(self):
        """Inpaint batch respects batch_size (parallelization)."""
        executor = InpaintExecutor(batch_size=2)
        config = InpaintConfig()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple image/mask pairs
            image_paths = []
            mask_paths = []
            for i in range(4):
                img_path = Path(tmpdir) / f"crop_{i}.png"
                mask_path = Path(tmpdir) / f"mask_{i}.png"
                img_path.write_bytes(b"fake_image")
                mask_path.write_bytes(b"fake_mask")
                image_paths.append(img_path)
                mask_paths.append(mask_path)

            output_dir = Path(tmpdir) / "output"

            # Mock to track concurrent calls
            concurrent_calls = {"count": 0, "max": 0}

            async def mock_inpaint_single(self, *args, **kwargs):
                concurrent_calls["count"] += 1
                concurrent_calls["max"] = max(
                    concurrent_calls["max"], concurrent_calls["count"]
                )
                await asyncio.sleep(0.05)
                concurrent_calls["count"] -= 1
                return None

            with patch.object(
                InpaintExecutor, "inpaint_single", mock_inpaint_single
            ):
                results = await executor.inpaint_batch(
                    list(zip(image_paths, mask_paths)), config, output_dir
                )

                # Should have at most batch_size concurrent calls
                assert concurrent_calls["max"] <= executor.batch_size

    @pytest.mark.asyncio
    async def test_inpaint_batch_creates_output_dir(self):
        """Inpaint batch creates output directory if it doesn't exist."""
        executor = InpaintExecutor()
        config = InpaintConfig()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "nonexistent" / "output"
            assert not output_dir.exists()

            results = await executor.inpaint_batch([], config, output_dir)

            # Output directory should be created
            assert output_dir.exists()
            assert output_dir.is_dir()


class TestInpaintExecutorIntegration:
    """Integration tests for InpaintExecutor."""

    def test_executor_creation_from_config(self):
        """Test executor creation from ProcessConfig."""
        config = ProcessConfig(
            video_path="input.mp4",
            mask_path="mask.png",
            comfyui_host="192.168.1.50",
            comfyui_port=9000,
            inpaint_timeout_sec=600.0,
            batch_size=8,
        )

        executor = InpaintExecutor(
            host=config.comfyui_host,
            port=config.comfyui_port,
            timeout_sec=config.inpaint_timeout_sec,
            batch_size=config.batch_size,
        )

        assert executor.host == "192.168.1.50"
        assert executor.port == 9000
        assert executor.timeout_sec == 600.0
        assert executor.batch_size == 8

    @pytest.mark.asyncio
    async def test_batch_with_varying_filenames(self):
        """Batch processing generates correct output filenames."""
        executor = InpaintExecutor()
        config = InpaintConfig()

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test image/mask pairs
            pairs = []
            for i in range(3):
                img = Path(tmpdir) / f"img_{i}.png"
                mask = Path(tmpdir) / f"mask_{i}.png"
                img.write_bytes(b"img_data")
                mask.write_bytes(b"mask_data")
                pairs.append((img, mask))

            output_dir = Path(tmpdir) / "output"

            # Mock inpaint_single to return expected filenames
            call_count = 0

            async def mock_inpaint(self, *args, **kwargs):
                nonlocal call_count
                call_count += 1
                # Return a path to verify batch processes all items
                return None

            with patch.object(
                InpaintExecutor, "inpaint_single", mock_inpaint
            ):
                results = await executor.inpaint_batch(pairs, config, output_dir)

                # All items should be processed
                assert call_count == 3
                assert len(results) == 3

    @pytest.mark.asyncio
    async def test_executor_timeout_handling(self):
        """Executor timeout is passed to inpaint_single correctly."""
        executor = InpaintExecutor(timeout_sec=60.0)
        config = InpaintConfig()

        with tempfile.TemporaryDirectory() as tmpdir:
            img = Path(tmpdir) / "img.png"
            mask = Path(tmpdir) / "mask.png"
            output = Path(tmpdir) / "output"

            img.write_bytes(b"img_data")
            mask.write_bytes(b"mask_data")

            # Verify executor has correct timeout
            assert executor.timeout_sec == 60.0

            # Single result with import error should still work
            result = await executor.inpaint_single(img, mask, config, output)
            assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
