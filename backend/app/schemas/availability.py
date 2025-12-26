"""Availability Pydantic schemas."""
from datetime import datetime, time, date
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, field_validator


class TimeSlot(BaseModel):
    """A single available time slot."""
    start: datetime
    end: datetime
    available: bool = True


class DayAvailability(BaseModel):
    """Available slots for a specific day."""
    date: date
    day_name: str
    slots: List[TimeSlot]


class AvailabilityBase(BaseModel):
    """Base availability schema."""
    day_of_week: int = Field(..., ge=0, le=6)  # 0=Monday, 6=Sunday
    start_time: time
    end_time: time
    slot_duration_minutes: int = Field(default=60, ge=15, le=480)
    buffer_minutes: int = Field(default=0, ge=0, le=60)
    is_available: bool = True
    
    @field_validator('end_time')
    @classmethod
    def end_time_after_start(cls, v, info):
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('end_time must be after start_time')
        return v


class AvailabilityCreate(AvailabilityBase):
    """Schema for creating availability."""
    pass


class AvailabilityUpdate(BaseModel):
    """Schema for updating availability."""
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    slot_duration_minutes: Optional[int] = Field(None, ge=15, le=480)
    buffer_minutes: Optional[int] = Field(None, ge=0, le=60)
    is_available: Optional[bool] = None


class AvailabilityResponse(AvailabilityBase):
    """Schema for availability response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime


class WeeklyAvailability(BaseModel):
    """Full weekly availability schedule."""
    schedule: List[AvailabilityResponse]


class BlockedDateBase(BaseModel):
    """Base blocked date schema."""
    date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    reason: Optional[str] = Field(None, max_length=255)


class BlockedDateCreate(BlockedDateBase):
    """Schema for creating a blocked date."""
    pass


class BlockedDateResponse(BlockedDateBase):
    """Schema for blocked date response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    created_at: datetime


class AvailableSlotsRequest(BaseModel):
    """Request schema for getting available slots."""
    start_date: date
    end_date: date
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        if 'start_date' in info.data:
            if v < info.data['start_date']:
                raise ValueError('end_date must be on or after start_date')
            # Limit range to 30 days
            delta = v - info.data['start_date']
            if delta.days > 30:
                raise ValueError('Date range cannot exceed 30 days')
        return v


class AvailableSlotsResponse(BaseModel):
    """Response schema for available slots."""
    provider_id: UUID
    business_name: str
    timezone: str
    days: List[DayAvailability]

