"""Availability model for scheduling configuration."""
import uuid
from datetime import datetime, time, date
from sqlalchemy import String, Boolean, DateTime, Time, Date, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Availability(Base):
    """Weekly availability schedule for a provider."""
    
    __tablename__ = "availability"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Day of week (0=Monday, 6=Sunday)
    day_of_week: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    
    # Working hours
    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )
    end_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )
    
    # Slot configuration
    slot_duration_minutes: Mapped[int] = mapped_column(
        Integer,
        default=60,
        nullable=False,
    )
    buffer_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    
    # Status
    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
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
        back_populates="availability",
    )
    
    def __repr__(self) -> str:
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return f"<Availability {days[self.day_of_week]} {self.start_time}-{self.end_time}>"


class BlockedDate(Base):
    """Specific dates when provider is unavailable."""
    
    __tablename__ = "blocked_dates"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Blocked date range
    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    
    # Optional: block specific time range only
    start_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )
    end_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )
    
    # Reason for blocking
    reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    
    def __repr__(self) -> str:
        return f"<BlockedDate {self.date}>"

