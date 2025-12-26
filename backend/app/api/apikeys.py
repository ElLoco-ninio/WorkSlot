"""API Key management endpoints."""
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_subscribed_user, get_client_ip
from app.core.security import generate_api_key
from app.models import User, APIKey, AuditLog, AuditAction
from app.schemas import APIKeyCreate, APIKeyResponse, APIKeyCreated, APIKeyUpdate


router = APIRouter()


@router.get("", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_subscribed_user),
    db: AsyncSession = Depends(get_db),
):
    """List all API keys for the current user."""
    result = await db.execute(
        select(APIKey)
        .where(APIKey.user_id == current_user.id)
        .where(APIKey.revoked_at.is_(None))
        .order_by(APIKey.created_at.desc())
    )
    api_keys = result.scalars().all()
    return api_keys


@router.post("", response_model=APIKeyCreated, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    request: Request,
    current_user: User = Depends(get_current_subscribed_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new API key.
    
    Note: The full API key is only shown once upon creation.
    Store it securely as it cannot be retrieved later.
    """
    # Check API key limit
    result = await db.execute(
        select(func.count(APIKey.id))
        .where(APIKey.user_id == current_user.id)
        .where(APIKey.is_active == True)
        .where(APIKey.revoked_at.is_(None))
    )
    current_count = result.scalar() or 0
    limit = current_user.subscription.get_api_key_limit()
    
    if current_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"API key limit reached ({limit}). Please upgrade your plan.",
        )
    
    # Generate new API key
    full_key, key_prefix, key_hash = generate_api_key()
    
    # Create API key record
    api_key = APIKey(
        user_id=current_user.id,
        key_prefix=key_prefix,
        key_hash=key_hash,
        name=key_data.name,
    )
    db.add(api_key)
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.API_KEY_CREATE,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        metadata={"key_prefix": key_prefix, "name": key_data.name},
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(api_key)
    
    # Return with full key (shown only once)
    return APIKeyCreated(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        key=full_key,  # Full key - shown only once
        is_active=api_key.is_active,
        last_used_at=api_key.last_used_at,
        usage_count=api_key.usage_count,
        created_at=api_key.created_at,
    )


@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_subscribed_user),
    db: AsyncSession = Depends(get_db),
):
    """Get details of a specific API key."""
    result = await db.execute(
        select(APIKey)
        .where(APIKey.id == key_id)
        .where(APIKey.user_id == current_user.id)
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
    
    return api_key


@router.patch("/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: UUID,
    update_data: APIKeyUpdate,
    current_user: User = Depends(get_current_subscribed_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an API key's name or status."""
    result = await db.execute(
        select(APIKey)
        .where(APIKey.id == key_id)
        .where(APIKey.user_id == current_user.id)
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
    
    if api_key.revoked_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a revoked API key",
        )
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(api_key, field, value)
    
    await db.commit()
    await db.refresh(api_key)
    
    return api_key


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_subscribed_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke an API key. This action is permanent."""
    result = await db.execute(
        select(APIKey)
        .where(APIKey.id == key_id)
        .where(APIKey.user_id == current_user.id)
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
    
    if api_key.revoked_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API key already revoked",
        )
    
    # Revoke the key
    api_key.is_active = False
    api_key.revoked_at = datetime.utcnow()
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.API_KEY_REVOKE,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        metadata={"key_prefix": api_key.key_prefix, "name": api_key.name},
    )
    db.add(audit_log)
    
    await db.commit()
    
    return {"message": "API key revoked successfully"}


@router.post("/{key_id}/regenerate", response_model=APIKeyCreated)
async def regenerate_api_key(
    key_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_subscribed_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Regenerate an API key with a new value.
    
    The old key will be immediately invalidated.
    """
    result = await db.execute(
        select(APIKey)
        .where(APIKey.id == key_id)
        .where(APIKey.user_id == current_user.id)
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
    
    if api_key.revoked_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot regenerate a revoked API key",
        )
    
    # Generate new key
    full_key, key_prefix, key_hash = generate_api_key()
    
    # Update the key
    api_key.key_prefix = key_prefix
    api_key.key_hash = key_hash
    api_key.last_used_at = None
    api_key.usage_count = 0
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.API_KEY_REGENERATE,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        metadata={"key_prefix": key_prefix, "name": api_key.name},
    )
    db.add(audit_log)
    
    await db.commit()
    await db.refresh(api_key)
    
    return APIKeyCreated(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        key=full_key,
        is_active=api_key.is_active,
        last_used_at=api_key.last_used_at,
        usage_count=api_key.usage_count,
        created_at=api_key.created_at,
    )

