"""Execute inpaint workflows asynchronously with ComfyUI."""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

from .workflow_builder import WorkflowBuilder
from ..core.types import InpaintConfig

logger = logging.getLogger(__name__)


class InpaintExecutor:
    """Submit crops to ComfyUI for inpaint, manage async execution queue, collect results."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8188) -> None:
        """Initialize inpaint executor with ComfyUI connection params.

        Args:
            host: ComfyUI server host (default: localhost).
            port: ComfyUI server port (default: 8188).
        """
        self.host = host
        self.port = port
        self.workflow_builder = WorkflowBuilder()

    async def inpaint_single(
        self,
        image_path: str,
        mask_path: str,
        config: InpaintConfig,
        output_dir: str,
    ) -> Path:
        """Submit a single crop for inpaint and await result.

        Args:
            image_path: Path to crop image file (must exist).
            mask_path: Path to inpaint mask file (must exist).
            config: InpaintConfig with model, prompt, steps, cfg, etc.
            output_dir: Directory to save inpainted result.

        Returns:
            Path to inpainted result image file.

        Raises:
            FileNotFoundError: If input files do not exist.
            RuntimeError: If inpaint submission or execution fails.
            TimeoutError: If inpaint execution exceeds timeout.
        """
        # Validate input files exist
        image_file = Path(image_path)
        mask_file = Path(mask_path)

        if not image_file.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        if not mask_file.exists():
            raise FileNotFoundError(f"Mask file not found: {mask_path}")

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Build workflow
        workflow = self.workflow_builder.build(
            image_path=str(image_file),
            mask_path=str(mask_file),
            config=config,
        )

        if not self.workflow_builder.validate_workflow(workflow):
            raise RuntimeError("Generated workflow is invalid")

        logger.debug(f"Built workflow for {image_file.name}")

        # Import ComfyUIClient here to avoid circular dependency
        # and because it requires aiohttp which may not be available
        try:
            from projects.tools.comfyui.client import ComfyUIClient
        except ImportError:
            raise RuntimeError(
                "ComfyUI client not available. Install projects/tools/comfyui "
                "or ensure aiohttp is installed."
            )

        # Submit to ComfyUI
        async with ComfyUIClient(host=self.host, port=self.port) as client:
            try:
                # Submit workflow
                prompt_id = await client.submit_prompt(workflow)
                logger.debug(f"Submitted prompt {prompt_id} for {image_file.name}")

                # Wait for execution with timeout
                await client.listen_execution(
                    prompt_id,
                    callback=None,
                    timeout=config.timeout if hasattr(config, 'timeout') else 300.0,
                )
                logger.debug(f"Execution complete for {prompt_id}")

            except asyncio.TimeoutError as e:
                raise TimeoutError(
                    f"Inpaint execution timeout for {image_file.name}: {e}"
                ) from e
            except Exception as e:
                raise RuntimeError(
                    f"Inpaint execution failed for {image_file.name}: {e}"
                ) from e

        # Locate output file
        # ComfyUI saves to output_path/[filename_prefix]_*.png
        filename_prefix = image_file.stem
        output_files = list(output_path.glob(f"{filename_prefix}_*.png"))

        if not output_files:
            raise RuntimeError(
                f"No output file found for {image_file.name} "
                f"(expected pattern: {filename_prefix}_*.png in {output_dir})"
            )

        # Use most recently modified file (in case multiple outputs exist)
        output_file = max(output_files, key=lambda p: p.stat().st_mtime)
        logger.info(f"Inpainted result saved to {output_file}")

        return output_file

    async def inpaint_batch(
        self,
        image_mask_pairs: List[Tuple[str, str]],
        config: InpaintConfig,
        output_dir: str,
        batch_size: int | None = None,
    ) -> List[Path]:
        """Submit multiple crops for inpaint in parallel and collect results.

        Args:
            image_mask_pairs: List of (image_path, mask_path) tuples.
            config: InpaintConfig applied to all crops.
            output_dir: Directory to save inpainted results.
            batch_size: Maximum parallel tasks (if None, all submitted immediately).

        Returns:
            List of paths to inpainted result images, in same order as input pairs.

        Raises:
            RuntimeError: If any inpaint execution fails.
            TimeoutError: If any execution exceeds timeout.
        """
        if not image_mask_pairs:
            logger.warning("No image-mask pairs to inpaint")
            return []

        # Use provided batch_size or default to all at once
        if batch_size is None:
            batch_size = len(image_mask_pairs)

        logger.info(
            f"Submitting {len(image_mask_pairs)} crops for inpaint "
            f"(batch_size={batch_size})"
        )

        results = []
        tasks = []

        for image_path, mask_path in image_mask_pairs:
            task = self.inpaint_single(
                image_path=image_path,
                mask_path=mask_path,
                config=config,
                output_dir=output_dir,
            )
            tasks.append(task)

            # Execute in batches if batch_size specified
            if len(tasks) >= batch_size:
                logger.debug(f"Executing batch of {len(tasks)} tasks")
                batch_results = await asyncio.gather(*tasks, return_exceptions=False)
                results.extend(batch_results)
                tasks = []

        # Execute remaining tasks
        if tasks:
            logger.debug(f"Executing final batch of {len(tasks)} tasks")
            batch_results = await asyncio.gather(*tasks, return_exceptions=False)
            results.extend(batch_results)

        logger.info(f"Inpaint batch complete: {len(results)} results collected")

        return results
