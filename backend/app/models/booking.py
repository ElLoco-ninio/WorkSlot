"""Booking model for customer appointments."""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class BookingStatus(str, Enum):
    """Booking status workflow."""
    PENDING = "pending"            # Initial state (if payment not required)
    AWAITING_PAYMENT = "awaiting_payment" # Initial state (if payment required)
    VERIFIED = "verified"          # Email verified (legacy/optional)
    CONFIRMED = "confirmed"        # Approved by provider
    DECLINED = "declined"          # Rejected by provider
    EXPIRED = "expired"            # Payment hold time elapsed
    ARRIVED = "arrived"           # Customer arrived
    COMPLETED = "completed"       # Job completed
    CANCELLED = "cancelled"       # Cancelled by customer or provider
    NO_SHOW = "no_show"          # Customer didn't show up


class Booking(Base):
    """Customer booking/appointment model."""
    
    __tablename__ = "bookings"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Customer information
    customer_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    customer_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    customer_phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    
    # Booking time slot
    slot_start: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )
    slot_end: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    # Hold & Expiration Logic
    hold_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )
    expired_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    
    # Payment Tracking (Audit only, no status implication)
    payment_redirected_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    
    # Booking details
    service_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Status tracking
    status: Mapped[BookingStatus] = mapped_column(
        SQLEnum(BookingStatus),
        default=BookingStatus.PENDING,
        nullable=False,
        index=True,
    )
    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    
    # Provider notes (internal)
    provider_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    decline_reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
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
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    arrived_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    
    # Relationships
    provider: Mapped["User"] = relationship(
        "User",
        back_populates="bookings",
    )
    verification_token: Mapped["EmailVerificationToken"] = relationship(
        "EmailVerificationToken",
        back_populates="booking",
        uselist=False,
    )
    
    def __repr__(self) -> str:
        return f"<Booking {self.customer_name} @ {self.slot_start}>"


class EmailVerificationToken(Base):
    """Token for verifying customer email addresses."""
    
    __tablename__ = "email_verification_tokens"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    
    # Token storage
    token_hash: Mapped[str] = mapped_column(
        String(64),  # SHA-256 hash
        nullable=False,
        unique=True,
        index=True,
    )
    
    # Expiration
    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )
    
    # Status
    used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    
    # Relationship
    booking: Mapped["Booking"] = relationship(
        "Booking",
        back_populates="verification_token",
    )
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not used and not expired)."""
        return not self.used and not self.is_expired
    
    def __repr__(self) -> str:
        return f"<EmailVerificationToken booking={self.booking_id}>"

