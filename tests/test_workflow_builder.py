"""Tests for workflow builder."""

import json
import tempfile
from pathlib import Path

import pytest

from src.watermark_removal.core.types import InpaintConfig
from src.watermark_removal.inpaint.workflow_builder import WorkflowBuilder


@pytest.fixture
def default_inpaint_config() -> InpaintConfig:
    """Create default inpaint config for testing."""
    return InpaintConfig(
        model_name="flux-dev.safetensors",
        prompt="remove watermark, clean background",
        negative_prompt="watermark, logo, text, artifacts",
        steps=20,
        cfg_scale=7.5,
        seed=42,
        sampler="euler",
    )


@pytest.fixture
def workflow_builder() -> WorkflowBuilder:
    """Create workflow builder instance."""
    return WorkflowBuilder()


class TestWorkflowBuilderHappyPath:
    """Happy path tests."""

    def test_workflow_builder_builds_valid_workflow(self, workflow_builder, default_inpaint_config):
        """Test building a valid workflow."""
        workflow = workflow_builder.build(
            image_path="/path/to/crop_image.png",
            mask_path="/path/to/inpaint_mask.png",
            config=default_inpaint_config,
        )

        # Verify workflow is dict
        assert isinstance(workflow, dict)

        # Verify all required nodes are present
        required_nodes = {"1", "2", "3", "4", "5", "6", "7", "8", "9"}
        assert required_nodes.issubset(set(workflow.keys()))

        # Verify workflow is valid
        assert workflow_builder.validate_workflow(workflow)

    def test_workflow_builder_substitutes_model_name(self, workflow_builder, default_inpaint_config):
        """Test that model name is substituted correctly."""
        config = InpaintConfig(
            model_name="custom-model.safetensors",
            prompt="test prompt",
            negative_prompt="test negative",
            steps=15,
            cfg_scale=8.0,
        )

        workflow = workflow_builder.build(
            image_path="/path/to/crop.png",
            mask_path="/path/to/mask.png",
            config=config,
        )

        assert workflow["1"]["inputs"]["ckpt_name"] == "custom-model.safetensors"

    def test_workflow_builder_substitutes_prompt(self, workflow_builder, default_inpaint_config):
        """Test that prompt is substituted correctly."""
        custom_prompt = "custom inpaint prompt"
        config = InpaintConfig(
            model_name="flux-dev.safetensors",
            prompt=custom_prompt,
            negative_prompt="negative",
            steps=20,
            cfg_scale=7.5,
        )

        workflow = workflow_builder.build(
            image_path="/path/to/crop.png",
            mask_path="/path/to/mask.png",
            config=config,
        )

        assert workflow["4"]["inputs"]["text"] == custom_prompt

    def test_workflow_builder_substitutes_negative_prompt(self, workflow_builder):
        """Test that negative prompt is substituted correctly."""
        negative_prompt = "custom negative prompt"
        config = InpaintConfig(
            model_name="flux-dev.safetensors",
            prompt="positive",
            negative_prompt=negative_prompt,
            steps=20,
            cfg_scale=7.5,
        )

        workflow = workflow_builder.build(
            image_path="/path/to/crop.png",
            mask_path="/path/to/mask.png",
            config=config,
        )

        assert workflow["5"]["inputs"]["text"] == negative_prompt

    def test_workflow_builder_substitutes_inpaint_parameters(self, workflow_builder):
        """Test that inpaint parameters are substituted correctly."""
        config = InpaintConfig(
            model_name="flux-dev.safetensors",
            prompt="test",
            negative_prompt="test",
            steps=50,
            cfg_scale=10.0,
            seed=123,
            sampler="dpmpp",
        )

        workflow = workflow_builder.build(
            image_path="/path/to/crop.png",
            mask_path="/path/to/mask.png",
            config=config,
        )

        node_7 = workflow["7"]["inputs"]
        assert node_7["steps"] == 50
        assert node_7["cfg"] == 10.0
        assert node_7["seed"] == 123
        assert node_7["sampler"] == "dpmpp"

    def test_workflow_builder_substitutes_image_path(self, workflow_builder, default_inpaint_config):
        """Test that image path is substituted correctly."""
        workflow = workflow_builder.build(
            image_path="/path/to/frame_000123.png",
            mask_path="/path/to/mask.png",
            config=default_inpaint_config,
        )

        # Should use filename only
        assert workflow["2"]["inputs"]["image"] == "frame_000123.png"

    def test_workflow_builder_substitutes_mask_path(self, workflow_builder, default_inpaint_config):
        """Test that mask path is substituted correctly."""
        workflow = workflow_builder.build(
            image_path="/path/to/crop.png",
            mask_path="/path/to/frame_000123_mask.png",
            config=default_inpaint_config,
        )

        # Should use filename only
        assert workflow["3"]["inputs"]["image"] == "frame_000123_mask.png"

    def test_workflow_builder_preserves_node_connections(self, workflow_builder, default_inpaint_config):
        """Test that node connections are preserved after building."""
        workflow = workflow_builder.build(
            image_path="/path/to/crop.png",
            mask_path="/path/to/mask.png",
            config=default_inpaint_config,
        )

        # Check key connections
        assert workflow["4"]["inputs"]["clip"] == ["1", 0]
        assert workflow["5"]["inputs"]["clip"] == ["1", 0]
        assert workflow["6"]["inputs"]["pixels"] == ["2", 0]
        assert workflow["6"]["inputs"]["vae"] == ["1", 2]
        assert workflow["7"]["inputs"]["latent"] == ["6", 0]
        assert workflow["7"]["inputs"]["conditioning"] == ["4", 0]
        assert workflow["8"]["inputs"]["latent"] == ["7", 0]
        assert workflow["9"]["inputs"]["images"] == ["8", 0]

    def test_workflow_builder_does_not_modify_template(self, workflow_builder, default_inpaint_config):
        """Test that building a workflow doesn't modify the template."""
        original_template = json.loads(json.dumps(workflow_builder.template))

        workflow1 = workflow_builder.build(
            image_path="/path/to/crop1.png",
            mask_path="/path/to/mask1.png",
            config=default_inpaint_config,
        )

        workflow2 = workflow_builder.build(
            image_path="/path/to/crop2.png",
            mask_path="/path/to/mask2.png",
            config=default_inpaint_config,
        )

        # Template should not have changed
        assert workflow_builder.template == original_template

        # Two workflows should be independent
        assert workflow1["2"]["inputs"]["image"] == "crop1.png"
        assert workflow2["2"]["inputs"]["image"] == "crop2.png"


