"""FastAPI server for real-time frame streaming watermark removal."""

import asyncio
import io
import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse

from src.watermark_removal.core.types import ProcessConfig
from .queue_processor import BackgroundTaskRunner
from .session_manager import SessionManager, StreamingSession

logger = logging.getLogger(__name__)


def create_app(
    process_func=None,
    queue_size: int = 100,
    result_ttl_sec: int = 300,
) -> tuple[FastAPI, SessionManager, BackgroundTaskRunner]:
    """Create and configure FastAPI application for streaming.

    Args:
        process_func: Async frame processing function.
                     Signature: async func(frame: np.ndarray, session: StreamingSession) -> (output_frame, metrics)
        queue_size: Maximum frames in processing queue.
        result_ttl_sec: Result cache TTL in seconds.

    Returns:
        tuple: (FastAPI app, SessionManager, BackgroundTaskRunner)
    """
    app = FastAPI(title="Watermark Removal Streaming Service")
    session_manager = SessionManager(session_timeout_sec=600)

    # Default process function if not provided (identity function for testing)
    if process_func is None:
        async def default_process_func(frame: np.ndarray, session: StreamingSession):
            """Default identity processing function."""
            await asyncio.sleep(0.01)  # Simulate processing
            return frame, {"quality": 1.0, "time_ms": 10.0}

        process_func = default_process_func

    background_runner = BackgroundTaskRunner(process_func, queue_size=queue_size)

    @app.on_event("startup")
    async def startup_event():
        """Start background task runner on app startup."""
        await background_runner.start()
        logger.info("FastAPI app started, background runner activated")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Stop background task runner on app shutdown."""
        await background_runner.stop()
        logger.info("FastAPI app shutdown, background runner stopped")

    @app.post("/stream/start")
    async def stream_start(config_data: Optional[dict] = None) -> JSONResponse:
        """Create a new streaming session.

        Args:
            config_data: Optional configuration dict (ProcessConfig fields).

        Returns:
            JSON response with session_id.
        """
        # Create session with optional config
        config = None
        if config_data:
            try:
                config = ProcessConfig(**config_data)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid config: {str(e)}")

        session = session_manager.create_session(config=config)
        return JSONResponse(
            {
                "session_id": session.session_id,
                "created_at": session.created_at,
                "status": "active",
            }
        )

    @app.post("/stream/frame/{session_id}")
    async def stream_frame(
        session_id: str, file: UploadFile = File(...)
    ) -> JSONResponse:
        """Queue a frame for processing.

        Args:
            session_id: Session identifier.
            file: PNG frame file.

        Returns:
            JSON response with frame_id.
        """
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=400, detail=f"Invalid session_id: {session_id}")

        try:
            # Read frame from upload
            content = await file.read()
            frame_array = cv2.imdecode(
                np.frombuffer(content, np.uint8), cv2.IMREAD_COLOR
            )
            if frame_array is None:
                raise HTTPException(status_code=400, detail="Invalid image file")

            # Enqueue frame
            frame_id = session.frame_count
            session.frame_count += 1
            success = await background_runner.enqueue_frame(session, frame_id, frame_array)
            if not success:
                raise HTTPException(status_code=503, detail="Queue full, frame dropped")

            return JSONResponse(
                {
                    "frame_id": frame_id,
                    "session_id": session_id,
                    "queued_at": session.last_activity,
                }
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error queuing frame for session {session_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Error queuing frame: {str(e)}")

    @app.get("/stream/result/{session_id}/{frame_id}")
    async def stream_result(session_id: str, frame_id: int) -> JSONResponse:
        """Poll result for a specific frame.

        Args:
            session_id: Session identifier.
            frame_id: Frame identifier.

        Returns:
            JSON response with result status and frame data if available.
        """
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=400, detail=f"Invalid session_id: {session_id}")

        result = session.get_result(frame_id, result_ttl_sec)
        if not result:
            return JSONResponse(
                {
                    "status": "not_found",
                    "frame_id": frame_id,
                    "session_id": session_id,
                }
            )

        response = {
            "status": result.status,
            "frame_id": result.frame_id,
            "session_id": session_id,
            "metrics": result.metrics,
        }

        if result.status == "error":
            response["error_message"] = result.error_message
        elif result.status == "completed" and result.output_frame is not None:
            # Encode frame as PNG and include as base64
            _, png_data = cv2.imencode(".png", result.output_frame)
            import base64
            response["frame_base64"] = base64.b64encode(png_data).decode("utf-8")

        return JSONResponse(response)

    @app.post("/stream/stop/{session_id}")
    async def stream_stop(session_id: str) -> JSONResponse:
        """Finalize a streaming session.

        Args:
            session_id: Session identifier.

        Returns:
            JSON response with session metrics summary.
        """
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=400, detail=f"Invalid session_id: {session_id}")

        try:
            # Save checkpoint
            checkpoint_path = Path(f"/tmp/checkpoint_{session_id}.json")
            session.save_checkpoint(checkpoint_path)

            metrics_summary = session.get_metrics_summary()
            return JSONResponse(
                {
                    "session_id": session_id,
                    "frame_count": session.frame_count,
                    "processing_errors": session.processing_errors,
                    "metrics": metrics_summary,
                    "checkpoint_path": str(checkpoint_path),
                }
            )
        except Exception as e:
            logger.error(f"Error stopping session {session_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Error stopping session: {str(e)}")

    @app.get("/health")
    async def health_check() -> JSONResponse:
        """Health check endpoint.

        Returns:
            JSON response with server status and queue depth.
        """
        session_manager.cleanup_inactive_sessions()
        stats = background_runner.get_stats()
        return JSONResponse(
            {
                "status": "healthy",
                "queue_depth": stats["queue_depth"],
                "processed_count": stats["processed_count"],
                "error_count": stats["error_count"],
                "active_sessions": session_manager.get_session_count(),
            }
        )

    return app, session_manager, background_runner
