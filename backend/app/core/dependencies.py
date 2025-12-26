"""FastAPI dependencies for authentication and authorization."""
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token, hash_api_key, validate_api_key_format
from app.models import User, APIKey, Subscription


# Security scheme for JWT Bearer tokens
oauth2_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user from database
    result = await db.execute(
        select(User)
        .options(selectinload(User.subscription))
        .where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to get current active user with subscription check.
    """
    return current_user


async def get_current_subscribed_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to get current user with active subscription.
    """
    if not current_user.subscription or not current_user.subscription.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active subscription required",
        )
    
    if not current_user.subscription.can_use_api:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Current plan does not include API access. Please upgrade.",
        )
    
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to get current admin user.
    """
    # Check if is_admin attribute exists (for backward compatibility)
    is_admin = getattr(current_user, 'is_admin', False)
    
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    return current_user


async def get_api_key_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to authenticate via API key (for widget requests).
    """
    # Get API key from header
    api_key = request.headers.get("X-API-Key")
    
    if not api_key:
        # Also check query parameter as fallback
        api_key = request.query_params.get("api_key")
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )
    
    # Validate format
    if not validate_api_key_format(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
        )
    
    # Hash and lookup
    key_hash = hash_api_key(api_key)
    
    result = await db.execute(
        select(APIKey)
        .options(
            selectinload(APIKey.user).selectinload(User.subscription)
        )
        .where(APIKey.key_hash == key_hash)
    )
    api_key_obj = result.scalar_one_or_none()
    
    if not api_key_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    
    if not api_key_obj.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has been revoked",
        )
    
    if not api_key_obj.user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )
    
    # Update last used timestamp
    from datetime import datetime
    api_key_obj.last_used_at = datetime.utcnow()
    api_key_obj.usage_count += 1
    await db.commit()
    
    return api_key_obj.user


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    # Check for forwarded IP (behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to client host
    if request.client:
        return request.client.host
    
    return "unknown"