class TestWorkflowBuilderEdgeCases:
    """Edge case tests."""

    def test_workflow_builder_with_no_seed(self, workflow_builder):
        """Test building workflow without specifying seed."""
        config = InpaintConfig(
            model_name="flux-dev.safetensors",
            prompt="test",
            negative_prompt="test",
            steps=20,
            cfg_scale=7.5,
            seed=None,  # No seed specified
            sampler="euler",
        )

        workflow = workflow_builder.build(
            image_path="/path/to/crop.png",
            mask_path="/path/to/mask.png",
            config=config,
        )

        # Seed from template should be preserved (42)
        assert workflow["7"]["inputs"]["seed"] == 42

    def test_workflow_builder_with_no_sampler(self, workflow_builder):
        """Test building workflow without specifying sampler."""
        config = InpaintConfig(
            model_name="flux-dev.safetensors",
            prompt="test",
            negative_prompt="test",
            steps=20,
            cfg_scale=7.5,
            seed=42,
            sampler=None,  # No sampler specified
        )

        workflow = workflow_builder.build(
            image_path="/path/to/crop.png",
            mask_path="/path/to/mask.png",
            config=config,
        )

        # Sampler from template should be preserved (euler)
        assert workflow["7"]["inputs"]["sampler"] == "euler"

    def test_workflow_builder_with_long_prompt(self, workflow_builder):
        """Test building workflow with very long prompt."""
        long_prompt = "remove watermark seamlessly " * 50
        config = InpaintConfig(
            model_name="flux-dev.safetensors",
            prompt=long_prompt,
            negative_prompt="artifacts",
            steps=20,
            cfg_scale=7.5,
        )

        workflow = workflow_builder.build(
            image_path="/path/to/crop.png",
            mask_path="/path/to/mask.png",
            config=config,
        )

        assert workflow["4"]["inputs"]["text"] == long_prompt

    def test_workflow_builder_with_special_characters_in_path(self, workflow_builder, default_inpaint_config):
        """Test building workflow with special characters in file paths."""
        workflow = workflow_builder.build(
            image_path="/path/to/frame_[001]-crop.png",
            mask_path="/path/to/frame_[001]-mask.png",
            config=default_inpaint_config,
        )

        assert workflow["2"]["inputs"]["image"] == "frame_[001]-crop.png"
        assert workflow["3"]["inputs"]["image"] == "frame_[001]-mask.png"


