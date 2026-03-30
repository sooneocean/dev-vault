"""
Configuration management for the watermark removal pipeline.

Loads YAML config files, validates parameters, and constructs ProcessConfig objects.
"""

import logging
from pathlib import Path
import yaml

from .types import ProcessConfig, InpaintConfig


logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manages configuration loading and validation.

    Loads a YAML configuration file, validates required fields, applies defaults,
    and constructs a ProcessConfig object suitable for the pipeline.
    """

    REQUIRED_FIELDS = {"video_path", "mask_path"}

    def __init__(self, config_path: str | Path):
        """
        Initialize ConfigManager with a config file path.

        Args:
            config_path: Path to YAML configuration file

        Raises:
            FileNotFoundError: If config file does not exist
        """
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

    def load(self) -> ProcessConfig:
        """
        Load and validate configuration from YAML file.

        Returns:
            ProcessConfig object ready for pipeline execution

        Raises:
            ValueError: If required fields are missing
            yaml.YAMLError: If YAML parsing fails
        """
        logger.info(f"Loading config from {self.config_path}")

        # Load YAML
        with open(self.config_path, "r") as f:
            config_dict = yaml.safe_load(f) or {}

        # Validate required fields
        missing = self.REQUIRED_FIELDS - set(config_dict.keys())
        if missing:
            raise ValueError(
                f"Missing required config fields: {missing}. "
                f"Required: {self.REQUIRED_FIELDS}"
            )

        # Extract and build InpaintConfig if present
        inpaint_dict = config_dict.pop("inpaint", {})
        inpaint_config = InpaintConfig(**inpaint_dict) if inpaint_dict else InpaintConfig()

        # Build ProcessConfig with all available parameters
        # Any missing parameters will use dataclass defaults
        process_config = ProcessConfig(
            inpaint=inpaint_config,
            **config_dict,
        )

        logger.info(
            f"Config loaded successfully: "
            f"video={process_config.video_path}, "
            f"mask={process_config.mask_path}, "
            f"output={process_config.output_dir}"
        )

        return process_config
