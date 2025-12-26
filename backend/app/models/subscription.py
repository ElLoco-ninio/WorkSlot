"""Subscription model for plan management."""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PlanType(str, Enum):
    """Subscription plan types."""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"


class SubscriptionStatus(str, Enum):
    """Subscription status types."""
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"


class Subscription(Base):
    """Subscription model for managing user plans."""
    
    __tablename__ = "subscriptions"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    plan_type: Mapped[PlanType] = mapped_column(
        SQLEnum(PlanType),
        default=PlanType.FREE,
        nullable=False,
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        SQLEnum(SubscriptionStatus),
        default=SubscriptionStatus.ACTIVE,
        nullable=False,
    )
    
    # Stripe integration fields (ready for production)
    stripe_customer_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    stripe_price_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    
    # Billing period
    current_period_start: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    cancel_at_period_end: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    
    # Relationship
    user: Mapped["User"] = relationship(
        "User",
        back_populates="subscription",
    )
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is active."""
        return self.status in (SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING)
    
    @property
    def can_use_api(self) -> bool:
        """Check if user can use API features."""
        return self.is_active and self.plan_type != PlanType.FREE
    
    def get_api_key_limit(self) -> int:
        """Get API key limit based on plan."""
        limits = {
            PlanType.FREE: 0,
            PlanType.BASIC: 1,
            PlanType.PRO: 5,
        }
        return limits.get(self.plan_type, 0)
    
    def get_booking_limit(self) -> int:
        """Get monthly booking limit based on plan."""
        limits = {
            PlanType.FREE: 0,
            PlanType.BASIC: 100,
            PlanType.PRO: 1000,
        }
        return limits.get(self.plan_type, 0)
    
    def __repr__(self) -> str:
        return f"<Subscription {self.plan_type.value} - {self.status.value}>"

