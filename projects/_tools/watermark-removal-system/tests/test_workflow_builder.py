"""
Unit tests for watermark_removal.inpaint.workflow_builder module.

Tests workflow JSON generation for ComfyUI Flux inpaint.
"""

import pytest
from pathlib import Path

from src.watermark_removal.inpaint.workflow_builder import WorkflowBuilder
from src.watermark_removal.core.types import InpaintConfig


class TestWorkflowBuilder:
    """Test WorkflowBuilder class."""

    def test_build_default_config(self):
        """Build workflow with default InpaintConfig."""
        image_path = "/path/to/crop.png"
        mask_path = "/path/to/mask.png"
        config = InpaintConfig()

        workflow = WorkflowBuilder.build(image_path, mask_path, config)

        assert workflow is not None
        assert isinstance(workflow, dict)
        # Check all required nodes exist
        assert "1" in workflow  # CheckpointLoader
        assert "2" in workflow  # LoadImage (crop)
        assert "3" in workflow  # LoadImage (mask)
        assert "4" in workflow  # CLIPTextEncode (positive)
        assert "5" in workflow  # CLIPTextEncode (negative)
        assert "6" in workflow  # VAEEncode
        assert "7" in workflow  # FluxInpaint
        assert "8" in workflow  # VAEDecode
        assert "9" in workflow  # SaveImage

    def test_build_node_structure(self):
        """Each node has correct structure (inputs, class_type, _meta)."""
        config = InpaintConfig()
        workflow = WorkflowBuilder.build("image.png", "mask.png", config)

        for node_id, node in workflow.items():
            assert "inputs" in node
            assert "class_type" in node
            assert "_meta" in node
            assert "title" in node["_meta"]

    def test_checkpoint_loader_node(self):
        """CheckpointLoader node uses config.model_name."""
        config = InpaintConfig(model_name="flux-pro")
        workflow = WorkflowBuilder.build("image.png", "mask.png", config)

        assert workflow["1"]["class_type"] == "CheckpointLoader"
        assert workflow["1"]["inputs"]["ckpt_name"] == "flux-pro"

    def test_image_loading_nodes(self):
        """LoadImage nodes have correct image paths."""
        image_path = "/custom/crop.png"
        mask_path = "/custom/mask.png"
        config = InpaintConfig()

        workflow = WorkflowBuilder.build(image_path, mask_path, config)

        assert workflow["2"]["class_type"] == "LoadImage"
        assert workflow["2"]["inputs"]["image"] == image_path
        assert workflow["3"]["class_type"] == "LoadImage"
        assert workflow["3"]["inputs"]["image"] == mask_path

    def test_text_encoding_nodes(self):
        """CLIPTextEncode nodes use config prompts."""
        config = InpaintConfig(
            prompt="create seamless background",
            negative_prompt="watermark, artifact, blur",
        )
        workflow = WorkflowBuilder.build("image.png", "mask.png", config)

        assert workflow["4"]["class_type"] == "CLIPTextEncode"
        assert workflow["4"]["inputs"]["text"] == "create seamless background"
        assert workflow["4"]["inputs"]["clip"] == ["1", 1]

        assert workflow["5"]["class_type"] == "CLIPTextEncode"
        assert workflow["5"]["inputs"]["text"] == "watermark, artifact, blur"
        assert workflow["5"]["inputs"]["clip"] == ["1", 1]

    def test_inpaint_node_parameters(self):
        """FluxInpaint node uses config parameters."""
        config = InpaintConfig(
            steps=30,
            cfg_scale=8.0,
            sampler="dpmpp_3m",
            scheduler="exponential",
            seed=42,
        )
        workflow = WorkflowBuilder.build("image.png", "mask.png", config)

        inpaint = workflow["7"]
        assert inpaint["class_type"] == "FluxInpaint"
        assert inpaint["inputs"]["steps"] == 30
        assert inpaint["inputs"]["cfg"] == 8.0
        assert inpaint["inputs"]["sampler_name"] == "dpmpp_3m"
        assert inpaint["inputs"]["scheduler"] == "exponential"
        assert inpaint["inputs"]["seed"] == 42

    def test_save_image_node(self):
        """SaveImage node has correct filename prefix."""
        workflow = WorkflowBuilder.build("image.png", "mask.png", InpaintConfig())

        save = workflow["9"]
        assert save["class_type"] == "SaveImage"
        # Default output filename is "inpainted.png", so prefix should be "inpainted"
        assert save["inputs"]["filename_prefix"] == "inpainted"

    def test_save_image_custom_filename(self):
        """SaveImage node uses custom output filename."""
        config = InpaintConfig()
        workflow = WorkflowBuilder.build(
            "image.png", "mask.png", config, output_filename="result_123.png"
        )

        assert workflow["9"]["inputs"]["filename_prefix"] == "result_123"

    def test_node_connections_valid(self):
        """Node connections reference valid nodes and outputs."""
        config = InpaintConfig()
        workflow = WorkflowBuilder.build("image.png", "mask.png", config)

        # Helper to validate connections
        def validate_connection(connection):
            if isinstance(connection, list) and len(connection) == 2:
                node_id, output_idx = connection
                return node_id in workflow and isinstance(output_idx, int)
            return True

        # Check FluxInpaint connections
        inpaint_inputs = workflow["7"]["inputs"]
        assert validate_connection(inpaint_inputs["positive"])
        assert validate_connection(inpaint_inputs["negative"])
        assert validate_connection(inpaint_inputs["latent_image"])
        assert validate_connection(inpaint_inputs["model"])
        assert validate_connection(inpaint_inputs["mask"])

        # Check VAEDecode connection
        vae_decode_inputs = workflow["8"]["inputs"]
        assert validate_connection(vae_decode_inputs["samples"])

        # Check SaveImage connection
        save_inputs = workflow["9"]["inputs"]
        assert validate_connection(save_inputs["images"])

    def test_path_object_handling(self):
        """Build accepts Path objects as well as strings."""
        config = InpaintConfig()
        image_path = Path("/path/to/crop.png")
        mask_path = Path("/path/to/mask.png")

        workflow = WorkflowBuilder.build(image_path, mask_path, config)

        assert workflow["2"]["inputs"]["image"] == str(image_path)
        assert workflow["3"]["inputs"]["image"] == str(mask_path)

    def test_seed_handling(self):
        """Seed value is correctly passed to FluxInpaint."""
        config_random = InpaintConfig(seed=-1)
        workflow_random = WorkflowBuilder.build("image.png", "mask.png", config_random)
        assert workflow_random["7"]["inputs"]["seed"] == -1

        config_fixed = InpaintConfig(seed=12345)
        workflow_fixed = WorkflowBuilder.build("image.png", "mask.png", config_fixed)
        assert workflow_fixed["7"]["inputs"]["seed"] == 12345


