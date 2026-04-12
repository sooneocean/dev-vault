#!/usr/bin/env python3
"""Label Studio setup and initialization script.

Generates Docker Compose configuration, creates initial project, and validates setup.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from watermark_removal.annotation.label_studio_client import LabelStudioClient

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


LABEL_CONFIG_BBOX = """<View>
  <Image name="image" value="$image_url" width="100%" height="100%"/>
  <RectangleLabeler name="label" toName="image">
    <Label value="watermark" background="red"/>
  </RectangleLabeler>
  <Choices name="confidence" toName="image">
    <Choice value="high" background="green"/>
    <Choice value="medium" background="yellow"/>
    <Choice value="low" background="red"/>
  </Choices>
</View>
"""


async def create_project(
    client: LabelStudioClient,
    project_title: str = "Watermark Detection",
    project_description: str = "Review and correct watermark detection annotations",
) -> dict:
    """Create a new Label Studio project.

    Args:
        client: LabelStudioClient instance.
        project_title: Project title.
        project_description: Project description.

    Returns:
        Project response dict.

    Raises:
        RuntimeError: If project creation fails.
    """
    logger.info(f"Creating Label Studio project: {project_title}")

    try:
        project = await client.create_project(
            title=project_title,
            description=project_description,
            label_config=LABEL_CONFIG_BBOX,
        )

        logger.info(f"Project created successfully (ID: {project.get('id')})")
        return project

    except RuntimeError as e:
        logger.error(f"Failed to create project: {e}")
        raise


async def validate_setup(
    host: str = "localhost",
    port: int = 8080,
    api_key: str = "",
) -> bool:
    """Validate Label Studio setup.

    Args:
        host: Label Studio host.
        port: Label Studio port.
        api_key: Label Studio API key.

    Returns:
        True if setup is valid.

    Raises:
        RuntimeError: If validation fails.
    """
    logger.info(f"Validating Label Studio at {host}:{port}")

    if not api_key:
        logger.warning("No API key provided. Setup requires manual authentication.")
        logger.info("Start Label Studio and create an API key:")
        logger.info("  1. Navigate to http://{host}:{port}")
        logger.info("  2. Create a new user or login")
        logger.info("  3. Go to Account Settings > API Tokens")
        logger.info("  4. Create and copy your API token")
        return False

    client = LabelStudioClient(
        host=host,
        port=port,
        api_key=api_key,
    )

    try:
        await client.validate_connection()
        logger.info("Label Studio connection validated")
        return True

    except RuntimeError as e:
        logger.error(f"Label Studio validation failed: {e}")
        raise
    finally:
        await client.close()


async def main() -> None:
    """Main setup workflow."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Label Studio setup and initialization for watermark detection"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Label Studio host (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Label Studio port (default: 8080)",
    )
    parser.add_argument(
        "--api-key",
        default="",
        help="Label Studio API key (optional for validation only)",
    )
    parser.add_argument(
        "--create-project",
        action="store_true",
        help="Create initial watermark detection project",
    )
    parser.add_argument(
        "--project-title",
        default="Watermark Detection",
        help="Project title (default: Watermark Detection)",
    )

    args = parser.parse_args()

    try:
        # Validate setup
        is_valid = await validate_setup(
            host=args.host,
            port=args.port,
            api_key=args.api_key,
        )

        if not is_valid and args.api_key:
            logger.error("Setup validation failed")
            sys.exit(1)

        # Create project if requested
        if args.create_project:
            if not args.api_key:
                logger.error("--api-key required when --create-project is used")
                sys.exit(1)

            client = LabelStudioClient(
                host=args.host,
                port=args.port,
                api_key=args.api_key,
            )

            try:
                await create_project(client, args.project_title)
                logger.info("Project created and ready for use")
            finally:
                await client.close()

        logger.info("Label Studio setup completed successfully")

    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
