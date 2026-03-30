"""Configuration management for watermark removal pipeline."""

import logging
from pathlib import Path

import yaml

from .types import InpaintConfig, ProcessConfig

logger = logging.getLogger(__name__)


class ConfigManager:
    """Load and validate YAML configuration files."""

    def __init__(self, config_path: str) -> None:
        """Initialize config manager.

        Args:
            config_path: Path to YAML config file (absolute or relative).

        Raises:
            FileNotFoundError: If config file does not exist.
        """
        self.config_path = Path(config_path).resolve()
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        logger.info(f"Loading config from {self.config_path}")

    def load(self) -> ProcessConfig:
        """Load and validate configuration.

        Returns:
            ProcessConfig: Validated system configuration object.

        Raises:
            ValueError: If required fields are missing or invalid.
            yaml.YAMLError: If config file is not valid YAML.
        """
        # Read YAML file
        with open(self.config_path, "r") as f:
            raw_config = yaml.safe_load(f) or {}

        # Validate required fields
        required_fields = ["video_path", "mask_path", "output_dir"]
        for field in required_fields:
            if field not in raw_config or not raw_config[field]:
                raise ValueError(f"Required config field missing: {field}")

        # Extract inpaint config (optional, with defaults)
        inpaint_raw = raw_config.get("inpaint", {})
        inpaint_config = InpaintConfig(
            model_name=inpaint_raw.get("model_name", "flux-dev.safetensors"),
            prompt=inpaint_raw.get("prompt", "remove watermark, clean background"),
            negative_prompt=inpaint_raw.get(
                "negative_prompt", "watermark, text, artifacts, blurry"
            ),
            steps=inpaint_raw.get("steps", 20),
            cfg_scale=inpaint_raw.get("cfg_scale", 7.5),
            seed=inpaint_raw.get("seed", 42),
            sampler=inpaint_raw.get("sampler", "euler"),
        )

        # Build ProcessConfig
        config = ProcessConfig(
            video_path=raw_config["video_path"],
            mask_path=raw_config["mask_path"],
            output_dir=raw_config["output_dir"],
            inpaint=inpaint_config,
            context_padding=raw_config.get("context_padding", 50),
            target_inpaint_size=raw_config.get("target_inpaint_size", 1024),
            batch_size=raw_config.get("batch_size", 4),
            timeout=raw_config.get("timeout", 300.0),
            output_codec=raw_config.get("output_codec", "h264"),
            output_crf=raw_config.get("output_crf", 23),
            keep_intermediate=raw_config.get("keep_intermediate", False),
            verbose=raw_config.get("verbose", True),
        )

        logger.info(
            f"Config loaded: video={config.video_path}, "
            f"mask={config.mask_path}, output={config.output_dir}"
        )
        logger.debug(f"Inpaint config: model={config.inpaint.model_name}, "
                     f"steps={config.inpaint.steps}, "
                     f"cfg={config.inpaint.cfg_scale}")

        return config
