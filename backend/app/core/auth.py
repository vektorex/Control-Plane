import time
from typing import Any, Dict, Optional
from fastapi import Depends, Header, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.core.errors import AuthenticationError, AuthorizationError
from backend.app.core.logging import logger
from backend.app.db.database import get_db
from backend.app.db.models.user import User
from backend.app.services.auth_service import AuthService

# Bearer security scheme
security_scheme = HTTPBearer(auto_error=False)

# Fallback secret for local development/testing when SUPABASE_JWT_SECRET is not set
DEV_JWT_SECRET = "dev-secret-super-safe-ai-work-layer-local-only-key-32b"


def get_jwt_secret() -> str:
    """Returns the configured Supabase JWT secret or local development fallback."""
    return settings.SUPABASE_JWT_SECRET or DEV_JWT_SECRET


def create_access_token(
    auth_user_id: str,
    email: str,
    expires_in_seconds: int = 3600,
    secret: Optional[str] = None,
    audience: Optional[str] = "authenticated",
) -> str:
    """
    Utility to create signed JWT tokens for tests, integration, and development.
    """
    signing_key = secret or get_jwt_secret()
    payload = {
        "sub": auth_user_id,
        "email": email,
        "aud": audience or "authenticated",
        "role": "authenticated",
        "iat": int(time.time()),
        "exp": int(time.time()) + expires_in_seconds,
        "app_metadata": {"provider": "email"},
        "user_metadata": {"email": email},
    }
    return jwt.encode(payload, signing_key, algorithm="HS256")


def decode_jwt_token(token: str) -> Dict[str, Any]:
    """
    Independently verifies and decodes Supabase JWT token.
    Validates signature, expiration, and required claims.
    """
    if not token or not token.strip():
        raise AuthenticationError("Authentication token is missing or empty.")

    signing_key = get_jwt_secret()

    try:
        decoded = jwt.decode(
            token,
            signing_key,
            algorithms=["HS256", "RS256", "ES256"],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": False,
            },
        )
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Authentication token has expired.")
    except (jwt.InvalidSignatureError, jwt.DecodeError, jwt.InvalidTokenError):
        raise AuthenticationError("Invalid authentication token signature.")

    # Validate essential claims
    sub = decoded.get("sub")
    if not sub:
        raise AuthenticationError("Authentication token is missing subject claim ('sub').")

    return decoded



async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency that extracts Bearer token, verifies Supabase identity,
    and returns the persistent User model (auto-provisioning workspace if first visit).
    """
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Authentication required. Please provide a valid Bearer token.")

    token = credentials.credentials
    payload = decode_jwt_token(token)

    auth_user_id = str(payload["sub"])
    email = payload.get("email") or payload.get("user_metadata", {}).get("email") or f"{auth_user_id}@user.local"

    auth_service = AuthService(session)
    user = await auth_service.get_or_create_user_with_default_workspace(
        auth_user_id=auth_user_id,
        email=email,
    )
    return user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    session: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    FastAPI dependency that returns User if Bearer token is provided and valid, otherwise None.
    """
    if credentials is None or not credentials.credentials:
        return None
    try:
        return await get_current_user(credentials=credentials, session=session)
    except Exception:
        return None
