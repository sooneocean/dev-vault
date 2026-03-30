"""Tests for async inpaint executor."""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import cv2
import numpy as np
import pytest

from src.watermark_removal.core.types import InpaintConfig
from src.watermark_removal.inpaint.inpaint_executor import InpaintExecutor


def create_dummy_image(path: str, width: int = 1024, height: int = 1024) -> None:
    """Create a dummy PNG image for testing."""
    image = np.zeros((height, width, 3), dtype=np.uint8)
    image[:, :] = [100, 150, 200]  # BGR color
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(path, image)


@pytest.fixture
def default_inpaint_config() -> InpaintConfig:
    """Create default inpaint config."""
    return InpaintConfig(
        model_name="flux-dev.safetensors",
        prompt="remove watermark",
        negative_prompt="artifacts",
        steps=20,
        cfg_scale=7.5,
        seed=42,
    )


@pytest.fixture
def inpaint_executor() -> InpaintExecutor:
    """Create inpaint executor instance."""
    return InpaintExecutor(host="127.0.0.1", port=8188)


class TestInpaintExecutorHappyPath:
    """Happy path tests."""

    @pytest.mark.asyncio
    async def test_inpaint_executor_inpaint_single_happy_path(
        self, inpaint_executor, default_inpaint_config
    ):
        """Test submitting a single crop for inpaint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create dummy image and mask
            image_path = f"{tmpdir}/crop.png"
            mask_path = f"{tmpdir}/mask.png"
            output_dir = f"{tmpdir}/output"

            create_dummy_image(image_path)
            create_dummy_image(mask_path)

            # Mock ComfyUIClient
            mock_client = AsyncMock()
            mock_client.submit_prompt = AsyncMock(return_value="prompt_123")
            mock_client.listen_execution = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            # Create expected output file
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            output_file = Path(output_dir) / "crop_0001.png"
            create_dummy_image(str(output_file))

            with patch(
                "projects.tools.comfyui.client.ComfyUIClient",
                return_value=mock_client,
            ):
                result = await inpaint_executor.inpaint_single(
                    image_path=image_path,
                    mask_path=mask_path,
                    config=default_inpaint_config,
                    output_dir=output_dir,
                )

            assert result == output_file
            assert result.exists()
            mock_client.submit_prompt.assert_called_once()
            mock_client.listen_execution.assert_called_once()

    @pytest.mark.asyncio
    async def test_inpaint_executor_inpaint_batch_happy_path(
        self, inpaint_executor, default_inpaint_config
    ):
        """Test submitting multiple crops for inpaint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create dummy images and masks
            pairs = []
            for i in range(3):
                image_path = f"{tmpdir}/crop_{i}.png"
                mask_path = f"{tmpdir}/mask_{i}.png"
                create_dummy_image(image_path)
                create_dummy_image(mask_path)
                pairs.append((image_path, mask_path))

            output_dir = f"{tmpdir}/output"
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            # Mock ComfyUIClient
            mock_client = AsyncMock()
            mock_client.submit_prompt = AsyncMock(side_effect=["prompt_1", "prompt_2", "prompt_3"])
            mock_client.listen_execution = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            # Create expected output files
            for i in range(3):
                output_file = Path(output_dir) / f"crop_{i}_0001.png"
                create_dummy_image(str(output_file))

            with patch(
                "projects.tools.comfyui.client.ComfyUIClient",
                return_value=mock_client,
            ):
                results = await inpaint_executor.inpaint_batch(
                    image_mask_pairs=pairs,
                    config=default_inpaint_config,
                    output_dir=output_dir,
                )

            assert len(results) == 3
            assert all(r.exists() for r in results)


