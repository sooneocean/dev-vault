"""
Unit tests for security modules.

Tests authentication, validation, encryption, and audit logging.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from src.security.auth import (
    JWTAuthenticator,
    APIKeyManager,
    AuthorizationChecker,
    UserRole,
    TokenData,
)
from src.security.validation import (
    SourceValidator,
    FormatValidator,
    ConfigValidator,
    RateLimiter,
    ValidationError,
)
from src.security.encryption import (
    KeyManager,
    DataEncryptor,
    PII,
)
from src.security.audit import (
    AuditLogger,
    AuditEventType,
    AuditSeverity,
)


# ============= Authentication Tests =============


class TestJWTAuthenticator:
    """Test JWT token management."""

    def test_create_access_token(self):
        """Create valid JWT token."""
        token = JWTAuthenticator.create_access_token(
            user_id="user123",
            username="testuser",
            roles=[UserRole.USER],
        )

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_valid_token(self):
        """Verify valid token."""
        token = JWTAuthenticator.create_access_token(
            user_id="user123",
            username="testuser",
            roles=[UserRole.USER],
        )

        token_data = JWTAuthenticator.verify_token(token)

        assert token_data is not None
        assert token_data.user_id == "user123"
        assert token_data.username == "testuser"
        assert UserRole.USER in token_data.roles

    def test_verify_invalid_token(self):
        """Verify invalid token returns None."""
        result = JWTAuthenticator.verify_token("invalid.token.here")
        assert result is None

    def test_token_expiration(self):
        """Token expires after expiration time."""
        token = JWTAuthenticator.create_access_token(
            user_id="user123",
            username="testuser",
            roles=[UserRole.USER],
            expires_delta=timedelta(seconds=0),  # Expire immediately
        )

        import time

        time.sleep(0.1)
        token_data = JWTAuthenticator.verify_token(token)

        # Token should still verify but be marked as expired
        if token_data:
            assert JWTAuthenticator.is_token_expired(token_data)

    def test_multiple_roles_in_token(self):
        """Token can contain multiple roles."""
        token = JWTAuthenticator.create_access_token(
            user_id="user123",
            username="testuser",
            roles=[UserRole.USER, UserRole.ADMIN],
        )

        token_data = JWTAuthenticator.verify_token(token)

        assert token_data is not None
        assert len(token_data.roles) == 2
        assert UserRole.ADMIN in token_data.roles


class TestAPIKeyManager:
    """Test API key management."""

    def test_generate_api_key(self):
        """Generate new API key."""
        manager = APIKeyManager()

        raw_key, api_key = manager.generate_api_key(
            user_id="user123",
            roles=[UserRole.USER],
        )

        assert raw_key is not None
        assert len(raw_key) > 0
        assert api_key.user_id == "user123"
        assert api_key.revoked is False

    def test_verify_api_key(self):
        """Verify API key."""
        manager = APIKeyManager()

        raw_key, api_key = manager.generate_api_key(
            user_id="user123",
            roles=[UserRole.USER],
        )

        verified = manager.verify_api_key(raw_key)

        assert verified is not None
        assert verified.user_id == "user123"

    def test_verify_invalid_api_key(self):
        """Verify invalid key returns None."""
        manager = APIKeyManager()

        result = manager.verify_api_key("invalid_key")

        assert result is None

    def test_revoke_api_key(self):
        """Revoke API key."""
        manager = APIKeyManager()

        raw_key, api_key = manager.generate_api_key(
            user_id="user123",
            roles=[UserRole.USER],
        )

        # Revoke
        result = manager.revoke_api_key(api_key.key_id)
        assert result is True

        # Verify should fail
        verified = manager.verify_api_key(raw_key)
        assert verified is None

    def test_list_api_keys(self):
        """List user's API keys."""
        manager = APIKeyManager()

        raw_key1, _ = manager.generate_api_key(
            user_id="user123",
            roles=[UserRole.USER],
        )
        raw_key2, _ = manager.generate_api_key(
            user_id="user123",
            roles=[UserRole.VIEWER],
        )

        keys = manager.list_api_keys("user123")

        assert len(keys) == 2
        assert all(k.user_id == "user123" for k in keys)
        assert all(not k.revoked for k in keys)


