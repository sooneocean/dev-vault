"""
FastAPI streaming service for real-time watermark removal.

Provides async REST API for submitting frames, querying results, and managing sessions.
Includes authentication, rate limiting, and webhook signature validation.
"""

import logging
from typing import Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Header, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..core.types import ProcessConfig
from .session_manager import SessionManager, FrameResult
from .queue_processor import BackgroundTaskRunner
from .auth import (
    verify_api_key,
    verify_bearer_token,
    check_rate_limit,
    hmac_validator,
)

logger = logging.getLogger(__name__)


# Pydantic models for request/response
class StreamStartRequest(BaseModel):
    """Request to start a streaming session."""

    config: Optional[dict] = None  # ProcessConfig as dict


class StreamStartResponse(BaseModel):
    """Response with session ID and metadata."""

    session_id: str
    created_at: datetime
    status: str = "active"


class StreamFrameResponse(BaseModel):
    """Response when frame is submitted."""

    session_id: str
    frame_id: int
    status: str = "queued"
    queue_size: int


class StreamResultResponse(BaseModel):
    """Response with frame result data."""

    frame_id: int
    status: str  # "pending", "processing", "completed", "error"
    timestamp: datetime
    metrics: dict
    error_message: Optional[str] = None
    output_path: Optional[str] = None


class StreamStopResponse(BaseModel):
    """Response when session is stopped."""

    session_id: str
    summary: dict  # Aggregated metrics and statistics


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    timestamp: datetime
    active_sessions: int


# Initialize FastAPI app and session manager
app = FastAPI(
    title="Watermark Removal Streaming API",
    description="Real-time streaming service for watermark removal with authentication and rate limiting",
    version="3.0.0",
)

# Add CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-API-Key", "X-Webhook-Signature", "X-Webhook-Timestamp"],
)

session_manager = SessionManager(result_ttl_sec=300, session_ttl_sec=600)
background_runners = {}  # Map of session_id -> BackgroundTaskRunner


@app.on_event("startup")
async def startup_event():
    """Initialize on server startup."""
    logger.info("Watermark Removal Streaming API starting")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown."""
    logger.info("Shutting down background tasks")
    for runner in background_runners.values():
        await runner.stop()
    background_runners.clear()


async def get_client_id(
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
) -> str:
    """
    Extract and validate client ID from API key or Bearer token.

    Args:
        x_api_key: API key from X-API-Key header
        authorization: Bearer token from Authorization header

    Returns:
        Client identifier

    Raises:
        HTTPException: If neither auth method provided or validation fails
    """
    # Try API key first
    if x_api_key:
        await verify_api_key(x_api_key)
        return f"api_key:{x_api_key[:20]}..."

    # Try Bearer token
    if authorization:
        client_id = await verify_bearer_token(authorization)
        return client_id

    # No auth provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authentication: provide X-API-Key or Authorization header",
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint (no auth required).

    Returns:
        HealthResponse with status and active session count
    """
    active_sessions = await session_manager.get_active_session_count()
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        active_sessions=active_sessions,
    )


@app.post("/stream/start", response_model=StreamStartResponse)
async def stream_start(
    request: StreamStartRequest,
    client_id: str = Depends(get_client_id),
) -> StreamStartResponse:
    """
    Start a new streaming session.

    Requires authentication via X-API-Key or Authorization header.

    Args:
        request: StreamStartRequest with optional ProcessConfig
        client_id: Authenticated client identifier (from dependency)

    Returns:
        StreamStartResponse with session_id and metadata

    Raises:
        HTTPException: If authentication fails or rate limit exceeded
    """
    # Check rate limit
    await check_rate_limit(client_id)

    # Build ProcessConfig from request (use defaults if not provided)
    config = ProcessConfig(
        video_path=Path("/tmp/placeholder.mp4"),  # Placeholder for streaming
        mask_path=Path("/tmp/placeholder_mask.mp4"),  # Placeholder for streaming
        output_dir=Path("/tmp/streaming_output"),
        # Additional config fields from request if provided
        **(request.config or {}),
    )

    # Create session
    session_id = await session_manager.create_session(config)
    session = await session_manager.get_session(session_id)

    # Start background task runner
    runner = BackgroundTaskRunner(
        session=session,
        max_queue_size=100,
        timeout_per_frame_sec=300.0,
    )
    await runner.start()
    background_runners[session_id] = runner

    logger.info(f"Started streaming session: {session_id} (client: {client_id})")

    return StreamStartResponse(
        session_id=session_id,
        created_at=session.created_at,
        status="active",
    )


