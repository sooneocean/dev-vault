"""
Async inpaint execution via ComfyUI.

Manages batch processing and result collection.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional, List, Tuple

from ..core.types import InpaintConfig, ProcessConfig
from .workflow_builder import WorkflowBuilder

logger = logging.getLogger(__name__)


class InpaintExecutor:
    """Executes inpaint jobs on ComfyUI."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8188,
        timeout_sec: float = 300.0,
        batch_size: int = 4,
    ):
        """
        Initialize executor.

        Args:
            host: ComfyUI server host
            port: ComfyUI server port
            timeout_sec: Timeout per inpaint job (seconds)
            batch_size: Max parallel inpaint jobs
        """
        self.host = host
        self.port = port
        self.timeout_sec = timeout_sec
        self.batch_size = batch_size
        logger.info(
            f"InpaintExecutor: {host}:{port}, timeout={timeout_sec}s, batch={batch_size}"
        )

    async def inpaint_single(
        self,
        image_path: str | Path,
        mask_path: str | Path,
        config: InpaintConfig,
        output_dir: str | Path,
        output_filename: str = "inpainted.png",
    ) -> Optional[Path]:
        """
        Inpaint single crop via ComfyUI.

        Args:
            image_path: Crop image path
            mask_path: Inpaint mask path
            config: Inpaint configuration
            output_dir: Directory for output image
            output_filename: Output filename

        Returns:
            Path to inpainted image if successful, None otherwise
        """
        try:
            # Import ComfyUI client
            sys.path.insert(
                0,
                str(
                    Path(__file__).parent.parent.parent.parent.parent
                    / "tools"
                    / "comfyui"
                ),
            )
            try:
                from client import ComfyUIClient
            except ImportError:
                logger.warning("ComfyUIClient not available, returning None")
                return None

            # Build workflow
            workflow = WorkflowBuilder.build(
                image_path, mask_path, config, output_filename
            )

            # Create output directory
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            logger.debug(f"Submitting inpaint: {image_path}")

            # Execute via ComfyUI
            async with ComfyUIClient(self.host, self.port) as client:
                result = await asyncio.wait_for(
                    client.execute_workflow(workflow),
                    timeout=self.timeout_sec,
                )

                # Extract output path from result
                # ComfyUI SaveImage node returns {"9": {"images": [{"filename": "..."}]}}
                if result and isinstance(result, dict):
                    if "9" in result:
                        node_output = result["9"]
                        if isinstance(node_output, dict) and "images" in node_output:
                            images = node_output["images"]
                            if images and isinstance(images, list):
                                img_info = images[0]
                                if isinstance(img_info, dict):
                                    filename = img_info.get("filename")
                                    subfolder = img_info.get("subfolder", "")
                                    if filename:
                                        inpainted_path = (
                                            output_dir / subfolder / filename
                                            if subfolder
                                            else output_dir / filename
                                        )
                                        logger.debug(f"Inpainted: {inpainted_path}")
                                        return inpainted_path

                logger.warning(f"No output found for {image_path}")
                return None

        except asyncio.TimeoutError:
            logger.error(f"Inpaint timeout for {image_path}")
            return None
        except ConnectionError as e:
            logger.error(f"Connection error: {e}")
            return None
        except Exception as e:
            logger.error(f"Inpaint failed for {image_path}: {e}")
            return None

    async def inpaint_batch(
        self,
        image_mask_pairs: List[Tuple[str | Path, str | Path]],
        config: InpaintConfig,
        output_dir: str | Path,
    ) -> List[Optional[Path]]:
        """
        Inpaint multiple crops in parallel.

        Args:
            image_mask_pairs: List of (image_path, mask_path) tuples
            config: Inpaint configuration
            output_dir: Output directory for results

        Returns:
            List of result paths (None for failed jobs)
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create semaphore to limit parallelism
        semaphore = asyncio.Semaphore(self.batch_size)

        async def inpaint_with_semaphore(idx: int, image_path, mask_path):
            async with semaphore:
                output_filename = f"inpainted_{idx:06d}.png"
                return await self.inpaint_single(
                    image_path, mask_path, config, output_dir, output_filename
                )

        # Submit all jobs
        tasks = [
            inpaint_with_semaphore(idx, image_path, mask_path)
            for idx, (image_path, mask_path) in enumerate(image_mask_pairs)
        ]

        # Gather results
        results = await asyncio.gather(*tasks, return_exceptions=False)

        successful = len([r for r in results if r])
        logger.info(f"Batch complete: {successful} / {len(results)} succeeded")

        return results


async def execute_inpaint_workflow(
    image_mask_pairs: List[Tuple[Path, Path]],
    config: ProcessConfig,
) -> List[Optional[Path]]:
    """
    Execute inpaint workflow for a batch of crops.

    Convenience function for external callers.

    Args:
        image_mask_pairs: List of (crop_image, crop_mask) Path pairs
        config: ProcessConfig with inpaint and execution parameters

    Returns:
        List of inpainted image paths
    """
    executor = InpaintExecutor(
        host=config.comfyui_host,
        port=config.comfyui_port,
        timeout_sec=config.inpaint_timeout_sec,
        batch_size=config.batch_size,
    )

    return await executor.inpaint_batch(
        image_mask_pairs,
        config.inpaint,
        config.output_dir,
    )
