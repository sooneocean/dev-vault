#!/usr/bin/env python3
"""CLI entry point for streaming watermark removal server.

Usage:
    python scripts/run_streaming_server.py --config config.yaml --port 8000

Uses uvloop for event loop optimization on supported platforms.
"""

import asyncio
import logging
import sys
from pathlib import Path

import click
import uvicorn

# Try to import uvloop for event loop optimization
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    HAS_UVLOOP = True
except ImportError:
    HAS_UVLOOP = False

from src.watermark_removal.streaming.server import create_app

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--port",
    type=int,
    default=8000,
    help="Server port (default 8000).",
)
@click.option(
    "--host",
    type=str,
    default="127.0.0.1",
    help="Server host (default 127.0.0.1).",
)
@click.option(
    "--queue-size",
    type=int,
    default=100,
    help="Maximum queue size for frames (default 100).",
)
@click.option(
    "--result-ttl",
    type=int,
    default=300,
    help="Result cache TTL in seconds (default 300).",
)
@click.option(
    "--workers",
    type=int,
    default=1,
    help="Number of uvicorn workers (default 1).",
)
@click.option(
    "--reload",
    is_flag=True,
    default=False,
    help="Enable auto-reload on code changes (dev mode).",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose logging.",
)
def main(
    port: int,
    host: str,
    queue_size: int,
    result_ttl: int,
    workers: int,
    reload: bool,
    verbose: bool,
) -> None:
    """Run FastAPI streaming server for watermark removal.

    This server accepts frames via HTTP POST and processes them asynchronously.
    Results are cached and can be polled via GET requests.

    Example:
        python scripts/run_streaming_server.py --port 8000
    """
    # Setup logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("Streaming server starting...")
    if HAS_UVLOOP:
        logger.info("Using uvloop for event loop optimization")
    else:
        logger.warning("uvloop not available, using standard asyncio")

    try:
        # Create FastAPI app
        app, session_manager, background_runner = create_app(
            process_func=None,  # Use default identity function
            queue_size=queue_size,
            result_ttl_sec=result_ttl,
        )

        logger.info(
            f"Starting server on {host}:{port} "
            f"(queue_size={queue_size}, result_ttl={result_ttl}s, workers={workers})"
        )

        # Run server
        uvicorn.run(
            app,
            host=host,
            port=port,
            workers=workers,
            reload=reload,
            log_level="debug" if verbose else "info",
        )

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