class TestInpaintExecutorEdgeCases:
    """Edge case tests."""

    @pytest.mark.asyncio
    async def test_inpaint_executor_empty_batch(self, inpaint_executor, default_inpaint_config):
        """Test submitting empty batch."""
        results = await inpaint_executor.inpaint_batch(
            image_mask_pairs=[],
            config=default_inpaint_config,
            output_dir="/tmp/output",
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_inpaint_executor_batch_with_batch_size(
        self, inpaint_executor, default_inpaint_config
    ):
        """Test batch submission with batch size limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create 5 pairs
            pairs = []
            for i in range(5):
                image_path = f"{tmpdir}/crop_{i}.png"
                mask_path = f"{tmpdir}/mask_{i}.png"
                create_dummy_image(image_path)
                create_dummy_image(mask_path)
                pairs.append((image_path, mask_path))

            output_dir = f"{tmpdir}/output"
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            # Mock ComfyUIClient
            mock_client = AsyncMock()
            call_count = [0]

            async def mock_submit(*args, **kwargs):
                call_count[0] += 1
                return f"prompt_{call_count[0]}"

            mock_client.submit_prompt = AsyncMock(side_effect=mock_submit)
            mock_client.listen_execution = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            # Create output files
            for i in range(5):
                output_file = Path(output_dir) / f"crop_{i}_0001.png"
                create_dummy_image(str(output_file))

            with patch(
                "projects.tools.comfyui.client.ComfyUIClient",
                return_value=mock_client,
            ):
                results = await inpaint_executor.inpaint_batch(
                    image_mask_pairs=pairs,
                    config=default_inpaint_config,
                    output_dir=output_dir,
                    batch_size=2,  # Process 2 at a time
                )

            assert len(results) == 5
            # submit_prompt should have been called 5 times total
            assert call_count[0] == 5


class TestInpaintExecutorErrors:
    """Error handling tests."""

    @pytest.mark.asyncio
    async def test_inpaint_executor_missing_image_file(
        self, inpaint_executor, default_inpaint_config
    ):
        """Test error when image file does not exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mask_path = f"{tmpdir}/mask.png"
            create_dummy_image(mask_path)

            with pytest.raises(FileNotFoundError, match="Image file not found"):
                await inpaint_executor.inpaint_single(
                    image_path="/nonexistent/image.png",
                    mask_path=mask_path,
                    config=default_inpaint_config,
                    output_dir=f"{tmpdir}/output",
                )

    @pytest.mark.asyncio
    async def test_inpaint_executor_missing_mask_file(
        self, inpaint_executor, default_inpaint_config
    ):
        """Test error when mask file does not exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = f"{tmpdir}/image.png"
            create_dummy_image(image_path)

            with pytest.raises(FileNotFoundError, match="Mask file not found"):
                await inpaint_executor.inpaint_single(
                    image_path=image_path,
                    mask_path="/nonexistent/mask.png",
                    config=default_inpaint_config,
                    output_dir=f"{tmpdir}/output",
                )

    @pytest.mark.asyncio
    async def test_inpaint_executor_comfyui_timeout(
        self, inpaint_executor, default_inpaint_config
    ):
        """Test error when ComfyUI execution times out."""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = f"{tmpdir}/image.png"
            mask_path = f"{tmpdir}/mask.png"
            create_dummy_image(image_path)
            create_dummy_image(mask_path)
            output_dir = f"{tmpdir}/output"

            # Mock ComfyUIClient that times out
            mock_client = AsyncMock()
            mock_client.submit_prompt = AsyncMock(return_value="prompt_123")
            mock_client.listen_execution = AsyncMock(
                side_effect=asyncio.TimeoutError("Execution timeout")
            )
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            with patch(
                "projects.tools.comfyui.client.ComfyUIClient",
                return_value=mock_client,
            ):
                with pytest.raises(TimeoutError, match="timeout"):
                    await inpaint_executor.inpaint_single(
                        image_path=image_path,
                        mask_path=mask_path,
                        config=default_inpaint_config,
                        output_dir=output_dir,
                    )

    @pytest.mark.asyncio
    async def test_inpaint_executor_no_output_file(
        self, inpaint_executor, default_inpaint_config
    ):
        """Test error when ComfyUI doesn't produce output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = f"{tmpdir}/image.png"
            mask_path = f"{tmpdir}/mask.png"
            create_dummy_image(image_path)
            create_dummy_image(mask_path)
            output_dir = f"{tmpdir}/output"

            # Mock ComfyUIClient that succeeds but produces no output
            mock_client = AsyncMock()
            mock_client.submit_prompt = AsyncMock(return_value="prompt_123")
            mock_client.listen_execution = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            # Create output directory but no output file
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            with patch(
                "projects.tools.comfyui.client.ComfyUIClient",
                return_value=mock_client,
            ):
                with pytest.raises(RuntimeError, match="No output file found"):
                    await inpaint_executor.inpaint_single(
                        image_path=image_path,
                        mask_path=mask_path,
                        config=default_inpaint_config,
                        output_dir=output_dir,
                    )

    @pytest.mark.asyncio
    async def test_inpaint_executor_comfyui_connection_error(
        self, inpaint_executor, default_inpaint_config
    ):
        """Test error when ComfyUI connection fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = f"{tmpdir}/image.png"
            mask_path = f"{tmpdir}/mask.png"
            create_dummy_image(image_path)
            create_dummy_image(mask_path)
            output_dir = f"{tmpdir}/output"

            # Mock ComfyUIClient that fails to connect
            mock_client = AsyncMock()
            mock_client.submit_prompt = AsyncMock(
                side_effect=RuntimeError("Connection refused")
            )
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)

            with patch(
                "projects.tools.comfyui.client.ComfyUIClient",
                return_value=mock_client,
            ):
                with pytest.raises(RuntimeError, match="failed"):
                    await inpaint_executor.inpaint_single(
                        image_path=image_path,
                        mask_path=mask_path,
                        config=default_inpaint_config,
                        output_dir=output_dir,
                    )


class TestInpaintExecutorIntegration:
    """Integration tests."""

    @pytest.mark.asyncio
    async def test_inpaint_executor_initialization(self, inpaint_executor):
        """Test executor initialization."""
        assert inpaint_executor.host == "127.0.0.1"
        assert inpaint_executor.port == 8188
        assert inpaint_executor.workflow_builder is not None

    @pytest.mark.asyncio
    async def test_inpaint_executor_custom_host_port(self):
        """Test executor with custom host/port."""
        executor = InpaintExecutor(host="192.168.1.100", port=9000)
        assert executor.host == "192.168.1.100"
        assert executor.port == 9000
