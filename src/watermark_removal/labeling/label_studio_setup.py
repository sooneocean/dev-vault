"""
Label Studio setup utilities for Docker MVP deployment.

Generates Docker Compose configuration, initializes projects,
and manages API key setup for self-hosted Label Studio.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DockerComposeGenerator:
    """Generate Docker Compose configuration for Label Studio."""

    @staticmethod
    def generate(
        output_path: str,
        port: int = 8080,
        data_dir: Optional[str] = None,
    ) -> bool:
        """
        Generate docker-compose.yml for Label Studio.

        Args:
            output_path: Path to write docker-compose.yml
            port: Port to expose Label Studio on
            data_dir: Directory for persistent data (default: ./data)

        Returns:
            True if successful
        """
        if data_dir is None:
            data_dir = "./label_studio_data"

        logger.info(f"Generating Docker Compose config: {output_path}")

        compose_content = f"""version: '3.8'

services:
  label-studio:
    image: heartexlabs/label-studio:latest
    container_name: label-studio
    ports:
      - "{port}:8080"
    environment:
      - LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true
      - LOCAL_FILES_DOCUMENT_ROOT=/label-studio/data
    volumes:
      - {data_dir}:/label-studio/data
      - {data_dir}/media:/label-studio/data/media
    networks:
      - label-studio-network

  postgres:
    image: postgres:13
    container_name: label-studio-db
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_USER: postgres
      POSTGRES_DB: label_studio
    volumes:
      - {data_dir}/db:/var/lib/postgresql/data
    networks:
      - label-studio-network

networks:
  label-studio-network:
    driver: bridge
"""

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            f.write(compose_content)

        logger.info(f"Docker Compose config written to {output_path}")
        return True


class ProjectInitializer:
    """Initialize Label Studio projects with label configuration."""

    LABEL_CONFIG_WATERMARK = """
<View>
  <Image name="image" value="$ocr"/>
  <RectangleLabeler name="label" toName="image">
    <Label value="watermark" background="red"/>
    <Label value="logo" background="green"/>
    <Label value="text" background="blue"/>
    <Label value="subtitle" background="yellow"/>
    <Label value="other" background="gray"/>
  </RectangleLabeler>
  <Choices name="quality" toName="image" choice="single">
    <Choice value="clear" background="lightblue"/>
    <Choice value="unclear" background="lightyellow"/>
    <Choice value="broken" background="lightcoral"/>
  </Choices>
</View>
"""

    @staticmethod
    def get_label_config() -> str:
        """
        Get Label Studio label configuration for watermark annotation.

        Returns:
            XML label config
        """
        return ProjectInitializer.LABEL_CONFIG_WATERMARK

    @staticmethod
    def initialize_project(
        project_name: str = "Watermark Removal",
        description: str = "Annotation workflow for watermark removal system",
    ) -> dict:
        """
        Get project initialization data.

        Args:
            project_name: Name of the project
            description: Project description

        Returns:
            Dict with project configuration (ready for API upload)
        """
        logger.info(f"Initializing project: {project_name}")

        project_config = {
            "title": project_name,
            "description": description,
            "label_config": ProjectInitializer.get_label_config(),
            "task_type": "image_bounding_box",
            "created_at": __import__("time").time(),
        }

        logger.info(f"Project config created: {project_name}")
        return project_config


class APIKeyManager:
    """Manage Label Studio API key storage and retrieval."""

    @staticmethod
    def setup_api_key(
        api_key: str,
        config_dir: Optional[str] = None,
    ) -> bool:
        """
        Store API key securely.

        Phase 3B MVP: Store in local config file with 0600 permissions.
        Phase 4: Migrate to environment variable or secrets manager.

        Args:
            api_key: API key from Label Studio
            config_dir: Directory to store config (default: ~/.label_studio)

        Returns:
            True if successful
        """
        if config_dir is None:
            config_dir = os.path.expanduser("~/.label_studio")

        config_dir = Path(config_dir)
        config_dir.mkdir(parents=True, exist_ok=True)

        # Also check environment variable
        env_key = os.environ.get("LABEL_STUDIO_API_KEY")
        if env_key:
            logger.info("API key found in environment variable LABEL_STUDIO_API_KEY")
            return True

        # Store in config file with restricted permissions
        config_file = config_dir / "api_key.json"

        config_data = {
            "api_key": api_key,
            "created_at": __import__("time").time(),
        }

        with open(config_file, "w") as f:
            json.dump(config_data, f, indent=2)

        # Restrict permissions to owner only
        os.chmod(config_file, 0o600)

        logger.info(f"API key stored at {config_file} (permissions: 0600)")
        return True

    @staticmethod
    def get_api_key(config_dir: Optional[str] = None) -> Optional[str]:
        """
        Retrieve stored API key.

        Args:
            config_dir: Directory where config is stored

        Returns:
            API key (or None if not found)
        """
        # Check environment variable first
        env_key = os.environ.get("LABEL_STUDIO_API_KEY")
        if env_key:
            logger.info("Using API key from LABEL_STUDIO_API_KEY environment variable")
            return env_key

        if config_dir is None:
            config_dir = os.path.expanduser("~/.label_studio")

        config_file = Path(config_dir) / "api_key.json"

        if not config_file.exists():
            logger.warning(f"API key file not found: {config_file}")
            return None

        try:
            with open(config_file, "r") as f:
                config_data = json.load(f)

            api_key = config_data.get("api_key")
            if api_key:
                logger.info("API key retrieved from config file")
                return api_key

            return None

        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to read API key: {e}")
            return None


class LabelStudioSetup:
    """High-level setup orchestration."""

    @staticmethod
    def setup_self_hosted(
        docker_compose_path: str = "./docker-compose.yml",
        data_dir: str = "./label_studio_data",
        port: int = 8080,
    ) -> bool:
        """
        Setup self-hosted Label Studio deployment.

        Args:
            docker_compose_path: Path to write docker-compose.yml
            data_dir: Data directory for persistence
            port: Port to expose Label Studio on

        Returns:
            True if successful
        """
        logger.info("Setting up self-hosted Label Studio")

        # Generate Docker Compose config
        if not DockerComposeGenerator.generate(docker_compose_path, port, data_dir):
            return False

        logger.info(
            f"Setup complete. Start Label Studio with:\n"
            f"  docker-compose -f {docker_compose_path} up -d\n"
            f"Then access at: http://localhost:{port}"
        )

        return True
