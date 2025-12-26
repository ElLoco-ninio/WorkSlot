"""Audit log model for tracking user actions."""
import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AuditAction(str, Enum):
    """Types of auditable actions."""
    # Auth actions
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    PASSWORD_CHANGE = "password_change"
    
    # API Key actions
    API_KEY_CREATE = "api_key_create"
    API_KEY_REVOKE = "api_key_revoke"
    API_KEY_REGENERATE = "api_key_regenerate"
    
    # Booking actions
    BOOKING_CREATE = "booking_create"
    BOOKING_VERIFY = "booking_verify"
    BOOKING_APPROVE = "booking_approve"
    BOOKING_DECLINE = "booking_decline"
    BOOKING_ARRIVE = "booking_arrive"
    BOOKING_COMPLETE = "booking_complete"
    BOOKING_CANCEL = "booking_cancel"
    
    # Availability actions
    AVAILABILITY_UPDATE = "availability_update"
    BLOCKED_DATE_CREATE = "blocked_date_create"
    BLOCKED_DATE_DELETE = "blocked_date_delete"
    
    # Subscription actions
    SUBSCRIPTION_CREATE = "subscription_create"
    SUBSCRIPTION_UPDATE = "subscription_update"
    SUBSCRIPTION_CANCEL = "subscription_cancel"
    
    # Settings actions
    SETTINGS_UPDATE = "settings_update"


class AuditLog(Base):
    """Audit log for tracking important user actions."""
    
    __tablename__ = "audit_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Action details
    action: Mapped[AuditAction] = mapped_column(
        SQLEnum(AuditAction),
        nullable=False,
        index=True,
    )
    
    # Additional metadata (flexible JSON storage)
    event_metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    
    # Request information
    ip_address: Mapped[str | None] = mapped_column(
        String(45),  # IPv6 compatible
        nullable=True,
    )
    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )
    
    # Relationship
    user: Mapped["User"] = relationship(
        "User",
        back_populates="audit_logs",
    )
    
    def __repr__(self) -> str:
        return f"<AuditLog {self.action.value} @ {self.created_at}>"

