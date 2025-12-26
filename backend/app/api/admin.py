"""Admin API endpoints."""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_admin_user
from app.models import User, Booking, Subscription, APIKey, AuditLog
from app.schemas import UserResponse, BookingResponse
from app.models.subscription import PlanType, SubscriptionStatus

router = APIRouter()


@router.get("/stats")
async def get_admin_stats(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get admin dashboard statistics.
    """
    # Total users
    users_result = await db.execute(select(func.count(User.id)))
    total_users = users_result.scalar() or 0
    
    # Total bookings
    bookings_result = await db.execute(select(func.count(Booking.id)))
    total_bookings = bookings_result.scalar() or 0
    
    # Active subscriptions
    subscriptions_result = await db.execute(
        select(func.count(Subscription.id))
        .where(Subscription.status.in_(["active", "trialing"]))
    )
    active_subscriptions = subscriptions_result.scalar() or 0
    
    # Total API keys
    api_keys_result = await db.execute(select(func.count(APIKey.id)))
    total_api_keys = api_keys_result.scalar() or 0
    
    # Recent users (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_users_result = await db.execute(
        select(func.count(User.id)).where(User.created_at >= week_ago)
    )
    recent_users = recent_users_result.scalar() or 0
    
    return {
        "total_users": total_users,
        "total_bookings": total_bookings,
        "active_subscriptions": active_subscriptions,
        "total_api_keys": total_api_keys,
        "recent_users": recent_users,
    }


@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List all users with pagination and filters."""
    query = select(User).options(selectinload(User.subscription))
    
    # Apply filters
    if search:
        query = query.where(
            or_(
                User.email.ilike(f"%{search}%"),
                User.business_name.ilike(f"%{search}%"),
            )
        )
    
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination and ordering
    query = query.order_by(User.created_at.desc()).offset((page - 1) * size).limit(size)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return {
        "items": [UserResponse.model_validate(u) for u in users],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size,
    }


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed user information."""
    result = await db.execute(
        select(User)
        .options(selectinload(User.subscription), selectinload(User.api_keys))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user


@router.patch("/users/{user_id}/activate")
async def toggle_user_active(
    user_id: UUID,
    is_active: bool = Query(..., description="Set user active status"),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Activate or deactivate a user account."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own account",
        )
    
    user.is_active = is_active
    await db.commit()
    await db.refresh(user)
    
    return {"message": f"User {'activated' if is_active else 'deactivated'} successfully", "user": user}


@router.patch("/users/{user_id}/subscription")
async def update_user_subscription(
    user_id: UUID,
    plan_type: PlanType = Query(..., description="New plan type"),
    subscription_status: SubscriptionStatus = Query(..., description="New subscription status"),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user subscription plan and status."""
    result = await db.execute(
        select(User)
        .options(selectinload(User.subscription))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if not user.subscription:
        # Create subscription if it doesn't exist
        subscription = Subscription(
            user_id=user.id,
            plan_type=plan_type,
            status=subscription_status,
        )
        db.add(subscription)
    else:
        user.subscription.plan_type = plan_type
        user.subscription.status = subscription_status
    
    await db.commit()
    await db.refresh(user)
    
    return {"message": "Subscription updated successfully", "user": user}


@router.get("/bookings")
async def list_all_bookings(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List all bookings across all users."""
    query = select(Booking).options(selectinload(Booking.provider))
    
    if user_id:
        query = query.where(Booking.provider_id == user_id)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.order_by(Booking.created_at.desc()).offset((page - 1) * size).limit(size)
    
    result = await db.execute(query)
    bookings = result.scalars().all()
    
    return {
        "items": [BookingResponse.model_validate(b) for b in bookings],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size,
    }


@router.get("/health")
async def get_system_health(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get system health and troubleshooting information."""
    # Database connectivity
    try:
        await db.execute(select(1))
        db_status = "healthy"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Recent errors from audit logs
    error_logs_result = await db.execute(
        select(func.count(AuditLog.id))
        .where(AuditLog.action == "ERROR")
        .where(AuditLog.created_at >= datetime.utcnow() - timedelta(days=1))
    )
    recent_errors = error_logs_result.scalar() or 0
    
    # Inactive users count
    inactive_users_result = await db.execute(
        select(func.count(User.id)).where(User.is_active == False)
    )
    inactive_users = inactive_users_result.scalar() or 0
    
    return {
        "database": db_status,
        "recent_errors_24h": recent_errors,
        "inactive_users": inactive_users,
        "timestamp": datetime.utcnow().isoformat(),
    }

