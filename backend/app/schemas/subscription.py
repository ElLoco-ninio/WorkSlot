"""Subscription Pydantic schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

from app.models.subscription import PlanType, SubscriptionStatus


class SubscriptionBase(BaseModel):
    """Base subscription schema."""
    plan_type: PlanType


class SubscriptionCreate(SubscriptionBase):
    """Schema for creating subscription."""
    pass


class SubscriptionUpdate(BaseModel):
    """Schema for updating subscription."""
    plan_type: Optional[PlanType] = None


class SubscriptionResponse(SubscriptionBase):
    """Schema for subscription response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    status: SubscriptionStatus
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool
    created_at: datetime
    
    # Computed fields
    is_active: bool
    can_use_api: bool


class SubscriptionWithLimits(SubscriptionResponse):
    """Subscription with plan limits."""
    api_key_limit: int
    booking_limit: int

