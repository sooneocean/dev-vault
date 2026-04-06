"""
ComfyUI Flux inpaint workflow builder.

Generates workflow JSON for submitting to ComfyUI.
"""

import json
from pathlib import Path

from ..core.types import InpaintConfig


class WorkflowBuilder:
    """Build ComfyUI Flux inpaint workflows."""

    @staticmethod
    def build(
        image_path: str | Path,
        mask_path: str | Path,
        config: InpaintConfig,
        output_filename: str = "inpainted.png",
    ) -> dict:
        """
        Build Flux inpaint ComfyUI workflow.

        Args:
            image_path: Path to input crop image
            mask_path: Path to inpaint mask
            config: InpaintConfig with model parameters
            output_filename: Output file name for SaveImage node

        Returns:
            Workflow dict ready for ComfyUI /prompt API
        """
        return {
            "1": {
                "inputs": {
                    "ckpt_name": config.model_name,
                },
                "class_type": "CheckpointLoader",
                "_meta": {"title": "Load Checkpoint"},
            },
            "2": {
                "inputs": {"image": str(image_path)},
                "class_type": "LoadImage",
                "_meta": {"title": "Load Image"},
            },
            "3": {
                "inputs": {"image": str(mask_path)},
                "class_type": "LoadImage",
                "_meta": {"title": "Load Mask"},
            },
            "4": {
                "inputs": {
                    "text": config.prompt,
                    "clip": ["1", 1],
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "Positive Prompt"},
            },
            "5": {
                "inputs": {
                    "text": config.negative_prompt,
                    "clip": ["1", 1],
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "Negative Prompt"},
            },
            "6": {
                "inputs": {
                    "image": ["2", 0],
                    "vae": ["1", 2],
                },
                "class_type": "VAEEncode",
                "_meta": {"title": "Encode Image"},
            },
            "7": {
                "inputs": {
                    "seed": config.seed,
                    "steps": config.steps,
                    "cfg": config.cfg_scale,
                    "sampler_name": config.sampler,
                    "scheduler": config.scheduler,
                    "positive": ["4", 0],
                    "negative": ["5", 0],
                    "latent_image": ["6", 0],
                    "model": ["1", 0],
                    "mask": ["3", 0],
                },
                "class_type": "FluxInpaint",
                "_meta": {"title": "Flux Inpaint"},
            },
            "8": {
                "inputs": {
                    "samples": ["7", 0],
                    "vae": ["1", 2],
                },
                "class_type": "VAEDecode",
                "_meta": {"title": "Decode Image"},
            },
            "9": {
                "inputs": {
                    "filename_prefix": Path(output_filename).stem,
                    "images": ["8", 0],
                },
                "class_type": "SaveImage",
                "_meta": {"title": "Save Image"},
            },
        }
