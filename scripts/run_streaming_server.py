#!/usr/bin/env python
"""
CLI entry point for streaming watermark removal server.

Usage:
    python scripts/run_streaming_server.py --port 8000 --host 0.0.0.0 --log-level info
"""

import argparse
import logging
import sys
from pathlib import Path


def setup_logging(log_level: str):
    """Configure logging for the application."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def main():
    """Main entry point for streaming server."""
    parser = argparse.ArgumentParser(
        description="Start the watermark removal streaming API server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start server on default port 8000
  python scripts/run_streaming_server.py

  # Start server on custom port with debug logging
  python scripts/run_streaming_server.py --port 8080 --log-level debug

  # Start server on specific host and port
  python scripts/run_streaming_server.py --host 127.0.0.1 --port 9000
        """,
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on (default: 8000)",
    )

    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Logging level (default: info)",
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1, use 1 for async-native server)",
    )

    parser.add_argument(
        "--use-uvloop",
        action="store_true",
        help="Use uvloop for async I/O acceleration (requires uvloop package)",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    logger.info("Watermark Removal Streaming API — Starting")
    logger.info(f"Configuration: host={args.host}, port={args.port}, workers={args.workers}")

    # Try to use uvloop for better async performance
    if args.use_uvloop:
        try:
            import uvloop

            asyncio_policy = uvloop.EventLoopPolicy()
            import asyncio

            asyncio.set_event_loop_policy(asyncio_policy)
            logger.info("Using uvloop for async event loop")
        except ImportError:
            logger.warning("uvloop not available, falling back to standard asyncio")

    # Import and run FastAPI app
    try:
        from watermark_removal.streaming.server import app

        import uvicorn

        logger.info(f"Starting server on {args.host}:{args.port}")

        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            workers=args.workers,
            log_level=args.log_level,
            access_log=args.log_level == "debug",  # Disable access logs unless debugging
        )

    except ImportError as e:
        logger.error(f"Failed to import watermark_removal.streaming.server: {e}")
        logger.error("Ensure watermark-removal-system package is installed or in PYTHONPATH")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
