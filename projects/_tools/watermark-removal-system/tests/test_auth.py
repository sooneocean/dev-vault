"""
Tests for authentication and authorization (streaming auth module).

Covers:
- API key validation
- Bearer token validation
- HMAC signature validation
- Rate limiting
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from src.watermark_removal.streaming.auth import (
    APIKeyManager,
    BearerTokenManager,
    HMACSignatureValidator,
    RateLimiter,
)
from src.watermark_removal.streaming.server import app


class TestAPIKeyManager:
    """Tests for API key management."""

    def test_init_default_keys(self):
        """Test initialization with default test key."""
        manager = APIKeyManager()
        assert len(manager.valid_keys) > 0

    def test_init_custom_keys(self):
        """Test initialization with custom keys."""
        custom_keys = ["key1", "key2", "key3"]
        manager = APIKeyManager(valid_keys=custom_keys)
        assert manager.valid_keys == custom_keys

    def test_validate_key_valid(self):
        """Test validation of valid API key."""
        manager = APIKeyManager(valid_keys=["test-key-123"])
        assert manager.validate_key("test-key-123") is True

    def test_validate_key_invalid(self):
        """Test validation of invalid API key."""
        manager = APIKeyManager(valid_keys=["test-key-123"])
        assert manager.validate_key("invalid-key") is False

    def test_validate_key_empty(self):
        """Test validation with empty key."""
        manager = APIKeyManager(valid_keys=["test-key-123"])
        assert manager.validate_key("") is False


class TestBearerTokenManager:
    """Tests for Bearer token management."""

    def test_init_default_tokens(self):
        """Test initialization with default test token."""
        manager = BearerTokenManager()
        assert len(manager.valid_tokens) > 0

    def test_init_custom_tokens(self):
        """Test initialization with custom tokens."""
        custom_tokens = {"token1": "client1", "token2": "client2"}
        manager = BearerTokenManager(valid_tokens=custom_tokens)
        assert manager.valid_tokens == custom_tokens

    def test_validate_token_valid(self):
        """Test validation of valid Bearer token."""
        manager = BearerTokenManager(valid_tokens={"token-123": "client-id"})
        client_id = manager.validate_token("token-123")
        assert client_id == "client-id"

    def test_validate_token_invalid(self):
        """Test validation of invalid Bearer token."""
        manager = BearerTokenManager(valid_tokens={"token-123": "client-id"})
        assert manager.validate_token("invalid-token") is None

    def test_validate_token_empty(self):
        """Test validation with empty token."""
        manager = BearerTokenManager(valid_tokens={"token-123": "client-id"})
        assert manager.validate_token("") is None


class TestHMACSignatureValidator:
    """Tests for HMAC signature validation."""

    def test_init_default_secret(self):
        """Test initialization with default secret."""
        validator = HMACSignatureValidator()
        assert validator.secret_key is not None

    def test_init_custom_secret(self):
        """Test initialization with custom secret."""
        validator = HMACSignatureValidator(secret_key="custom-secret")
        assert validator.secret_key == "custom-secret"

    def test_compute_signature(self):
        """Test signature computation."""
        validator = HMACSignatureValidator(secret_key="test-secret")
        timestamp = "2026-03-31T12:00:00Z"
        payload = b"test-payload"

        signature = validator.compute_signature(payload, timestamp)

        # Signature should be hex string
        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex digest is 64 chars

    def test_validate_signature_valid(self):
        """Test signature validation with valid signature."""
        validator = HMACSignatureValidator(secret_key="test-secret")
        timestamp = datetime.now().isoformat() + "Z"
        payload = b"test-payload"

        # Compute expected signature
        signature = validator.compute_signature(payload, timestamp)

        # Validate should return True
        assert validator.validate_signature(payload, timestamp, signature) is True

    def test_validate_signature_invalid(self):
        """Test signature validation with invalid signature."""
        validator = HMACSignatureValidator(secret_key="test-secret")
        timestamp = datetime.now().isoformat() + "Z"
        payload = b"test-payload"

        # Use wrong signature
        assert validator.validate_signature(payload, timestamp, "wrong-signature") is False

    def test_validate_signature_expired_timestamp(self):
        """Test signature validation with expired timestamp."""
        validator = HMACSignatureValidator(secret_key="test-secret")

        # Create old timestamp (older than tolerance)
        old_timestamp = (datetime.utcnow() - timedelta(minutes=6)).isoformat() + "Z"
        payload = b"test-payload"
        signature = validator.compute_signature(payload, old_timestamp)

        # Should reject because timestamp is too old (default 300s)
        assert validator.validate_signature(
            payload, old_timestamp, signature, tolerance_sec=300
        ) is False

    def test_validate_signature_invalid_timestamp_format(self):
        """Test signature validation with invalid timestamp format."""
        validator = HMACSignatureValidator(secret_key="test-secret")
        payload = b"test-payload"
        signature = "fake-signature"

        # Invalid timestamp format should return False
        assert validator.validate_signature(payload, "invalid-date", signature) is False

    def test_compute_signature_deterministic(self):
        """Test that signature computation is deterministic."""
        validator = HMACSignatureValidator(secret_key="test-secret")
        timestamp = "2026-03-31T12:00:00Z"
        payload = b"test-payload"

        sig1 = validator.compute_signature(payload, timestamp)
        sig2 = validator.compute_signature(payload, timestamp)

        assert sig1 == sig2


class TestRateLimiter:
    """Tests for rate limiting."""

    def test_init_default_rate(self):
        """Test initialization with default rate."""
        limiter = RateLimiter()
        assert limiter.requests_per_minute == 60

    def test_init_custom_rate(self):
        """Test initialization with custom rate."""
        limiter = RateLimiter(requests_per_minute=30)
        assert limiter.requests_per_minute == 30

    def test_is_allowed_single_request(self):
        """Test single request is allowed."""
        limiter = RateLimiter(requests_per_minute=10)
        assert limiter.is_allowed("client-1") is True

    def test_is_allowed_within_limit(self):
        """Test requests within limit are allowed."""
        limiter = RateLimiter(requests_per_minute=5)
        client_id = "client-1"

        for i in range(5):
            assert limiter.is_allowed(client_id) is True

    def test_is_allowed_exceeds_limit(self):
        """Test request exceeding limit is rejected."""
        limiter = RateLimiter(requests_per_minute=3)
        client_id = "client-1"

        # Use up limit
        for i in range(3):
            limiter.is_allowed(client_id)

        # Next request should be rejected
        assert limiter.is_allowed(client_id) is False

    def test_is_allowed_multiple_clients(self):
        """Test rate limit is per-client."""
        limiter = RateLimiter(requests_per_minute=2)

        # Client 1 uses up limit
        limiter.is_allowed("client-1")
        limiter.is_allowed("client-1")

        # Client 2 should still be allowed
        assert limiter.is_allowed("client-2") is True

    def test_get_request_count(self):
        """Test getting request count for client."""
        limiter = RateLimiter()
        client_id = "client-1"

        assert limiter.get_request_count(client_id) == 0

        limiter.is_allowed(client_id)
        assert limiter.get_request_count(client_id) == 1

        limiter.is_allowed(client_id)
        assert limiter.get_request_count(client_id) == 2

    def test_cleanup_old_entries(self):
        """Test cleanup of old client entries."""
        limiter = RateLimiter(requests_per_minute=10)

        # Add requests from old client
        limiter.is_allowed("old-client")

        # Verify entry exists
        assert "old-client" in limiter.client_requests

        # Cleanup (entries older than 5 minutes are removed)
        # Since we just added, it won't be removed
        limiter.cleanup_old_entries()
        assert "old-client" in limiter.client_requests


class TestFastAPIAuthentication:
    """Tests for FastAPI authentication integration."""

    def test_health_check_no_auth(self):
        """Test /health endpoint requires no authentication."""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_stream_start_no_auth(self):
        """Test /stream/start endpoint requires authentication."""
        client = TestClient(app)
        response = client.post("/stream/start", json={})

        # Should fail without auth
        assert response.status_code == 401
        assert "Missing authentication" in response.json()["detail"]

    def test_stream_start_with_api_key(self):
        """Test /stream/start with API key authentication."""
        client = TestClient(app)
        headers = {"X-API-Key": "sk-test-watermark-removal-phase-3"}
        response = client.post("/stream/start", json={}, headers=headers)

        # Should succeed with valid API key
        assert response.status_code == 200
        assert "session_id" in response.json()

    def test_stream_start_with_invalid_api_key(self):
        """Test /stream/start with invalid API key."""
        client = TestClient(app)
        headers = {"X-API-Key": "invalid-key"}
        response = client.post("/stream/start", json={}, headers=headers)

        # Should fail with invalid API key
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

    def test_stream_start_with_bearer_token(self):
        """Test /stream/start with Bearer token."""
        client = TestClient(app)
        headers = {
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.token"
        }
        response = client.post("/stream/start", json={}, headers=headers)

        # Should succeed with valid Bearer token
        assert response.status_code == 200
        assert "session_id" in response.json()

    def test_stream_start_with_invalid_bearer_token(self):
        """Test /stream/start with invalid Bearer token."""
        client = TestClient(app)
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.post("/stream/start", json={}, headers=headers)

        # Should fail with invalid Bearer token
        assert response.status_code == 401
        assert "Invalid or expired" in response.json()["detail"]

    def test_stream_start_malformed_auth_header(self):
        """Test /stream/start with malformed Authorization header."""
        client = TestClient(app)
        headers = {"Authorization": "InvalidFormat token"}
        response = client.post("/stream/start", json={}, headers=headers)

        # Should fail with malformed header
        assert response.status_code == 401
        assert "Invalid authorization header" in response.json()["detail"]

    def test_cors_headers(self):
        """Test CORS headers are present."""
        client = TestClient(app)
        response = client.get("/health", headers={"Origin": "http://localhost"})

        # CORS headers should be present (only sent when Origin header is included)
        assert "access-control-allow-origin" in response.headers


class TestWebhookValidation:
    """Tests for webhook endpoint signature validation."""

    def test_webhook_no_signature(self):
        """Test webhook without signature is rejected."""
        client = TestClient(app)
        response = client.post(
            "/webhook/stream-event",
            json={"event_type": "stream_ready"},
        )

        # Should fail without signature headers
        assert response.status_code == 422  # FastAPI validation error

    def test_webhook_invalid_signature(self):
        """Test webhook with invalid signature is rejected."""
        client = TestClient(app)
        timestamp = datetime.now().isoformat() + "Z"
        headers = {
            "X-Webhook-Signature": "invalid-signature",
            "X-Webhook-Timestamp": timestamp,
        }
        response = client.post(
            "/webhook/stream-event",
            json={"event_type": "stream_ready"},
            headers=headers,
        )

        # Should fail with invalid signature
        assert response.status_code == 401
        assert "Invalid webhook signature" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
