"""
Unit tests for Docker deployment configuration.

Tests Dockerfile build, docker-compose configuration, and environment setup.
"""

import pytest
import tempfile
from pathlib import Path
import yaml
import sys


class TestDockerfile:
    """Test Dockerfile configuration."""

    def test_dockerfile_exists(self):
        """Dockerfile exists in repository root."""
        dockerfile = Path(__file__).parent.parent / "Dockerfile"
        assert dockerfile.exists()

    def test_dockerfile_has_required_stages(self):
        """Dockerfile has multi-stage build structure."""
        dockerfile = Path(__file__).parent.parent / "Dockerfile"
        content = dockerfile.read_text()

        # Should have builder stage
        assert "FROM python:3.11-slim as builder" in content
        # Should have runtime stage
        assert "FROM python:3.11-slim" in content
        # Should copy from builder
        assert "COPY --from=builder" in content

    def test_dockerfile_has_entrypoint(self):
        """Dockerfile has ENTRYPOINT set."""
        dockerfile = Path(__file__).parent.parent / "Dockerfile"
        content = dockerfile.read_text()

        assert "ENTRYPOINT" in content
        assert "run_pipeline.py" in content

    def test_dockerfile_has_healthcheck(self):
        """Dockerfile has HEALTHCHECK configured."""
        dockerfile = Path(__file__).parent.parent / "Dockerfile"
        content = dockerfile.read_text()

        assert "HEALTHCHECK" in content


class TestDockerCompose:
    """Test docker-compose configuration."""

    def test_docker_compose_exists(self):
        """docker-compose.yml exists."""
        compose_file = Path(__file__).parent.parent / "docker-compose.yml"
        assert compose_file.exists()

    def test_docker_compose_valid_yaml(self):
        """docker-compose.yml is valid YAML."""
        compose_file = Path(__file__).parent.parent / "docker-compose.yml"
        content = compose_file.read_text()

        config = yaml.safe_load(content)
        assert isinstance(config, dict)
        assert "services" in config

    def test_docker_compose_has_watermark_removal_service(self):
        """docker-compose has watermark-removal service."""
        compose_file = Path(__file__).parent.parent / "docker-compose.yml"
        config = yaml.safe_load(compose_file.read_text())

        assert "services" in config
        assert "watermark-removal" in config["services"]

    def test_docker_compose_has_comfyui_service(self):
        """docker-compose has comfyui service."""
        compose_file = Path(__file__).parent.parent / "docker-compose.yml"
        config = yaml.safe_load(compose_file.read_text())

        assert "comfyui" in config["services"]

    def test_docker_compose_services_connected(self):
        """Services are connected via network."""
        compose_file = Path(__file__).parent.parent / "docker-compose.yml"
        config = yaml.safe_load(compose_file.read_text())

        # Check network configuration
        assert "networks" in config
        assert "watermark-removal-network" in config["networks"]

        # Check each service uses network
        for service_name, service in config["services"].items():
            if service_name in ["watermark-removal", "comfyui"]:
                assert "networks" in service
                assert "watermark-removal-network" in service.get("networks", {})

    def test_docker_compose_volumes_configured(self):
        """Services have proper volume mounts."""
        compose_file = Path(__file__).parent.parent / "docker-compose.yml"
        config = yaml.safe_load(compose_file.read_text())

        watermark_service = config["services"]["watermark-removal"]

        # Should have input/output volumes
        assert "volumes" in watermark_service
        volumes_str = str(watermark_service["volumes"])

        assert "/data/input" in volumes_str
        assert "/data/output" in volumes_str

    def test_docker_compose_healthchecks(self):
        """Services have health checks configured."""
        compose_file = Path(__file__).parent.parent / "docker-compose.yml"
        config = yaml.safe_load(compose_file.read_text())

        for service_name in ["watermark-removal", "comfyui"]:
            service = config["services"][service_name]
            assert "healthcheck" in service

    def test_docker_compose_environment_variables(self):
        """Services use environment variables."""
        compose_file = Path(__file__).parent.parent / "docker-compose.yml"
        config = yaml.safe_load(compose_file.read_text())

        watermark_service = config["services"]["watermark-removal"]

        # Should reference environment variables
        assert "environment" in watermark_service
        env = watermark_service["environment"]

        # Should have COMFYUI configuration
        env_str = str(env)
        assert "COMFYUI" in env_str


