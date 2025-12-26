from datetime import datetime, timedelta
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, Field

from app.core.database import get_db
from app.models import User, Booking, BookingStatus, Availability
# We need to import the availability service - skipping for now to focus on flow

router = APIRouter()

class PublicProviderProfile(BaseModel):
    id: uuid.UUID
    business_name: str
    service_category: Optional[str]
    location_city: Optional[str]
    payment_required: bool
    # Do not expose payment_link here, only on booking creation

class CreateBookingRequest(BaseModel):
    provider_id: uuid.UUID
    slot_start: datetime
    customer_name: str
    customer_email: EmailStr
    customer_phone: Optional[str] = None
    notes: Optional[str] = None

class CreateBookingResponse(BaseModel):
    booking_id: uuid.UUID
    status: str
    payment_required: bool
    payment_link: Optional[str] = None
    redirect_url: Optional[str] = None # Helper for frontend
    expires_at: Optional[datetime] = None

@router.get("/public/provider/{provider_id}", response_model=PublicProviderProfile)
async def get_public_provider(
    provider_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get public provider details for booking page."""
    query = select(User).where(User.id == provider_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Provider not found")
        
    return PublicProviderProfile(
        id=user.id,
        business_name=user.business_name,
        service_category=user.service_category,
        location_city=user.location_city,
        payment_required=user.payment_required
    )

@router.post("/public/bookings", response_model=CreateBookingResponse)
async def create_booking(
    request: CreateBookingRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new booking."""
    # 1. Fetch Provider
    result = await db.execute(select(User).where(User.id == request.provider_id))
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    # 2. Calculate End Time (Hardcoded 60 mins for MVP for now or from Avail)
    # TODO: Fetch real slot duration from Availability model
    slot_duration = 60 
    slot_end = request.slot_start + timedelta(minutes=slot_duration)
    
    # 3. Determine Initial Status & Hold
    if provider.payment_required:
        initial_status = BookingStatus.AWAITING_PAYMENT
        hold_minutes = provider.payment_hold_minutes or 30
        hold_expires_at = datetime.utcnow() + timedelta(minutes=hold_minutes)
        payment_link = provider.payment_link
    else:
        initial_status = BookingStatus.PENDING # Or CONFIRMED if auto-confirm
        hold_expires_at = None
        payment_link = None
        
    # 4. Create Booking
    new_booking = Booking(
        provider_id=request.provider_id,
        customer_name=request.customer_name,
        customer_email=request.customer_email,
        customer_phone=request.customer_phone,
        slot_start=request.slot_start,
        slot_end=slot_end, 
        notes=request.notes,
        status=initial_status,
        hold_expires_at=hold_expires_at,
        payment_redirected_at=None, # Set ONLY when they click link
    )
    
    db.add(new_booking)
    await db.commit()
    await db.refresh(new_booking)
    
    return CreateBookingResponse(
        booking_id=new_booking.id,
        status=new_booking.status,
        payment_required=provider.payment_required,
        payment_link=payment_link,
        redirect_url=payment_link, # Alias
        expires_at=hold_expires_at
    )
