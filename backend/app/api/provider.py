"""Provider dashboard API endpoints."""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import User, Booking, BookingStatus
from app.schemas import (
    UserResponse,
    SubscriptionResponse,
    SubscriptionWithLimits,
    BookingStats,
)
from app.services.subscription_service import SubscriptionService
from app.services.payment_service import PaymentService
from app.models.subscription import PlanType


router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_provider_profile(
    current_user: User = Depends(get_current_user),
):
    """Get current provider profile."""
    return current_user


@router.get("/subscription", response_model=SubscriptionWithLimits)
async def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current subscription status with limits."""
    subscription = current_user.subscription
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found",
        )
    
    service = SubscriptionService(db)
    limits = await service.check_limits(subscription)
    
    return SubscriptionWithLimits(
        id=subscription.id,
        user_id=subscription.user_id,
        plan_type=subscription.plan_type,
        status=subscription.status,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        cancel_at_period_end=subscription.cancel_at_period_end,
        created_at=subscription.created_at,
        is_active=subscription.is_active,
        can_use_api=subscription.can_use_api,
        api_key_limit=subscription.get_api_key_limit(),
        booking_limit=subscription.get_booking_limit(),
    )


@router.post("/subscription/checkout")
async def create_checkout_session(
    plan: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a Stripe Checkout session for subscription upgrade.
    Returns the checkout URL.
    """
    try:
        plan_type = PlanType(plan.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan type. Valid options: {[p.value for p in PlanType]}",
        )
    
    if plan_type == PlanType.FREE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create checkout session for free plan",
        )

    # Ensure customer exists
    customer_id = await PaymentService.create_customer(current_user)
    
    # Update user if customer_id acts as a cache (optional optimization, handled in service)
    if not current_user.subscription.stripe_customer_id:
        current_user.subscription.stripe_customer_id = customer_id
        await db.commit()

    # Create checkout session
    checkout_url = await PaymentService.create_checkout_session(
        current_user, 
        plan_type, 
        customer_id
    )
    
    return {"checkout_url": checkout_url}


@router.post("/subscription/activate-trial")
async def activate_trial(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Activate a 14-day trial of the Basic plan."""
    from app.models.subscription import PlanType
    
    subscription = current_user.subscription
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found",
        )
    
    if subscription.plan_type != PlanType.FREE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trial is only available for free plan users",
        )
    
    service = SubscriptionService(db)
    await service.activate_trial(subscription)
    await db.commit()
    
    return {
        "message": "14-day trial activated",
        "trial_ends": subscription.current_period_end,
    }


@router.get("/stats", response_model=BookingStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard statistics for the provider."""
    today = datetime.utcnow().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    
    # Today's bookings
    today_result = await db.execute(
        select(func.count(Booking.id))
        .where(Booking.provider_id == current_user.id)
        .where(func.date(Booking.slot_start) == today)
    )
    total_today = today_result.scalar() or 0
    
    # Pending bookings
    pending_result = await db.execute(
        select(func.count(Booking.id))
        .where(Booking.provider_id == current_user.id)
        .where(Booking.status.in_([BookingStatus.PENDING, BookingStatus.VERIFIED]))
    )
    total_pending = pending_result.scalar() or 0
    
    # Confirmed bookings
    confirmed_result = await db.execute(
        select(func.count(Booking.id))
        .where(Booking.provider_id == current_user.id)
        .where(Booking.status == BookingStatus.CONFIRMED)
    )
    total_confirmed = confirmed_result.scalar() or 0
    
    # Completed bookings
    completed_result = await db.execute(
        select(func.count(Booking.id))
        .where(Booking.provider_id == current_user.id)
        .where(Booking.status == BookingStatus.COMPLETED)
    )
    total_completed = completed_result.scalar() or 0
    
    # This week
    week_result = await db.execute(
        select(func.count(Booking.id))
        .where(Booking.provider_id == current_user.id)
        .where(func.date(Booking.slot_start) >= week_start)
    )
    total_this_week = week_result.scalar() or 0
    
    # This month
    month_result = await db.execute(
        select(func.count(Booking.id))
        .where(Booking.provider_id == current_user.id)
        .where(func.date(Booking.slot_start) >= month_start)
    )
    total_this_month = month_result.scalar() or 0
    
    return BookingStats(
        total_today=total_today,
        total_pending=total_pending,
        total_confirmed=total_confirmed,
        total_completed=total_completed,
        total_this_week=total_this_week,
        total_this_month=total_this_month,
    )


@router.get("/plans")
async def get_available_plans():
    """Get available subscription plans and their features."""
    from app.models.subscription import PlanType
    
    plans = []
    for plan_type in PlanType:
        features = SubscriptionService.get_plan_features(plan_type)
        plans.append({
            "type": plan_type.value,
            **features,
        })
    
    return {"plans": plans}

@router.post("/bookings/{booking_id}/confirm-payment")
async def confirm_booking_payment(
    booking_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Manually confirm a booking that is AWAITING_PAYMENT.
    """
    # 1. Fetch booking
    query = select(Booking).where(
        and_(
            Booking.id == booking_id,
            Booking.provider_id == current_user.id
        )
    )
    result = await db.execute(query)
    booking = result.scalar_one_or_none()
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
        
    # 2. Check strict state transitions
    if booking.status == BookingStatus.EXPIRED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This booking has expired and can no longer be confirmed."
        )
        
    if booking.status != BookingStatus.AWAITING_PAYMENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot confirm booking with status: {booking.status}. Only AWAITING_PAYMENT bookings can be confirmed."
        )
        
    # 3. Transition to CONFIRMED
    booking.status = BookingStatus.CONFIRMED
    booking.confirmed_at = datetime.utcnow()
    # Clear hold expiration as it's no longer relevant
    booking.hold_expires_at = None
    
    await db.commit()
    
    return {"message": "Booking confirmed successfully", "status": booking.status}


@router.put("/settings")
async def update_provider_settings(
    settings_update: dict, # Simplified schema for MVP speed
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update provider settings (Payment Link, Hold Duration, Profile)."""
    
    allowed_fields = [
        "business_name", "service_category", "location_city",
        "payment_link", "payment_required", "payment_hold_minutes", 
        "manual_confirm_enabled"
    ]
    
    for field in allowed_fields:
        if field in settings_update:
            setattr(current_user, field, settings_update[field])
            
    await db.commit()
    return {"message": "Settings updated", "user": current_user}