class TestEnvironmentConfig:
    """Test .env.example configuration."""

    def test_env_example_exists(self):
        """.env.example exists."""
        env_file = Path(__file__).parent.parent / ".env.example"
        assert env_file.exists()

    def test_env_example_has_required_variables(self):
        """.env.example has required variables."""
        env_file = Path(__file__).parent.parent / ".env.example"
        content = env_file.read_text()

        # Required variables
        required = [
            "COMFYUI_HOST",
            "COMFYUI_PORT",
            "GPU_INDEX",
            "MODELS_CACHE",
            "WATERMARK_REMOVAL_PORT",
        ]

        for var in required:
            assert var in content


class TestYAMLConfig:
    """Test docker.yaml configuration."""

    def test_docker_yaml_exists(self):
        """config/docker.yaml exists."""
        config_file = Path(__file__).parent.parent / "config" / "docker.yaml"
        assert config_file.exists()

    def test_docker_yaml_valid(self):
        """config/docker.yaml is valid YAML."""
        config_file = Path(__file__).parent.parent / "config" / "docker.yaml"
        content = config_file.read_text()

        # Extract just YAML part (before ---)
        yaml_part = content.split("---")[0]

        config = yaml.safe_load(yaml_part)
        assert isinstance(config, dict)

    def test_docker_yaml_has_required_fields(self):
        """config/docker.yaml has required fields."""
        config_file = Path(__file__).parent.parent / "config" / "docker.yaml"
        yaml_part = config_file.read_text().split("---")[0]

        config = yaml.safe_load(yaml_part)

        # Required fields
        required = [
            "video_path",
            "mask_path",
            "output_dir",
            "batch_size",
            "comfyui_host",
            "comfyui_port",
        ]

        for field in required:
            assert field in config

    def test_docker_yaml_phase2_configs(self):
        """config/docker.yaml includes Phase 2 options."""
        config_file = Path(__file__).parent.parent / "config" / "docker.yaml"
        yaml_part = config_file.read_text().split("---")[0]

        config = yaml.safe_load(yaml_part)

        # Phase 2 features
        phase2_fields = [
            "temporal_smooth_alpha",
            "use_adaptive_temporal_smoothing",
            "use_poisson_blending",
            "use_yolo_detection",
            "max_watermarks_per_frame",
            "use_watermark_tracker",
            "use_checkpoints",
        ]

        for field in phase2_fields:
            assert field in config


class TestDeploymentDocs:
    """Test deployment documentation."""

    def test_deployment_md_exists(self):
        """DEPLOYMENT.md exists."""
        doc = Path(__file__).parent.parent / "docs" / "DEPLOYMENT.md"
        assert doc.exists()

    def test_deployment_md_has_quickstart(self):
        """DEPLOYMENT.md has Quick Start section."""
        doc = Path(__file__).parent.parent / "docs" / "DEPLOYMENT.md"
        content = doc.read_text(encoding='utf-8')

        assert "Quick Start" in content
        assert "Prerequisites" in content
        assert "Environment Setup" in content

    def test_deployment_md_has_examples(self):
        """DEPLOYMENT.md has deployment examples."""
        doc = Path(__file__).parent.parent / "docs" / "DEPLOYMENT.md"
        content = doc.read_text(encoding='utf-8')

        assert "docker-compose" in content
        assert "curl" in content
        assert "http://localhost" in content

    def test_deployment_md_has_gpu_section(self):
        """DEPLOYMENT.md documents GPU support."""
        doc = Path(__file__).parent.parent / "docs" / "DEPLOYMENT.md"
        content = doc.read_text(encoding='utf-8')

        assert "GPU" in content.upper()
        assert "nvidia" in content.lower() or "NVIDIA" in content

    def test_deployment_md_has_troubleshooting(self):
        """DEPLOYMENT.md has Troubleshooting section."""
        doc = Path(__file__).parent.parent / "docs" / "DEPLOYMENT.md"
        content = doc.read_text(encoding='utf-8')

        assert "Troubleshooting" in content
        assert "out of memory" in content.lower()


class TestDockerStructure:
    """Test overall Docker deployment structure."""

    def test_docker_files_organized(self):
        """Docker-related files are organized correctly."""
        root = Path(__file__).parent.parent

        # Check files exist
        assert (root / "Dockerfile").exists()
        assert (root / "docker-compose.yml").exists()
        assert (root / ".env.example").exists()
        assert (root / "config" / "docker.yaml").exists()
        assert (root / "docs" / "DEPLOYMENT.md").exists()

    def test_data_directories_referenced(self):
        """Docker config references standard data directories."""
        compose_file = Path(__file__).parent.parent / "docker-compose.yml"
        config = yaml.safe_load(compose_file.read_text())

        # Check for standard paths
        compose_str = str(config)

        assert "/data/input" in compose_str
        assert "/data/output" in compose_str
        assert "/data/checkpoints" in compose_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
