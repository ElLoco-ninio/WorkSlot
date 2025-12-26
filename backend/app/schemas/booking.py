"""Booking Pydantic schemas."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models.booking import BookingStatus


class BookingBase(BaseModel):
    """Base booking schema."""
    customer_name: str = Field(..., min_length=2, max_length=255)
    customer_email: EmailStr
    customer_phone: Optional[str] = Field(None, max_length=50)
    service_type: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = Field(None, max_length=1000)


class BookingCreate(BookingBase):
    """Schema for creating a booking (from widget)."""
    slot_start: datetime
    slot_end: datetime


class BookingResponse(BookingBase):
    """Schema for booking response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    provider_id: UUID
    slot_start: datetime
    slot_end: datetime
    status: BookingStatus
    email_verified: bool
    created_at: datetime
    updated_at: datetime


class BookingDetailResponse(BookingResponse):
    """Detailed booking response for provider."""
    provider_notes: Optional[str] = None
    decline_reason: Optional[str] = None
    verified_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    arrived_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class BookingApprove(BaseModel):
    """Schema for approving a booking."""
    provider_notes: Optional[str] = Field(None, max_length=1000)


class BookingDecline(BaseModel):
    """Schema for declining a booking."""
    reason: str = Field(..., min_length=5, max_length=500)


class BookingListResponse(BaseModel):
    """Schema for paginated booking list."""
    items: List[BookingResponse]
    total: int
    page: int
    size: int
    pages: int


class BookingStats(BaseModel):
    """Schema for booking statistics."""
    total_today: int
    total_pending: int
    total_confirmed: int
    total_completed: int
    total_this_week: int
    total_this_month: int

