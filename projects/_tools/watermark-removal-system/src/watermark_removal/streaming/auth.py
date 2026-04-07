"""
Authentication and authorization for streaming API.

Supports Bearer token validation, API key verification, and HMAC-based webhook signatures.
"""

import hashlib
import hmac
import logging
from typing import Optional
from datetime import datetime, timedelta

from fastapi import HTTPException, Header, status

logger = logging.getLogger(__name__)


class APIKeyManager:
    """Manage API keys for streaming API access."""

    def __init__(self, valid_keys: Optional[list[str]] = None):
        """
        Initialize API key manager.

        Args:
            valid_keys: List of valid API keys. If None, uses default test key.
        """
        # Default test key (should be replaced in production)
        self.valid_keys = valid_keys or ["sk-test-watermark-removal-phase-3"]
        logger.info(f"APIKeyManager initialized with {len(self.valid_keys)} key(s)")

    def validate_key(self, api_key: str) -> bool:
        """
        Validate an API key.

        Args:
            api_key: API key to validate

        Returns:
            True if valid, False otherwise
        """
        if api_key in self.valid_keys:
            return True
        logger.warning(f"Invalid API key attempt: {api_key[:10]}...")
        return False


class BearerTokenManager:
    """Manage Bearer token authentication."""

    def __init__(self, valid_tokens: Optional[dict[str, str]] = None):
        """
        Initialize Bearer token manager.

        Args:
            valid_tokens: Dict mapping tokens to client identifiers.
                         If None, uses default test token.
        """
        # Default test token (should be replaced in production)
        self.valid_tokens = valid_tokens or {
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.token": "test-client"
        }
        logger.info(f"BearerTokenManager initialized with {len(self.valid_tokens)} token(s)")

    def validate_token(self, token: str) -> Optional[str]:
        """
        Validate a Bearer token.

        Args:
            token: Bearer token to validate

        Returns:
            Client identifier if valid, None otherwise
        """
        if token in self.valid_tokens:
            return self.valid_tokens[token]
        logger.warning(f"Invalid Bearer token attempt: {token[:20]}...")
        return None


class HMACSignatureValidator:
    """Validate HMAC signatures for webhook payloads."""

    def __init__(self, secret_key: str = "default-webhook-secret"):
        """
        Initialize HMAC validator.

        Args:
            secret_key: Shared secret for HMAC computation
        """
        self.secret_key = secret_key
        logger.info("HMACSignatureValidator initialized")

    def compute_signature(self, payload: bytes, timestamp: str) -> str:
        """
        Compute HMAC signature for payload.

        Args:
            payload: Raw payload bytes
            timestamp: Timestamp string (typically ISO format)

        Returns:
            Hex-encoded HMAC signature
        """
        message = f"{timestamp}.{payload.decode('utf-8', errors='ignore')}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def validate_signature(
        self,
        payload: bytes,
        timestamp: str,
        signature: str,
        tolerance_sec: int = 300,
    ) -> bool:
        """
        Validate webhook signature.

        Args:
            payload: Raw payload bytes
            timestamp: Timestamp from header
            signature: Expected signature from header
            tolerance_sec: Max age of timestamp before rejecting (seconds)

        Returns:
            True if signature is valid and not expired, False otherwise
        """
        # Check timestamp freshness
        try:
            ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            age = (datetime.utcnow() - ts.replace(tzinfo=None)).total_seconds()

            if age > tolerance_sec:
                logger.warning(f"Webhook timestamp too old: {age:.1f}s > {tolerance_sec}s")
                return False

        except ValueError:
            logger.warning(f"Invalid timestamp format: {timestamp}")
            return False

        # Compute expected signature
        expected_sig = self.compute_signature(payload, timestamp)

        # Constant-time comparison to prevent timing attacks
        valid = hmac.compare_digest(expected_sig, signature)

        if not valid:
            logger.warning(
                f"HMAC signature mismatch (payload age: {age:.1f}s)"
            )

        return valid


class RateLimiter:
    """Simple in-memory rate limiter for API endpoints."""

    def __init__(self, requests_per_minute: int = 60):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Max requests per minute per client
        """
        self.requests_per_minute = requests_per_minute
        self.client_requests: dict[str, list[datetime]] = {}
        logger.info(f"RateLimiter initialized: {requests_per_minute} req/min")

    def is_allowed(self, client_id: str) -> bool:
        """
        Check if client is allowed to make a request.

        Args:
            client_id: Unique client identifier

        Returns:
            True if request allowed, False if rate limit exceeded
        """
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)

        # Get client requests from past minute
        if client_id not in self.client_requests:
            self.client_requests[client_id] = []

        # Remove old requests
        self.client_requests[client_id] = [
            req_time
            for req_time in self.client_requests[client_id]
            if req_time > one_minute_ago
        ]

        # Check rate limit
        if len(self.client_requests[client_id]) >= self.requests_per_minute:
            logger.warning(
                f"Rate limit exceeded for client {client_id}: "
                f"{len(self.client_requests[client_id])}/{self.requests_per_minute} req/min"
            )
            return False

        # Record request
        self.client_requests[client_id].append(now)
        return True

    def get_request_count(self, client_id: str) -> int:
        """Get current request count for client in past minute."""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)

        if client_id not in self.client_requests:
            return 0

        count = len(
            [
                req_time
                for req_time in self.client_requests[client_id]
                if req_time > one_minute_ago
            ]
        )
        return count

    def cleanup_old_entries(self):
        """Remove old client entries to prevent memory growth."""
        now = datetime.now()
        five_minutes_ago = now - timedelta(minutes=5)

        clients_to_remove = []
        for client_id, requests in self.client_requests.items():
            # Keep only if client has recent requests
            recent = [r for r in requests if r > five_minutes_ago]
            if not recent:
                clients_to_remove.append(client_id)

        for client_id in clients_to_remove:
            del self.client_requests[client_id]

        if clients_to_remove:
            logger.debug(f"Cleaned up {len(clients_to_remove)} inactive client(s)")


# Global instances (should be injected in production)
api_key_manager = APIKeyManager()
bearer_token_manager = BearerTokenManager()
hmac_validator = HMACSignatureValidator()
rate_limiter = RateLimiter(requests_per_minute=100)


# FastAPI dependency functions
async def verify_api_key(x_api_key: str = Header(...)) -> str:
    """
    FastAPI dependency for API key verification.

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        Validated API key

    Raises:
        HTTPException: If API key is invalid
    """
    if not api_key_manager.validate_key(x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return x_api_key


async def verify_bearer_token(authorization: str = Header(...)) -> str:
    """
    FastAPI dependency for Bearer token verification.

    Args:
        authorization: Authorization header (format: "Bearer <token>")

    Returns:
        Validated client identifier

    Raises:
        HTTPException: If Bearer token is invalid
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization[7:]  # Remove "Bearer " prefix
    client_id = bearer_token_manager.validate_token(token)

    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return client_id


async def check_rate_limit(client_id: str) -> bool:
    """
    FastAPI dependency for rate limit checking.

    Args:
        client_id: Client identifier (from token or API key)

    Returns:
        True if request allowed

    Raises:
        HTTPException: If rate limit exceeded
    """
    if not rate_limiter.is_allowed(client_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded: maximum 100 requests per minute",
        )

    return True
