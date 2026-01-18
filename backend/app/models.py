from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON

# User Models
class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    is_admin: bool = Field(default=False)
    trial_ends_at: datetime
    onboarding_completed: bool = Field(default=False)
    is_active: bool = Field(default=True)

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    
    profile: Optional["Profile"] = Relationship(back_populates="user")
    bookings: List["Booking"] = Relationship(back_populates="provider")

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int

# Access Request Models
class AccessRequestBase(SQLModel):
    email: str
    phone: Optional[str] = None
    business_category: str
    city: str
    description: str
    status: str = Field(default="pending") # pending, reviewed, approved, rejected
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AccessRequest(AccessRequestBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class AccessRequestCreate(AccessRequestBase):
    pass

class AccessRequestRead(AccessRequestBase):
    id: int

# Profile Models
class ProfileBase(SQLModel):
    business_name: str
    logo_url: Optional[str] = None
    business_category: str
    service_area: str
    country: Optional[str] = None
    slug: str = Field(index=True, unique=True)
    availability_config: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    booking_rules: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))

class Profile(ProfileBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="profile")

class ProfileCreate(ProfileBase):
    new_password: str
    slug: Optional[str] = None # Allow optional in create, we'll gen it if missing or let user set it

class ProfileUpdate(SQLModel):
    business_name: Optional[str] = None
    business_category: Optional[str] = None
    service_area: Optional[str] = None
    country: Optional[str] = None
    logo_url: Optional[str] = None
    slug: Optional[str] = None
    availability_config: Optional[Dict[str, Any]] = None
    booking_rules: Optional[Dict[str, Any]] = None
    new_password: Optional[str] = None

class ProfileRead(ProfileBase):
    id: int
    user_id: int

# Booking Models
class BookingBase(SQLModel):
    customer_email: str
    customer_name: str
    customer_comment: Optional[str] = None
    provider_comment: Optional[str] = None
    start_time: datetime
    end_time: datetime
    status: str = Field(default="pending")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    hold_expires_at: Optional[datetime] = None

class Booking(BookingBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    provider_id: int = Field(foreign_key="user.id")
    provider: User = Relationship(back_populates="bookings")

class BookingCreate(BookingBase):
    provider_id: int

class BookingStatusUpdate(SQLModel):
    status: str
    provider_comment: Optional[str] = Field(default=None, max_length=500)

class BookingRead(BookingBase):
    id: int
    provider_id: int
