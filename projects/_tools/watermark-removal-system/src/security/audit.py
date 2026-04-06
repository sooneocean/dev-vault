"""
Audit logging for security and compliance.

Tracks user actions, configuration changes, and errors.
"""

import logging
import json
from datetime import datetime, timezone
from typing import Optional, Any, Dict
from enum import Enum
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Types of audit events."""
    # Authentication
    AUTH_LOGIN = "auth_login"
    AUTH_LOGOUT = "auth_logout"
    AUTH_FAILED = "auth_failed"
    AUTH_TOKEN_REFRESH = "auth_token_refresh"
    AUTH_API_KEY_CREATED = "auth_api_key_created"
    AUTH_API_KEY_REVOKED = "auth_api_key_revoked"

    # Sessions
    SESSION_CREATED = "session_created"
    SESSION_CLOSED = "session_closed"
    SESSION_ERROR = "session_error"
    SESSION_STATS = "session_stats"

    # Configuration
    CONFIG_CHANGED = "config_changed"
    CONFIG_VALIDATED = "config_validated"

    # Security
    VALIDATION_FAILED = "validation_failed"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    ENCRYPTION_ERROR = "encryption_error"

    # Errors
    ERROR_OCCURRED = "error_occurred"


class AuditSeverity(str, Enum):
    """Audit event severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event record."""
    event_type: AuditEventType
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    severity: AuditSeverity
    description: str
    details: Dict[str, Any]
    source_ip: Optional[str] = None


class AuditLogger:
    """Log audit events."""

    def __init__(self, max_events: int = 10000):
        self.events: list[AuditEvent] = []
        self.max_events = max_events

    def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        description: str = "",
        details: Optional[Dict[str, Any]] = None,
        source_ip: Optional[str] = None,
    ) -> AuditEvent:
        """Log an audit event."""
        if details is None:
            details = {}

        event = AuditEvent(
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            session_id=session_id,
            severity=severity,
            description=description,
            details=details,
            source_ip=source_ip,
        )

        self.events.append(event)

        # Keep only recent events
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events :]

        # Log to logger as well
        self._log_to_logger(event)

        return event

    def log_auth_login(
        self,
        user_id: str,
        username: str,
        source_ip: Optional[str] = None,
    ):
        """Log successful login."""
        self.log_event(
            AuditEventType.AUTH_LOGIN,
            user_id=user_id,
            severity=AuditSeverity.INFO,
            description=f"User {username} logged in",
            details={"username": username},
            source_ip=source_ip,
        )

    def log_auth_failed(
        self,
        username: Optional[str],
        reason: str,
        source_ip: Optional[str] = None,
    ):
        """Log failed authentication attempt."""
        self.log_event(
            AuditEventType.AUTH_FAILED,
            severity=AuditSeverity.WARNING,
            description=f"Authentication failed: {reason}",
            details={"username": username, "reason": reason},
            source_ip=source_ip,
        )

    def log_session_created(
        self,
        session_id: str,
        user_id: str,
        source_url: str,
    ):
        """Log session creation."""
        self.log_event(
            AuditEventType.SESSION_CREATED,
            user_id=user_id,
            session_id=session_id,
            severity=AuditSeverity.INFO,
            description=f"Session {session_id} created",
            details={"source_url": source_url},
        )

    def log_session_closed(
        self,
        session_id: str,
        user_id: Optional[str],
        frames_processed: int,
    ):
        """Log session closure."""
        self.log_event(
            AuditEventType.SESSION_CLOSED,
            user_id=user_id,
            session_id=session_id,
            severity=AuditSeverity.INFO,
            description=f"Session {session_id} closed",
            details={"frames_processed": frames_processed},
        )

    def log_validation_failed(
        self,
        reason: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Log validation failure."""
        if details is None:
            details = {}

        self.log_event(
            AuditEventType.VALIDATION_FAILED,
            user_id=user_id,
            severity=AuditSeverity.WARNING,
            description=f"Validation failed: {reason}",
            details=details,
        )

    def log_rate_limit_exceeded(
        self,
        user_id: Optional[str],
        source_ip: Optional[str] = None,
    ):
        """Log rate limit exceeded."""
        self.log_event(
            AuditEventType.RATE_LIMIT_EXCEEDED,
            user_id=user_id,
            severity=AuditSeverity.WARNING,
            description="Rate limit exceeded",
            source_ip=source_ip,
        )

    def log_error(
        self,
        error_type: str,
        error_message: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """Log error event."""
        self.log_event(
            AuditEventType.ERROR_OCCURRED,
            user_id=user_id,
            session_id=session_id,
            severity=AuditSeverity.ERROR,
            description=f"Error: {error_type}",
            details={"error_message": error_message},
        )

    def get_events(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Query audit events."""
        results = self.events

        if user_id:
            results = [e for e in results if e.user_id == user_id]

        if session_id:
            results = [e for e in results if e.session_id == session_id]

        if event_type:
            results = [e for e in results if e.event_type == event_type]

        # Return most recent first
        return list(reversed(results[-limit :]))

    def export_json(self, events: Optional[list[AuditEvent]] = None) -> str:
        """Export events as JSON."""
        if events is None:
            events = self.events

        data = [
            {
                "event_type": e.event_type.value,
                "timestamp": e.timestamp.isoformat(),
                "user_id": e.user_id,
                "session_id": e.session_id,
                "severity": e.severity.value,
                "description": e.description,
                "details": e.details,
                "source_ip": e.source_ip,
            }
            for e in events
        ]

        return json.dumps(data, indent=2)

    def _log_to_logger(self, event: AuditEvent):
        """Log event to standard logger."""
        level = {
            AuditSeverity.INFO: logging.INFO,
            AuditSeverity.WARNING: logging.WARNING,
            AuditSeverity.ERROR: logging.ERROR,
            AuditSeverity.CRITICAL: logging.CRITICAL,
        }[event.severity]

        msg = (
            f"[AUDIT] {event.event_type.value} | "
            f"user={event.user_id} session={event.session_id} | "
            f"{event.description}"
        )

        logger.log(level, msg)


# Global audit logger
audit_logger = AuditLogger()
