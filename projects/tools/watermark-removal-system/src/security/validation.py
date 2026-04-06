"""
Input validation for streaming API.

Validates video formats, file sizes, content types.
"""

import logging
from typing import Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Configuration
MAX_FILE_SIZE_MB = 5000  # 5GB
ALLOWED_VIDEO_FORMATS = {
    ".mp4",
    ".avi",
    ".mkv",
    ".mov",
    ".flv",
    ".webm",
    ".m3u8",  # HLS
}
ALLOWED_MIME_TYPES = {
    "video/mp4",
    "video/avi",
    "video/x-mkvideo",
    "video/quicktime",
    "video/x-flv",
    "video/webm",
    "application/vnd.apple.mpegurl",  # HLS
}
DANGEROUS_PATTERNS = {
    "../",
    "..\\",
    "/etc/",
    "\\windows\\",
    "C:\\",
}


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


class SourceValidator:
    """Validate streaming source URLs."""

    @staticmethod
    def validate_source_url(source_url: str) -> bool:
        """
        Validate source URL.

        Args:
            source_url: URL to validate

        Returns:
            True if valid

        Raises:
            ValidationError if invalid
        """
        if not source_url:
            raise ValidationError("Source URL cannot be empty")

        if len(source_url) > 2048:
            raise ValidationError("Source URL is too long")

        # Check for dangerous patterns
        for pattern in DANGEROUS_PATTERNS:
            if pattern in source_url:
                raise ValidationError(f"Dangerous pattern detected: {pattern}")

        # Check for valid protocol
        if source_url.startswith("file://"):
            return SourceValidator._validate_file_path(source_url[7:])
        elif source_url.startswith(("rtmp://", "rtsp://", "http://", "https://")):
            return True
        else:
            # Assume it's a file path
            return SourceValidator._validate_file_path(source_url)

    @staticmethod
    def _validate_file_path(file_path: str) -> bool:
        """Validate file path."""
        if not file_path:
            raise ValidationError("File path cannot be empty")

        # Check for dangerous patterns in path
        for pattern in DANGEROUS_PATTERNS:
            if pattern in file_path:
                raise ValidationError(f"Dangerous pattern in path: {pattern}")

        # Check file extension
        path = Path(file_path)
        if path.suffix.lower() not in ALLOWED_VIDEO_FORMATS:
            raise ValidationError(
                f"File format not allowed. Supported: {', '.join(ALLOWED_VIDEO_FORMATS)}"
            )

        # Check file size if file exists
        if path.exists():
            file_size_mb = path.stat().st_size / (1024 * 1024)
            if file_size_mb > MAX_FILE_SIZE_MB:
                raise ValidationError(
                    f"File too large: {file_size_mb:.1f}MB (max {MAX_FILE_SIZE_MB}MB)"
                )

        return True


class FormatValidator:
    """Validate video format specifications."""

    VALID_FORMATS = {
        "h264",  # H.264 (most compatible)
        "vp9",  # VP9
        "av1",  # AV1
        "hevc",  # HEVC/H.265
    }

    VALID_PRESETS = {
        "fast",  # Lowest quality, fastest
        "balanced",  # Medium quality/speed
        "quality",  # Highest quality, slowest
    }

    @staticmethod
    def validate_output_format(format_str: str) -> bool:
        """Validate output format."""
        if format_str not in FormatValidator.VALID_FORMATS:
            raise ValidationError(
                f"Invalid output format. Supported: {', '.join(FormatValidator.VALID_FORMATS)}"
            )
        return True

    @staticmethod
    def validate_quality_preset(preset_str: str) -> bool:
        """Validate quality preset."""
        if preset_str not in FormatValidator.VALID_PRESETS:
            raise ValidationError(
                f"Invalid preset. Supported: {', '.join(FormatValidator.VALID_PRESETS)}"
            )
        return True


class ConfigValidator:
    """Validate stream configuration."""

    @staticmethod
    def validate_buffer_size(buffer_size: int) -> bool:
        """Validate buffer size."""
        if not 1 <= buffer_size <= 300:
            raise ValidationError("Buffer size must be between 1 and 300")
        return True

    @staticmethod
    def validate_configuration(
        source_url: str,
        output_format: str,
        quality_preset: str,
        buffer_size: int,
    ) -> bool:
        """
        Validate complete stream configuration.

        Args:
            source_url: Source URL
            output_format: Output format
            quality_preset: Quality preset
            buffer_size: Buffer size

        Returns:
            True if valid

        Raises:
            ValidationError if any part is invalid
        """
        SourceValidator.validate_source_url(source_url)
        FormatValidator.validate_output_format(output_format)
        FormatValidator.validate_quality_preset(quality_preset)
        ConfigValidator.validate_buffer_size(buffer_size)

        logger.info(
            f"Configuration validated: {output_format} {quality_preset} (buffer={buffer_size})"
        )
        return True


class ContentTypeValidator:
    """Validate content types."""

    @staticmethod
    def validate_content_type(mime_type: Optional[str]) -> bool:
        """
        Validate content type.

        Args:
            mime_type: MIME type string

        Returns:
            True if valid

        Raises:
            ValidationError if invalid
        """
        if mime_type is None:
            return True

        if mime_type not in ALLOWED_MIME_TYPES:
            logger.warning(f"Unsupported MIME type: {mime_type}")
            # Don't raise - just warn

        return True


class RateLimiter:
    """Rate limiting for API access."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, List[float]] = {}

    def is_allowed(self, client_id: str) -> bool:
        """
        Check if request is allowed.

        Args:
            client_id: Client identifier (IP, user ID, etc)

        Returns:
            True if allowed, False if rate limited
        """
        import time

        now = time.time()
        window_start = now - self.window_seconds

        if client_id not in self.requests:
            self.requests[client_id] = []

        # Clean old requests
        self.requests[client_id] = [
            t for t in self.requests[client_id] if t > window_start
        ]

        # Check limit
        if len(self.requests[client_id]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for {client_id}")
            return False

        # Record this request
        self.requests[client_id].append(now)
        return True

    def get_remaining(self, client_id: str) -> int:
        """Get remaining requests for client."""
        import time

        if client_id not in self.requests:
            return self.max_requests

        now = time.time()
        window_start = now - self.window_seconds

        recent = [t for t in self.requests[client_id] if t > window_start]
        return max(0, self.max_requests - len(recent))
