"""
Authentication and authorization for streaming API.

Supports JWT tokens, API keys, and role-based access control.
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from enum import Enum
import json
import base64

from pydantic import BaseModel

# Try to import python-jose, fall back to simple implementation
try:
    from jose import JWTError, jwt as jose_jwt
    HAS_JOSE = True
except ImportError:
    HAS_JOSE = False
    JWTError = Exception  # Fallback exception

logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = "your-secret-key-change-in-production"  # Should be in env var
ALGORITHM = "HS256"
TOKEN_EXPIRATION_MINUTES = 30


class UserRole(str, Enum):
    """User role types."""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class TokenData(BaseModel):
    """JWT token payload."""
    user_id: str
    username: str
    roles: List[UserRole]
    exp: datetime


class APIKey(BaseModel):
    """API key metadata."""
    key_id: str
    key_hash: str  # bcrypt or argon2 hash
    user_id: str
    roles: List[UserRole]
    created_at: datetime
    last_used: Optional[datetime] = None
    revoked: bool = False


class JWTAuthenticator:
    """JWT token management."""

    @staticmethod
    def create_access_token(
        user_id: str,
        username: str,
        roles: List[UserRole],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create JWT access token.

        Args:
            user_id: User identifier
            username: Username
            roles: User roles
            expires_delta: Token expiration time

        Returns:
            Encoded JWT token
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=TOKEN_EXPIRATION_MINUTES)

        expire = datetime.now(timezone.utc) + expires_delta

        payload = {
            "user_id": user_id,
            "username": username,
            "roles": [r.value for r in roles],
            "exp": expire.timestamp(),
        }

        if HAS_JOSE:
            encoded_jwt = jose_jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        else:
            # Fallback: simple JWT implementation (not secure, for testing only)
            header = base64.urlsafe_b64encode(
                json.dumps({"alg": ALGORITHM}).encode()
            ).rstrip(b"=")
            body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=")
            signature = base64.urlsafe_b64encode(
                SECRET_KEY.encode()[:32]
            ).rstrip(b"=")
            encoded_jwt = (header + b"." + body + b"." + signature).decode()

        logger.info(f"Created token for user {username}")
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[TokenData]:
        """
        Verify and decode JWT token.

        Args:
            token: JWT token string

        Returns:
            TokenData if valid, None otherwise
        """
        try:
            if HAS_JOSE:
                payload = jose_jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            else:
                # Fallback: simple JWT verification
                parts = token.split(".")
                if len(parts) != 3:
                    return None
                body = parts[1]
                # Add padding if needed
                padding = 4 - (len(body) % 4)
                if padding != 4:
                    body += "=" * padding
                payload = json.loads(base64.urlsafe_b64decode(body))

            user_id = payload.get("user_id")
            username = payload.get("username")
            roles_str = payload.get("roles", [])
            roles = [UserRole(r) for r in roles_str]
            exp = datetime.fromtimestamp(payload.get("exp"), tz=timezone.utc)

            if not all([user_id, username]):
                return None

            token_data = TokenData(
                user_id=user_id,
                username=username,
                roles=roles,
                exp=exp,
            )

            return token_data

        except (JWTError, KeyError, ValueError, json.JSONDecodeError) as e:
            logger.warning(f"Invalid token: {e}")
            return None

    @staticmethod
    def is_token_expired(token_data: TokenData) -> bool:
        """Check if token is expired."""
        return datetime.now(timezone.utc) > token_data.exp


class APIKeyManager:
    """API key management."""

    def __init__(self):
        self.api_keys: dict[str, APIKey] = {}
        self.key_lookup: dict[str, str] = {}  # key -> key_id mapping

    def generate_api_key(
        self,
        user_id: str,
        roles: List[UserRole],
    ) -> tuple[str, APIKey]:
        """
        Generate new API key.

        Args:
            user_id: User identifier
            roles: User roles

        Returns:
            (raw_key, api_key_metadata) tuple
        """
        # Generate random key
        raw_key = secrets.token_urlsafe(32)

        # Hash key (in production, use bcrypt or argon2)
        key_hash = self._hash_key(raw_key)
        key_id = self._generate_key_id()

        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            user_id=user_id,
            roles=roles,
            created_at=datetime.now(timezone.utc),
            revoked=False,
        )

        self.api_keys[key_id] = api_key
        self.key_lookup[raw_key] = key_id

        logger.info(f"Generated API key {key_id} for user {user_id}")
        return raw_key, api_key

    def verify_api_key(self, raw_key: str) -> Optional[APIKey]:
        """
        Verify API key and return metadata.

        Args:
            raw_key: Raw API key string

        Returns:
            APIKey metadata if valid, None otherwise
        """
        if raw_key not in self.key_lookup:
            logger.warning(f"API key not found")
            return None

        key_id = self.key_lookup[raw_key]
        api_key = self.api_keys.get(key_id)

        if api_key is None or api_key.revoked:
            logger.warning(f"API key {key_id} is invalid or revoked")
            return None

        # Update last_used timestamp
        api_key.last_used = datetime.now(timezone.utc)
        logger.debug(f"API key {key_id} verified")

        return api_key

    def revoke_api_key(self, key_id: str) -> bool:
        """
        Revoke API key.

        Args:
            key_id: Key identifier

        Returns:
            True if revoked, False if not found
        """
        if key_id not in self.api_keys:
            logger.warning(f"API key {key_id} not found")
            return False

        self.api_keys[key_id].revoked = True
        logger.info(f"Revoked API key {key_id}")
        return True

    def list_api_keys(self, user_id: str) -> List[APIKey]:
        """List all API keys for user (excluding revoked)."""
        return [
            key
            for key in self.api_keys.values()
            if key.user_id == user_id and not key.revoked
        ]

    def _hash_key(self, key: str) -> str:
        """Hash API key (simplified - use bcrypt in production)."""
        import hashlib

        return hashlib.sha256(key.encode()).hexdigest()

    def _generate_key_id(self) -> str:
        """Generate unique key ID."""
        while True:
            key_id = f"key_{secrets.token_hex(8)}"
            if key_id not in self.api_keys:
                return key_id


class AuthorizationChecker:
    """Check user permissions."""

    @staticmethod
    def has_role(token_data: TokenData, required_role: UserRole) -> bool:
        """Check if user has required role."""
        return required_role in token_data.roles

    @staticmethod
    def has_any_role(token_data: TokenData, required_roles: List[UserRole]) -> bool:
        """Check if user has any of required roles."""
        return any(role in token_data.roles for role in required_roles)

    @staticmethod
    def has_all_roles(token_data: TokenData, required_roles: List[UserRole]) -> bool:
        """Check if user has all required roles."""
        return all(role in token_data.roles for role in required_roles)


# Global instances
jwt_authenticator = JWTAuthenticator()
api_key_manager = APIKeyManager()
auth_checker = AuthorizationChecker()