class TestWorkflowBuilderIntegration:
    """Integration tests for workflow generation."""

    def test_workflow_completeness(self):
        """Generated workflow has all required nodes for inpaint."""
        config = InpaintConfig()
        workflow = WorkflowBuilder.build("crop.png", "mask.png", config)

        required_classes = {
            "1": "CheckpointLoader",
            "2": "LoadImage",
            "3": "LoadImage",
            "4": "CLIPTextEncode",
            "5": "CLIPTextEncode",
            "6": "VAEEncode",
            "7": "FluxInpaint",
            "8": "VAEDecode",
            "9": "SaveImage",
        }

        for node_id, class_type in required_classes.items():
            assert node_id in workflow
            assert workflow[node_id]["class_type"] == class_type

    def test_workflow_serializable_json(self):
        """Workflow dict is JSON-serializable."""
        import json

        config = InpaintConfig()
        workflow = WorkflowBuilder.build("crop.png", "mask.png", config)

        # Should not raise
        json_str = json.dumps(workflow)
        assert json_str is not None

        # Deserialize to verify round-trip
        reloaded = json.loads(json_str)
        assert reloaded == workflow

    def test_multiple_workflows_independent(self):
        """Building multiple workflows doesn't cause interference."""
        config1 = InpaintConfig(model_name="flux-dev", seed=1)
        config2 = InpaintConfig(model_name="flux-pro", seed=2)

        workflow1 = WorkflowBuilder.build("image1.png", "mask1.png", config1)
        workflow2 = WorkflowBuilder.build("image2.png", "mask2.png", config2)

        assert workflow1["1"]["inputs"]["ckpt_name"] == "flux-dev"
        assert workflow1["7"]["inputs"]["seed"] == 1

        assert workflow2["1"]["inputs"]["ckpt_name"] == "flux-pro"
        assert workflow2["7"]["inputs"]["seed"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