class TestWorkflowBuilderValidation:
    """Validation tests."""

    def test_workflow_validate_valid_workflow(self, workflow_builder, default_inpaint_config):
        """Test validation of a valid workflow."""
        workflow = workflow_builder.build(
            image_path="/path/to/crop.png",
            mask_path="/path/to/mask.png",
            config=default_inpaint_config,
        )

        assert workflow_builder.validate_workflow(workflow)

    def test_workflow_validate_rejects_non_dict(self, workflow_builder):
        """Test validation rejects non-dict input."""
        assert not workflow_builder.validate_workflow("not a dict")
        assert not workflow_builder.validate_workflow([])
        assert not workflow_builder.validate_workflow(None)

    def test_workflow_validate_rejects_missing_nodes(self, workflow_builder, default_inpaint_config):
        """Test validation rejects workflow with missing nodes."""
        workflow = workflow_builder.build(
            image_path="/path/to/crop.png",
            mask_path="/path/to/mask.png",
            config=default_inpaint_config,
        )

        # Remove a node
        del workflow["9"]

        assert not workflow_builder.validate_workflow(workflow)

    def test_workflow_validate_rejects_missing_class_type(self, workflow_builder, default_inpaint_config):
        """Test validation rejects node without class_type."""
        workflow = workflow_builder.build(
            image_path="/path/to/crop.png",
            mask_path="/path/to/mask.png",
            config=default_inpaint_config,
        )

        # Remove class_type from a node
        del workflow["1"]["class_type"]

        assert not workflow_builder.validate_workflow(workflow)

    def test_workflow_validate_rejects_invalid_connections(self, workflow_builder, default_inpaint_config):
        """Test validation rejects workflow with invalid node connections."""
        workflow = workflow_builder.build(
            image_path="/path/to/crop.png",
            mask_path="/path/to/mask.png",
            config=default_inpaint_config,
        )

        # Break a connection
        workflow["4"]["inputs"]["clip"] = ["wrong", 0]

        assert not workflow_builder.validate_workflow(workflow)


class TestWorkflowBuilderErrors:
    """Error handling tests."""

    def test_workflow_builder_missing_template_file(self):
        """Test error when template file does not exist."""
        with pytest.raises(FileNotFoundError, match="template not found"):
            WorkflowBuilder(template_path="/nonexistent/path/to/template.json")

    def test_workflow_builder_invalid_json_template(self):
        """Test error when template is invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json {")
            f.flush()
            temp_path = f.name

        try:
            with pytest.raises(json.JSONDecodeError):
                WorkflowBuilder(template_path=temp_path)
        finally:
            Path(temp_path).unlink()


class TestWorkflowBuilderIntegration:
    """Integration tests."""

    def test_workflow_builder_multiple_builds(self, workflow_builder):
        """Test building multiple workflows sequentially."""
        configs = [
            InpaintConfig(
                model_name="flux-dev.safetensors",
                prompt="remove watermark",
                negative_prompt="bad",
                steps=i * 10,
                cfg_scale=7.5 + i,
            )
            for i in range(1, 4)
        ]

        workflows = [
            workflow_builder.build(
                image_path=f"/path/to/crop_{i:06d}.png",
                mask_path=f"/path/to/mask_{i:06d}.png",
                config=config,
            )
            for i, config in enumerate(configs)
        ]

        # All workflows should be valid
        assert all(workflow_builder.validate_workflow(w) for w in workflows)

        # Each workflow should have different parameters
        assert workflows[0]["7"]["inputs"]["steps"] == 10
        assert workflows[1]["7"]["inputs"]["steps"] == 20
        assert workflows[2]["7"]["inputs"]["steps"] == 30