@app.post("/stream/{session_id}/frame", response_model=StreamFrameResponse)
async def stream_frame(
    session_id: str,
    frame_id: int = Query(..., description="Frame sequence number"),
    file: UploadFile = File(...),
    client_id: str = Depends(get_client_id),
) -> StreamFrameResponse:
    """
    Submit a frame for processing in an active session.

    Requires authentication via X-API-Key or Authorization header.

    Args:
        session_id: Session identifier from /stream/start
        frame_id: Unique frame sequence number
        file: Frame image (PNG/JPEG)
        client_id: Authenticated client identifier (from dependency)

    Returns:
        StreamFrameResponse with queuing status and queue size

    Raises:
        HTTPException: If session not found, frame data invalid, or queue full
    """
    # Check rate limit
    await check_rate_limit(client_id)

    # Validate session
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    # Get runner
    runner = background_runners.get(session_id)
    if not runner:
        raise HTTPException(
            status_code=500,
            detail=f"Background runner not found for session: {session_id}",
        )

    # Read frame data
    try:
        frame_data = await file.read()
        if not frame_data:
            raise HTTPException(status_code=400, detail="Empty frame data")
    except Exception as e:
        logger.error(f"Failed to read frame data: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to read frame: {str(e)}")

    # Submit frame to queue
    queued = await runner.submit_frame(frame_id, frame_data)
    if not queued:
        logger.warning(f"Frame {frame_id} dropped due to queue overflow")
        raise HTTPException(
            status_code=503,
            detail="Processing queue full, frame dropped (backpressure)",
        )

    queue_size = await runner.get_queue_size()
    logger.info(f"Frame {frame_id} queued for session {session_id} (queue size: {queue_size})")

    return StreamFrameResponse(
        session_id=session_id,
        frame_id=frame_id,
        status="queued",
        queue_size=queue_size,
    )


@app.get("/stream/{session_id}/result/{frame_id}", response_model=StreamResultResponse)
async def stream_result(
    session_id: str,
    frame_id: int,
    client_id: str = Depends(get_client_id),
) -> StreamResultResponse:
    """
    Query result of a specific frame.

    Requires authentication via X-API-Key or Authorization header.

    Args:
        session_id: Session identifier
        frame_id: Frame sequence number
        client_id: Authenticated client identifier (from dependency)

    Returns:
        StreamResultResponse with frame status, metrics, and output

    Raises:
        HTTPException: If session not found or frame not found
    """
    # Check rate limit
    await check_rate_limit(client_id)

    # Validate session
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    # Get frame result
    result = session.get_frame_result(frame_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Frame {frame_id} not found in session {session_id}",
        )

    logger.debug(f"Queried result for frame {frame_id} in session {session_id}: {result.status}")

    return StreamResultResponse(
        frame_id=result.frame_id,
        status=result.status,
        timestamp=result.timestamp,
        metrics=result.metrics,
        error_message=result.error_message,
        output_path=str(result.output_path) if result.output_path else None,
    )


@app.post("/stream/{session_id}/stop", response_model=StreamStopResponse)
async def stream_stop(
    session_id: str,
    client_id: str = Depends(get_client_id),
) -> StreamStopResponse:
    """
    Stop a streaming session and return summary.

    Requires authentication via X-API-Key or Authorization header.

    Args:
        session_id: Session identifier
        client_id: Authenticated client identifier (from dependency)

    Returns:
        StreamStopResponse with session summary

    Raises:
        HTTPException: If session not found
    """
    # Check rate limit
    await check_rate_limit(client_id)

    # Validate session
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    # Get runner and wait for remaining frames
    runner = background_runners.get(session_id)
    if runner:
        # Wait for queue to drain (up to 300 seconds)
        await runner.wait_all_done(timeout_sec=300.0)
        await runner.stop()
        del background_runners[session_id]
        logger.info(f"Stopped background runner for session {session_id}")

    # End session and get summary
    summary = await session_manager.end_session(session_id)
    if not summary:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to end session: {session_id}",
        )

    logger.info(f"Ended streaming session: {session_id}, summary: {summary}")

    return StreamStopResponse(
        session_id=session_id,
        summary=summary,
    )


@app.post("/stream/{session_id}/cleanup")
async def cleanup_expired_sessions(
    client_id: str = Depends(get_client_id),
) -> dict:
    """
    Trigger cleanup of expired sessions (for maintenance).

    Requires authentication via X-API-Key or Authorization header.

    Args:
        client_id: Authenticated client identifier (from dependency)

    Returns:
        Dict with count of cleaned up sessions
    """
    # Check rate limit
    await check_rate_limit(client_id)

    count = await session_manager.cleanup_expired_sessions()
    return {"cleaned_up_sessions": count}


@app.post("/webhook/stream-event")
async def webhook_stream_event(
    payload: dict,
    x_webhook_signature: str = Header(...),
    x_webhook_timestamp: str = Header(...),
) -> dict:
    """
    Webhook endpoint for external stream events (e.g., new video upload).

    Validates HMAC signature and timestamp before processing.

    Args:
        payload: Event payload (JSON)
        x_webhook_signature: HMAC signature from X-Webhook-Signature header
        x_webhook_timestamp: Timestamp from X-Webhook-Timestamp header

    Returns:
        Acknowledgment dict

    Raises:
        HTTPException: If signature validation fails or payload invalid
    """
    import json

    # Serialize payload to bytes for signature validation
    payload_bytes = json.dumps(payload, sort_keys=True).encode()

    # Validate signature
    if not hmac_validator.validate_signature(
        payload_bytes,
        x_webhook_timestamp,
        x_webhook_signature,
        tolerance_sec=300,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    logger.info(
        f"Webhook received: {payload.get('event_type', 'unknown')} "
        f"at {x_webhook_timestamp}"
    )

    # Process event (stub for now)
    event_type = payload.get("event_type")
    if event_type == "stream_ready":
        session_id = payload.get("session_id")
        logger.info(f"Stream ready for session: {session_id}")

    return {
        "status": "received",
        "event_type": event_type,
        "timestamp": datetime.now().isoformat(),
    }


# Export app for uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
