"""
Data models for streaming API.

Request/response schemas for real-time frame processing.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum


class VideoFormatEnum(str, Enum):
    """Supported video formats."""
    H264 = "h264"      # H.264 (most compatible)
    VP9 = "vp9"        # VP9 (better compression)
    AV1 = "av1"        # AV1 (best compression, slow)
    HEVC = "hevc"      # HEVC/H.265


class QualityPresetEnum(str, Enum):
    """Quality/speed presets."""
    FAST = "fast"      # Lowest quality, fastest
    BALANCED = "balanced"  # Medium quality/speed
    QUALITY = "quality"    # Highest quality, slowest


class StreamingSessionRequest(BaseModel):
    """Request to start a streaming session."""
    source_url: str = Field(..., description="Input stream URL (RTMP, HLS, RTSP, file)")
    output_format: VideoFormatEnum = Field(default=VideoFormatEnum.H264)
    quality_preset: QualityPresetEnum = Field(default=QualityPresetEnum.BALANCED)
    buffer_size: int = Field(default=30, ge=1, le=300, description="Frame buffer size")
    enable_stats: bool = Field(default=True, description="Enable live statistics")

    class Config:
        example = {
            "source_url": "rtmp://example.com/live/stream",
            "output_format": "h264",
            "quality_preset": "balanced",
            "buffer_size": 30,
            "enable_stats": True,
        }


class StreamingSessionResponse(BaseModel):
    """Response when streaming session created."""
    session_id: str = Field(..., description="Unique session identifier")
    status: str = Field(default="active", description="Session status")
    stream_url: str = Field(..., description="Output stream URL for client")
    stats_url: str = Field(..., description="WebSocket URL for live statistics")
    created_at: str = Field(..., description="ISO 8601 timestamp")

    class Config:
        example = {
            "session_id": "sess_abc123def456",
            "status": "active",
            "stream_url": "ws://localhost:8000/stream/sess_abc123def456",
            "stats_url": "ws://localhost:8000/stats/sess_abc123def456",
            "created_at": "2026-03-31T10:30:00Z",
        }


class FrameStatistics(BaseModel):
    """Statistics for a single processed frame."""
    frame_id: int = Field(..., description="Frame index")
    timestamp_ms: float = Field(..., description="Timestamp in milliseconds")
    processing_time_ms: float = Field(..., description="Time to process frame")
    gpu_utilization_pct: float = Field(..., ge=0, le=100, description="GPU usage %")
    queue_depth: int = Field(..., ge=0, description="Frames waiting in queue")
    fps: float = Field(..., ge=0, description="Current throughput")
    status: str = Field(..., description="Status: processing/completed/error")

    class Config:
        example = {
            "frame_id": 1234,
            "timestamp_ms": 41333.33,
            "processing_time_ms": 45.2,
            "gpu_utilization_pct": 87.5,
            "queue_depth": 5,
            "fps": 22.3,
            "status": "completed",
        }


class StreamingStatsMessage(BaseModel):
    """WebSocket message with streaming statistics."""
    event_type: str = Field(..., description="Event: frame_processed, session_closed, error")
    data: Dict[str, Any] = Field(...)
    timestamp: str = Field(..., description="ISO 8601 timestamp")

    class Config:
        example = {
            "event_type": "frame_processed",
            "data": {
                "frame_id": 1234,
                "fps": 22.3,
                "processing_time_ms": 45.2,
            },
            "timestamp": "2026-03-31T10:30:45.123Z",
        }


class SessionStatusRequest(BaseModel):
    """Request session status."""
    session_id: str = Field(..., description="Session ID to check")


class SessionStatusResponse(BaseModel):
    """Response with session status."""
    session_id: str = Field(...)
    status: str = Field(..., description="Status: active/stopped/error")
    uptime_sec: float = Field(..., description="Seconds since session start")
    frames_processed: int = Field(..., description="Total frames processed")
    frames_dropped: int = Field(..., description="Total frames dropped")
    avg_fps: float = Field(..., description="Average throughput")
    errors: int = Field(..., description="Error count")

    class Config:
        example = {
            "session_id": "sess_abc123def456",
            "status": "active",
            "uptime_sec": 123.45,
            "frames_processed": 2789,
            "frames_dropped": 3,
            "avg_fps": 22.6,
            "errors": 0,
        }


class StreamingErrorResponse(BaseModel):
    """Error response for streaming operations."""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    details: Optional[str] = Field(None, description="Additional details")
    timestamp: str = Field(..., description="ISO 8601 timestamp")

    class Config:
        example = {
            "error": "Source stream disconnected",
            "error_code": "STREAM_DISCONNECTED",
            "details": "Connection lost after 123 seconds",
            "timestamp": "2026-03-31T10:30:45.123Z",
        }
