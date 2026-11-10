import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.core.logging import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """
    Hashes password securely using SHA-256 with salt.
    """
    salt = settings.SECRET_KEY[:16].encode("utf-8")
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000).hex()


# Alias for compatibility
get_password_hash = hash_password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies plain password against hashed password.
    """
    return hmac.compare_digest(hash_password(plain_password), hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Generates a secure JWT access token.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=1)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodes and verifies JWT token signature and expiration.
    Returns decoded token payload dictionary if valid, else None.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError as e:
        logger.warning(f"Failed to decode token: {str(e)}")
        return None


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[Dict[str, Any]]:
    """
    Dependency that optionally extracts the authenticated user payload if a Bearer token is provided.
    Returns None if no token is provided, preserving backwards-compatibility with unauthenticated workflows.
    """
    if not token:
        return None
    return decode_access_token(token)


async def get_current_user_required(
    token: Optional[str] = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    """
    Dependency enforcing strict authentication. Raises HTTP 401 if token is missing or invalid.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is required for this operation.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return payload
