"""Pydantic schemas package."""
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserLogin,
    UserUpdate,
    UserPasswordChange,
    UserResponse,
    TokenPayload,
    TokenResponse,
    RefreshTokenRequest,
)
from app.schemas.subscription import (
    SubscriptionBase,
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionResponse,
    SubscriptionWithLimits,
)
from app.schemas.apikey import (
    APIKeyCreate,
    APIKeyResponse,
    APIKeyCreated,
    APIKeyUpdate,
)
from app.schemas.booking import (
    BookingBase,
    BookingCreate,
    BookingResponse,
    BookingDetailResponse,
    BookingApprove,
    BookingDecline,
    BookingListResponse,
    BookingStats,
)
from app.schemas.availability import (
    TimeSlot,
    DayAvailability,
    AvailabilityBase,
    AvailabilityCreate,
    AvailabilityUpdate,
    AvailabilityResponse,
    WeeklyAvailability,
    BlockedDateBase,
    BlockedDateCreate,
    BlockedDateResponse,
    AvailableSlotsRequest,
    AvailableSlotsResponse,
)

__all__ = [
    # User
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "UserPasswordChange",
    "UserResponse",
    "TokenPayload",
    "TokenResponse",
    "RefreshTokenRequest",
    # Subscription
    "SubscriptionBase",
    "SubscriptionCreate",
    "SubscriptionUpdate",
    "SubscriptionResponse",
    "SubscriptionWithLimits",
    # API Key
    "APIKeyCreate",
    "APIKeyResponse",
    "APIKeyCreated",
    "APIKeyUpdate",
    # Booking
    "BookingBase",
    "BookingCreate",
    "BookingResponse",
    "BookingDetailResponse",
    "BookingApprove",
    "BookingDecline",
    "BookingListResponse",
    "BookingStats",
    # Availability
    "TimeSlot",
    "DayAvailability",
    "AvailabilityBase",
    "AvailabilityCreate",
    "AvailabilityUpdate",
    "AvailabilityResponse",
    "WeeklyAvailability",
    "BlockedDateBase",
    "BlockedDateCreate",
    "BlockedDateResponse",
    "AvailableSlotsRequest",
    "AvailableSlotsResponse",
]
