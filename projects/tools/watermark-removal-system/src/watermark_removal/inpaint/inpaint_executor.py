"""
Async inpaint execution via ComfyUI.

Manages batch processing and result collection.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from ..core.types import InpaintConfig


logger = logging.getLogger(__name__)


class InpaintExecutor:
    """Executes inpaint jobs on ComfyUI."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8188):
        """
        Initialize executor.

        Args:
            host: ComfyUI server host
            port: ComfyUI server port
        """
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"

    async def inpaint_single(
        self,
        image_path: str | Path,
        mask_path: str | Path,
        config: InpaintConfig,
        output_path: str | Path,
    ) -> Optional[Path]:
        """
        Inpaint single crop (async).

        Args:
            image_path: Crop image path
            mask_path: Inpaint mask path
            config: Inpaint configuration
            output_path: Where to save result

        Returns:
            Path to inpainted image if successful, None otherwise
        """
        # In real implementation, submit workflow to ComfyUI /prompt API
        logger.info(f"Inpainting {image_path} -> {output_path}")

        # For now, simulate async work
        await asyncio.sleep(0.1)

        return Path(output_path)

    async def inpaint_batch(
        self,
        image_mask_pairs: list[tuple[str | Path, str | Path]],
        config: InpaintConfig,
        output_dir: str | Path,
    ) -> list[Path]:
        """
        Inpaint multiple crops in parallel.

        Args:
            image_mask_pairs: List of (image_path, mask_path) tuples
            config: Inpaint configuration
            output_dir: Output directory for results

        Returns:
            List of result paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        tasks = []
        for i, (image_path, mask_path) in enumerate(image_mask_pairs):
            output_path = output_dir / f"inpainted_{i:06d}.png"
            task = self.inpaint_single(image_path, mask_path, config, output_path)
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]
