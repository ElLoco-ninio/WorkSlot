"""Availability management API endpoints."""
from datetime import datetime, time
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import User
from app.schemas import (
    AvailabilityCreate,
    AvailabilityUpdate,
    AvailabilityResponse,
    WeeklyAvailability,
    BlockedDateCreate,
    BlockedDateResponse,
)
from app.services.availability_service import AvailabilityService


router = APIRouter()


@router.get("", response_model=WeeklyAvailability)
async def get_weekly_availability(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the weekly availability schedule."""
    service = AvailabilityService(db)
    schedule = await service.get_weekly_schedule(current_user.id)
    
    # If no schedule exists, create default
    if not schedule:
        schedule = await service.create_default_availability(current_user.id)
        await db.commit()
    
    return WeeklyAvailability(schedule=schedule)


@router.put("/{day_of_week}", response_model=AvailabilityResponse)
async def update_day_availability(
    day_of_week: int,
    availability_data: AvailabilityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update availability for a specific day of the week (0=Monday, 6=Sunday)."""
    if day_of_week < 0 or day_of_week > 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="day_of_week must be between 0 (Monday) and 6 (Sunday)",
        )
    
    service = AvailabilityService(db)
    availability = await service.set_day_availability(
        user_id=current_user.id,
        day_of_week=day_of_week,
        start_time=availability_data.start_time,
        end_time=availability_data.end_time,
        slot_duration_minutes=availability_data.slot_duration_minutes,
        buffer_minutes=availability_data.buffer_minutes,
        is_available=availability_data.is_available,
    )
    
    await db.commit()
    await db.refresh(availability)
    
    return availability


@router.post("/bulk", response_model=WeeklyAvailability)
async def update_bulk_availability(
    schedule: List[AvailabilityCreate],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update availability for multiple days at once."""
    if len(schedule) != 7:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide availability for all 7 days",
        )
    
    service = AvailabilityService(db)
    updated = []
    
    for avail_data in schedule:
        availability = await service.set_day_availability(
            user_id=current_user.id,
            day_of_week=avail_data.day_of_week,
            start_time=avail_data.start_time,
            end_time=avail_data.end_time,
            slot_duration_minutes=avail_data.slot_duration_minutes,
            buffer_minutes=avail_data.buffer_minutes,
            is_available=avail_data.is_available,
        )
        updated.append(availability)
    
    await db.commit()
    
    return WeeklyAvailability(schedule=updated)


@router.post("/reset")
async def reset_to_default(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reset availability to default schedule (Mon-Fri 9am-5pm)."""
    service = AvailabilityService(db)
    await service.create_default_availability(current_user.id)
    await db.commit()
    
    return {"message": "Availability reset to default schedule"}


# ============== Blocked Dates ==============

@router.get("/blocked", response_model=List[BlockedDateResponse])
async def list_blocked_dates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all blocked dates."""
    from datetime import date, timedelta
    
    service = AvailabilityService(db)
    # Get blocked dates for the next year
    today = date.today()
    blocked = await service.get_blocked_dates(
        current_user.id,
        today,
        today + timedelta(days=365),
    )
    
    return blocked


@router.post("/blocked", response_model=BlockedDateResponse, status_code=status.HTTP_201_CREATED)
async def add_blocked_date(
    blocked_data: BlockedDateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a blocked date (e.g., vacation, holiday)."""
    from datetime import date
    
    if blocked_data.date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot block dates in the past",
        )
    
    service = AvailabilityService(db)
    blocked = await service.add_blocked_date(
        user_id=current_user.id,
        blocked_date=blocked_data.date,
        start_time=blocked_data.start_time,
        end_time=blocked_data.end_time,
        reason=blocked_data.reason,
    )
    
    await db.commit()
    await db.refresh(blocked)
    
    return blocked


@router.delete("/blocked/{blocked_id}")
async def remove_blocked_date(
    blocked_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a blocked date."""
    service = AvailabilityService(db)
    removed = await service.remove_blocked_date(current_user.id, blocked_id)
    
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blocked date not found",
        )
    
    await db.commit()
    
    return {"message": "Blocked date removed"}

