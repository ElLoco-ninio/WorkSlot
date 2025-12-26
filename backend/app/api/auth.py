"""Authentication API endpoints."""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_token_pair,
    decode_token,
    create_access_token,
)
from app.core.dependencies import get_current_user, get_client_ip
from app.models import User, Subscription, AuditLog, AuditAction
from app.models.subscription import PlanType, SubscriptionStatus
from app.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    UserPasswordChange,
    TokenResponse,
    RefreshTokenRequest,
)


router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new service provider account.
    
    Creates a user with a free subscription plan.
    """
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email.lower())
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create user
    user = User(
        email=user_data.email.lower(),
        password_hash=hash_password(user_data.password),
        business_name=user_data.business_name,
        phone=user_data.phone,
        timezone=user_data.timezone,
    )
    db.add(user)
    await db.flush()
    
    # Create free subscription
    subscription = Subscription(
        user_id=user.id,
        plan_type=PlanType.FREE,
        status=SubscriptionStatus.ACTIVE,
    )
    db.add(subscription)
    
    # Create audit log
    audit_log = AuditLog(
        user_id=user.id,
        action=AuditAction.REGISTER,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
        metadata={"email": user.email},
    )
    db.add(audit_log)
    
    await db.commit()
    
    # Generate tokens
    access_token, refresh_token, expires_in = create_token_pair(str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate and login a user.
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == credentials.email.lower())
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    
    # Create audit log
    audit_log = AuditLog(
        user_id=user.id,
        action=AuditAction.LOGIN,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    db.add(audit_log)
    await db.commit()
    
    # Generate tokens
    access_token, refresh_token, expires_in = create_token_pair(str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using refresh token.
    """
    payload = decode_token(token_request.refresh_token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    
    user_id = payload.get("sub")
    
    # Verify user still exists and is active
    result = await db.execute(
        select(User).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    # Generate new tokens
    access_token, refresh_token, expires_in = create_token_pair(str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Get current user profile.
    """
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_current_user_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update current user profile.
    """
    update_dict = update_data.model_dump(exclude_unset=True)
    
    for field, value in update_dict.items():
        setattr(current_user, field, value)
    
    current_user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(current_user)
    
    return current_user


@router.post("/change-password")
async def change_password(
    password_data: UserPasswordChange,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change user password.
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    
    # Update password
    current_user.password_hash = hash_password(password_data.new_password)
    current_user.updated_at = datetime.utcnow()
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.PASSWORD_CHANGE,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    db.add(audit_log)
    
    await db.commit()
    
    return {"message": "Password changed successfully"}

