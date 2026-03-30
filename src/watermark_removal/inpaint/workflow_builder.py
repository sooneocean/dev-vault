"""Build Flux inpaint ComfyUI workflows from templates."""

import json
import logging
from pathlib import Path
from typing import Dict, Any

from ..core.types import InpaintConfig

logger = logging.getLogger(__name__)


class WorkflowBuilder:
    """Generate Flux inpaint ComfyUI workflow JSON from crop and mask file paths."""

    def __init__(self, template_path: str | None = None) -> None:
        """Initialize workflow builder with template path.

        Args:
            template_path: Path to flux_inpaint_base.json template.
                          Defaults to workflows/flux_inpaint_base.json in project root.
        """
        if template_path is None:
            # Assume workflows/ is in project root
            template_path = str(Path(__file__).parent.parent.parent.parent / "workflows" / "flux_inpaint_base.json")

        self.template_path = template_path
        self.template = self._load_template()

    def _load_template(self) -> Dict[str, Any]:
        """Load workflow template from JSON file.

        Returns:
            Workflow dict from template.

        Raises:
            FileNotFoundError: If template file does not exist.
            json.JSONDecodeError: If template is invalid JSON.
        """
        template_file = Path(self.template_path)
        if not template_file.exists():
            raise FileNotFoundError(f"Workflow template not found: {self.template_path}")

        with open(template_file, "r", encoding="utf-8") as f:
            template = json.load(f)

        logger.debug(f"Loaded workflow template from {self.template_path}")
        return template

    def build(
        self,
        image_path: str,
        mask_path: str,
        config: InpaintConfig,
    ) -> Dict[str, Any]:
        """Generate Flux inpaint workflow JSON from paths and config.

        Args:
            image_path: Path to crop image (will be loaded by ComfyUI).
            mask_path: Path to inpaint mask (will be loaded by ComfyUI).
            config: InpaintConfig with model name, prompt, steps, cfg, etc.

        Returns:
            Workflow dict suitable for ComfyUI /prompt API.
        """
        # Deep copy template to avoid modifying original
        workflow = json.loads(json.dumps(self.template))

        # Update model name (node 1: CheckpointLoaderSimple)
        workflow["1"]["inputs"]["ckpt_name"] = config.model_name

        # Update image path (node 2: LoadImage)
        workflow["2"]["inputs"]["image"] = Path(image_path).name

        # Update mask path (node 3: LoadImage)
        workflow["3"]["inputs"]["image"] = Path(mask_path).name

        # Update positive prompt (node 4: CLIPTextEncode)
        workflow["4"]["inputs"]["text"] = config.prompt

        # Update negative prompt (node 5: CLIPTextEncode)
        workflow["5"]["inputs"]["text"] = config.negative_prompt

        # Update inpaint parameters (node 7: FluxInpaint)
        workflow["7"]["inputs"]["steps"] = config.steps
        workflow["7"]["inputs"]["cfg"] = config.cfg_scale
        if config.seed is not None:
            workflow["7"]["inputs"]["seed"] = config.seed
        if config.sampler is not None:
            workflow["7"]["inputs"]["sampler"] = config.sampler

        # Update SaveImage filename prefix (node 9: SaveImage)
        # Use stem of image_path as prefix for organization
        image_stem = Path(image_path).stem
        workflow["9"]["inputs"]["filename_prefix"] = image_stem

        logger.debug(
            f"Built workflow for {Path(image_path).name}: "
            f"model={config.model_name}, prompt={config.prompt[:30]}..., "
            f"steps={config.steps}, cfg={config.cfg_scale}"
        )

        return workflow

    def validate_workflow(self, workflow: Dict[str, Any]) -> bool:
        """Validate workflow structure.

        Args:
            workflow: Workflow dict to validate.

        Returns:
            True if workflow is valid, False otherwise.
        """
        # Check basic structure
        if not isinstance(workflow, dict):
            return False

        required_node_ids = {"1", "2", "3", "4", "5", "6", "7", "8", "9"}
        if not required_node_ids.issubset(set(workflow.keys())):
            return False

        # Check each node has required fields
        for node_id, node_data in workflow.items():
            if not isinstance(node_data, dict):
                return False
            if "class_type" not in node_data:
                return False
            if "inputs" not in node_data:
                return False

        # Check critical node connections
        # Node 4 should reference node 1 output
        if workflow.get("4", {}).get("inputs", {}).get("clip") != ["1", 0]:
            return False

        # Node 5 should reference node 1 output
        if workflow.get("5", {}).get("inputs", {}).get("clip") != ["1", 0]:
            return False

        # Node 6 should reference node 2 and node 1
        node_6_inputs = workflow.get("6", {}).get("inputs", {})
        if node_6_inputs.get("pixels") != ["2", 0]:
            return False
        if node_6_inputs.get("vae") != ["1", 2]:
            return False

        # Node 7 should reference nodes 6, 3, 4, 5, 1
        node_7_inputs = workflow.get("7", {}).get("inputs", {})
        if node_7_inputs.get("latent") != ["6", 0]:
            return False
        if node_7_inputs.get("mask") != ["3", 0]:
            return False
        if node_7_inputs.get("conditioning") != ["4", 0]:
            return False
        if node_7_inputs.get("negative_conditioning") != ["5", 0]:
            return False
        if node_7_inputs.get("model") != ["1", 0]:
            return False

        # Node 8 should reference nodes 7 and 1
        node_8_inputs = workflow.get("8", {}).get("inputs", {})
        if node_8_inputs.get("latent") != ["7", 0]:
            return False
        if node_8_inputs.get("vae") != ["1", 2]:
            return False

        # Node 9 should reference node 8
        if workflow.get("9", {}).get("inputs", {}).get("images") != ["8", 0]:
            return False

        return True
