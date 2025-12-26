"""User model for service providers."""
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    """Service provider user model."""
    
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    business_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    timezone: Mapped[str] = mapped_column(
        String(50),
        default="UTC",
        nullable=False,
    )
    
    # Profile & Service Details
    service_category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    location_city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    
    # Payment & Booking Configuration
    payment_link: Mapped[str | None] = mapped_column(
        String(500), # URL to Stripe/PayPal
        nullable=True,
    )
    payment_required: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    payment_hold_minutes: Mapped[int] = mapped_column(
        Integer,
        default=30,
        nullable=False,
    )
    manual_confirm_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
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
    
    # Relationships
    subscription: Mapped["Subscription"] = relationship(
        "Subscription",
        back_populates="user",
        uselist=False,
    )
    api_keys: Mapped[list["APIKey"]] = relationship(
        "APIKey",
        back_populates="user",
    )
    availability: Mapped[list["Availability"]] = relationship(
        "Availability",
        back_populates="user",
    )
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking",
        back_populates="provider",
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
    )
    
    def __repr__(self) -> str:
        return f"<User {self.email}>"

