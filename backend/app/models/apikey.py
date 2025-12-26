"""API Key model for widget authentication."""
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class APIKey(Base):
    """API Key model for authenticating widget requests."""
    
    __tablename__ = "api_keys"
    
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
    
    # Key storage - only prefix is visible, hash for verification
    key_prefix: Mapped[str] = mapped_column(
        String(12),  # e.g., "wsk_abc123"
        nullable=False,
        index=True,
    )
    key_hash: Mapped[str] = mapped_column(
        String(64),  # SHA-256 hash
        nullable=False,
        unique=True,
    )
    
    # Metadata
    name: Mapped[str] = mapped_column(
        String(100),
        default="Default API Key",
        nullable=False,
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    
    # Usage tracking
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    usage_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    
    # Relationship
    user: Mapped["User"] = relationship(
        "User",
        back_populates="api_keys",
    )
    
    def __repr__(self) -> str:
        return f"<APIKey {self.key_prefix}... ({self.name})>"

