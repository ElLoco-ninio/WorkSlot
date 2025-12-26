"""API Key Pydantic schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class APIKeyCreate(BaseModel):
    """Schema for creating an API key."""
    name: str = Field(default="Default API Key", max_length=100)


class APIKeyResponse(BaseModel):
    """Schema for API key response (without full key)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    key_prefix: str
    is_active: bool
    last_used_at: Optional[datetime] = None
    usage_count: int
    created_at: datetime


class APIKeyCreated(APIKeyResponse):
    """Schema for newly created API key (includes full key - shown only once)."""
    key: str  # Full API key, only shown on creation


class APIKeyUpdate(BaseModel):
    """Schema for updating an API key."""
    name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None