class TestAuthorizationChecker:
    """Test authorization checking."""

    def test_has_role(self):
        """Check if user has specific role."""
        token_data = TokenData(
            user_id="user123",
            username="testuser",
            roles=[UserRole.USER],
            exp=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        assert AuthorizationChecker.has_role(token_data, UserRole.USER)
        assert not AuthorizationChecker.has_role(token_data, UserRole.ADMIN)

    def test_has_any_role(self):
        """Check if user has any of required roles."""
        token_data = TokenData(
            user_id="user123",
            username="testuser",
            roles=[UserRole.USER],
            exp=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        assert AuthorizationChecker.has_any_role(
            token_data, [UserRole.ADMIN, UserRole.USER]
        )
        assert not AuthorizationChecker.has_any_role(token_data, [UserRole.ADMIN])

    def test_has_all_roles(self):
        """Check if user has all required roles."""
        token_data = TokenData(
            user_id="user123",
            username="testuser",
            roles=[UserRole.ADMIN, UserRole.USER],
            exp=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        assert AuthorizationChecker.has_all_roles(
            token_data, [UserRole.ADMIN, UserRole.USER]
        )
        assert AuthorizationChecker.has_all_roles(token_data, [UserRole.ADMIN])
        assert not AuthorizationChecker.has_all_roles(token_data, [UserRole.VIEWER])


# ============= Validation Tests =============


class TestSourceValidator:
    """Test source URL validation."""

    def test_validate_valid_file_url(self):
        """Validate file:// URL."""
        result = SourceValidator.validate_source_url("file:///test/video.mp4")
        assert result is True

    def test_validate_rtmp_url(self):
        """Validate RTMP URL."""
        result = SourceValidator.validate_source_url("rtmp://example.com/live/stream")
        assert result is True

    def test_validate_rtsp_url(self):
        """Validate RTSP URL."""
        result = SourceValidator.validate_source_url("rtsp://camera.example.com/stream")
        assert result is True

    def test_validate_empty_url(self):
        """Reject empty URL."""
        with pytest.raises(ValidationError):
            SourceValidator.validate_source_url("")

    def test_validate_dangerous_path(self):
        """Reject paths with dangerous patterns."""
        with pytest.raises(ValidationError):
            SourceValidator.validate_source_url("file://../../../etc/passwd")

    def test_validate_invalid_format(self):
        """Reject unsupported file formats."""
        with pytest.raises(ValidationError):
            SourceValidator.validate_source_url("/video.txt")

    def test_validate_too_long_url(self):
        """Reject excessively long URLs."""
        long_url = "file:///" + "a" * 3000
        with pytest.raises(ValidationError):
            SourceValidator.validate_source_url(long_url)


class TestFormatValidator:
    """Test format validation."""

    def test_validate_valid_output_format(self):
        """Validate supported output format."""
        assert FormatValidator.validate_output_format("h264") is True
        assert FormatValidator.validate_output_format("vp9") is True
        assert FormatValidator.validate_output_format("av1") is True
        assert FormatValidator.validate_output_format("hevc") is True

    def test_validate_invalid_output_format(self):
        """Reject unsupported format."""
        with pytest.raises(ValidationError):
            FormatValidator.validate_output_format("invalid")

    def test_validate_valid_preset(self):
        """Validate quality presets."""
        assert FormatValidator.validate_quality_preset("fast") is True
        assert FormatValidator.validate_quality_preset("balanced") is True
        assert FormatValidator.validate_quality_preset("quality") is True

    def test_validate_invalid_preset(self):
        """Reject invalid preset."""
        with pytest.raises(ValidationError):
            FormatValidator.validate_quality_preset("invalid")


class TestConfigValidator:
    """Test configuration validation."""

    def test_validate_valid_buffer_size(self):
        """Validate buffer sizes within range."""
        assert ConfigValidator.validate_buffer_size(1) is True
        assert ConfigValidator.validate_buffer_size(30) is True
        assert ConfigValidator.validate_buffer_size(300) is True

    def test_validate_invalid_buffer_size_too_small(self):
        """Reject buffer size too small."""
        with pytest.raises(ValidationError):
            ConfigValidator.validate_buffer_size(0)

    def test_validate_invalid_buffer_size_too_large(self):
        """Reject buffer size too large."""
        with pytest.raises(ValidationError):
            ConfigValidator.validate_buffer_size(301)

    def test_validate_complete_configuration(self):
        """Validate complete stream configuration."""
        result = ConfigValidator.validate_configuration(
            source_url="file:///test.mp4",
            output_format="h264",
            quality_preset="balanced",
            buffer_size=30,
        )
        assert result is True

    def test_validate_configuration_invalid_url(self):
        """Reject configuration with invalid URL."""
        with pytest.raises(ValidationError):
            ConfigValidator.validate_configuration(
                source_url="",
                output_format="h264",
                quality_preset="balanced",
                buffer_size=30,
            )


class TestRateLimiter:
    """Test rate limiting."""

    def test_rate_limiter_allows_requests(self):
        """Rate limiter allows requests within limit."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)

        for i in range(5):
            assert limiter.is_allowed("client1") is True

    def test_rate_limiter_blocks_excess_requests(self):
        """Rate limiter blocks requests exceeding limit."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client1") is False

    def test_rate_limiter_resets_per_client(self):
        """Rate limiter is per-client."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client1") is False

        # Different client should have own limit
        assert limiter.is_allowed("client2") is True
        assert limiter.is_allowed("client2") is True
        assert limiter.is_allowed("client2") is False

    def test_get_remaining_requests(self):
        """Get remaining requests."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)

        limiter.is_allowed("client1")
        limiter.is_allowed("client1")

        remaining = limiter.get_remaining("client1")
        assert remaining == 3


# ============= Encryption Tests =============


class TestKeyManager:
    """Test encryption key management."""

    def test_generate_key(self):
        """Generate encryption key."""
        from src.security.encryption import EncryptionKey

        key = EncryptionKey.generate("test_key")
        assert key is not None
        assert key.key_id == "test_key"

    def test_get_key(self):
        """Get encryption key."""
        manager = KeyManager()
        key = manager.get_key("default")
        assert key is not None

    def test_get_active_key(self):
        """Get active encryption key."""
        manager = KeyManager()
        key = manager.get_active_key()
        assert key is not None
        assert key.key_id == "default"

    def test_rotate_key(self):
        """Rotate encryption key."""
        manager = KeyManager()
        new_key = manager.get_key("default")

        # Add new key
        from src.security.encryption import EncryptionKey

        new_enc_key = EncryptionKey.generate("new_key")
        manager.add_key("new_key", new_enc_key)

        # Rotate
        result = manager.rotate_key("new_key")
        assert result is True
        assert manager.active_key_id == "new_key"


class TestDataEncryptor:
    """Test data encryption."""

    def test_encrypt_decrypt_roundtrip(self):
        """Encrypt and decrypt data."""
        manager = KeyManager()
        encryptor = DataEncryptor(manager)

        original_data = b"This is secret data"

        # Encrypt
        encrypted = encryptor.encrypt_data(original_data)
        assert encrypted is not None
        assert encrypted != original_data

        # Decrypt
        decrypted = encryptor.decrypt_data(encrypted)
        assert decrypted == original_data

    def test_encrypt_with_invalid_key(self):
        """Encryption with invalid key returns None."""
        manager = KeyManager()
        encryptor = DataEncryptor(manager)

        result = encryptor.encrypt_data(b"data", key_id="nonexistent")
        assert result is None


class TestPII:
    """Test PII redaction."""

    def test_redact_email(self):
        """Redact email addresses."""
        text = "Contact us at support@example.com for help"
        redacted = PII.redact_email(text)
        assert "support@example.com" not in redacted
        assert "[EMAIL_REDACTED]" in redacted

    def test_redact_phone(self):
        """Redact phone numbers."""
        text = "Call us at 555-123-4567 anytime"
        redacted = PII.redact_phone(text)
        assert "555-123-4567" not in redacted
        assert "[PHONE_REDACTED]" in redacted

    def test_redact_ssn(self):
        """Redact SSN."""
        text = "SSN: 123-45-6789 for record"
        redacted = PII.redact_ssn(text)
        assert "123-45-6789" not in redacted
        assert "[SSN_REDACTED]" in redacted

    def test_redact_all(self):
        """Redact all PII types."""
        text = "Email: test@example.com, Phone: 555-123-4567, SSN: 123-45-6789"
        redacted = PII.redact_all(text)

        assert "[EMAIL_REDACTED]" in redacted
        assert "[PHONE_REDACTED]" in redacted
        assert "[SSN_REDACTED]" in redacted


# ============= Audit Logging Tests =============


class TestAuditLogger:
    """Test audit logging."""

    def test_log_event(self):
        """Log audit event."""
        logger = AuditLogger()

        event = logger.log_event(
            event_type=AuditEventType.AUTH_LOGIN,
            user_id="user123",
            description="User logged in",
        )

        assert event is not None
        assert event.event_type == AuditEventType.AUTH_LOGIN
        assert event.user_id == "user123"

    def test_log_auth_login(self):
        """Log login event."""
        audit = AuditLogger()

        audit.log_auth_login("user123", "testuser", source_ip="192.168.1.1")

        events = audit.get_events(user_id="user123", event_type=AuditEventType.AUTH_LOGIN)
        assert len(events) == 1
        assert events[0].severity == AuditSeverity.INFO

    def test_log_auth_failed(self):
        """Log failed authentication."""
        audit = AuditLogger()

        audit.log_auth_failed("testuser", "Invalid credentials", source_ip="192.168.1.1")

        events = audit.get_events(event_type=AuditEventType.AUTH_FAILED)
        assert len(events) == 1
        assert events[0].severity == AuditSeverity.WARNING

    def test_log_session_created(self):
        """Log session creation."""
        audit = AuditLogger()

        audit.log_session_created("sess_123", "user123", "file:///video.mp4")

        events = audit.get_events(
            session_id="sess_123", event_type=AuditEventType.SESSION_CREATED
        )
        assert len(events) == 1

    def test_get_events_filter_by_user(self):
        """Filter events by user."""
        audit = AuditLogger()

        audit.log_auth_login("user1", "user1", source_ip="1.1.1.1")
        audit.log_auth_login("user2", "user2", source_ip="1.1.1.1")

        events = audit.get_events(user_id="user1")
        assert len(events) == 1
        assert events[0].user_id == "user1"

    def test_export_json(self):
        """Export events as JSON."""
        audit = AuditLogger()

        audit.log_auth_login("user123", "testuser", source_ip="192.168.1.1")

        json_str = audit.export_json()
        assert isinstance(json_str, str)
        assert "user123" in json_str
        assert "auth_login" in json_str

    def test_audit_events_limit(self):
        """Limit audit event storage."""
        audit = AuditLogger(max_events=10)

        # Log 15 events
        for i in range(15):
            audit.log_event(AuditEventType.SESSION_CREATED, description=f"Event {i}")

        # Should only keep last 10
        assert len(audit.events) == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
