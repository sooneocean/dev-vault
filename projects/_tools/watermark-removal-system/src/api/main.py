"""
Main FastAPI application for watermark removal streaming service.

Integrates streaming endpoints, request/response validation,
middleware, and container health checks.
"""

import logging
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from src.api import streaming
from src.api.models import StreamingErrorResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.

    Startup: Initialize session manager
    Shutdown: Clean up all active sessions
    """
    # Startup
    logger.info("Watermark removal streaming service starting")
    yield
    # Shutdown
    logger.info("Watermark removal streaming service shutting down")
    # Clean up all sessions
    for session_id in list(streaming.session_manager.sessions.keys()):
        await streaming.session_manager.close_session(session_id)
    logger.info("All sessions closed")


# Create FastAPI app
app = FastAPI(
    title="Watermark Removal Streaming API",
    description="Real-time frame processing with WebSocket streaming",
    version="3.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include streaming router
app.include_router(streaming.router)


@app.get("/health")
async def health_check():
    """
    Health check endpoint for container orchestration.

    Returns:
        Health status with active session count
    """
    sessions = await streaming.session_manager.get_all_sessions()
    return {
        "status": "healthy",
        "service": "watermark-removal-streaming",
        "version": "3.0.0",
        "active_sessions": len(sessions),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/")
async def root():
    """API root endpoint with service information."""
    return {
        "service": "Watermark Removal Streaming API",
        "version": "3.0.0",
        "endpoints": {
            "health": "/health",
            "streaming": "/stream",
            "documentation": "/docs",
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors.

    Returns:
        StreamingErrorResponse with error details
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "error_code": "INTERNAL_SERVER_ERROR",
            "details": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


# Optional: Add request/response logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    """Log HTTP requests and responses."""
    logger.debug(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.debug(f"{request.method} {request.url.path} - {response.status_code}")
    return response


if __name__ == "__main__":
    import uvicorn

    # Run with: uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
