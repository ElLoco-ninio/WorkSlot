"""Booking management service."""
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import generate_verification_token, hash_verification_token
from app.models import Booking, BookingStatus, EmailVerificationToken, User
from app.services.availability_service import AvailabilityService


class BookingService:
    """Service for managing bookings."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_booking(
        self,
        provider_id: UUID,
        customer_name: str,
        customer_email: str,
        slot_start: datetime,
        slot_end: datetime,
        customer_phone: Optional[str] = None,
        service_type: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Tuple[Booking, str]:
        """
        Create a new booking.
        
        Returns:
            Tuple of (booking, verification_token)
        """
        # Verify slot is available
        availability_service = AvailabilityService(self.db)
        is_available = await availability_service.is_slot_available(
            provider_id, slot_start, slot_end
        )
        
        if not is_available:
            raise ValueError("Selected time slot is not available")
        
        # Check for conflicts
        conflict = await self.check_booking_conflict(provider_id, slot_start, slot_end)
        if conflict:
            raise ValueError("Time slot conflicts with an existing booking")
        
        # Create booking
        booking = Booking(
            provider_id=provider_id,
            customer_name=customer_name,
            customer_email=customer_email.lower(),
            customer_phone=customer_phone,
            slot_start=slot_start,
            slot_end=slot_end,
            service_type=service_type,
            notes=notes,
            status=BookingStatus.PENDING,
        )
        self.db.add(booking)
        await self.db.flush()
        
        # Generate verification token
        token, token_hash = generate_verification_token()
        expires_at = datetime.utcnow() + timedelta(hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS)
        
        verification = EmailVerificationToken(
            booking_id=booking.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(verification)
        
        return booking, token
    
    async def check_booking_conflict(
        self,
        provider_id: UUID,
        slot_start: datetime,
        slot_end: datetime,
        exclude_booking_id: Optional[UUID] = None,
    ) -> bool:
        """Check if a time slot conflicts with existing bookings."""
        query = select(Booking).where(
            and_(
                Booking.provider_id == provider_id,
                Booking.status.in_([
                    BookingStatus.PENDING,
                    BookingStatus.VERIFIED,
                    BookingStatus.CONFIRMED,
                    BookingStatus.ARRIVED,
                ]),
                # Overlap check: not (new_end <= existing_start or new_start >= existing_end)
                Booking.slot_start < slot_end,
                Booking.slot_end > slot_start,
            )
        )
        
        if exclude_booking_id:
            query = query.where(Booking.id != exclude_booking_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def verify_booking(self, token: str) -> Optional[Booking]:
        """Verify a booking using the email verification token."""
        token_hash = hash_verification_token(token)
        
        result = await self.db.execute(
            select(EmailVerificationToken)
            .options(selectinload(EmailVerificationToken.booking))
            .where(EmailVerificationToken.token_hash == token_hash)
        )
        verification = result.scalar_one_or_none()
        
        if not verification:
            return None
        
        if not verification.is_valid:
            return None
        
        # Mark token as used
        verification.used = True
        verification.used_at = datetime.utcnow()
        
        # Update booking status
        booking = verification.booking
        booking.email_verified = True
        booking.verified_at = datetime.utcnow()
        booking.status = BookingStatus.VERIFIED
        
        return booking
    
    async def get_booking(self, booking_id: UUID, provider_id: UUID) -> Optional[Booking]:
        """Get a booking by ID."""
        result = await self.db.execute(
            select(Booking)
            .where(Booking.id == booking_id)
            .where(Booking.provider_id == provider_id)
        )
        return result.scalar_one_or_none()
    
    async def approve_booking(
        self,
        booking: Booking,
        provider_notes: Optional[str] = None,
    ) -> Booking:
        """Approve a booking."""
        if booking.status not in [BookingStatus.PENDING, BookingStatus.VERIFIED]:
            raise ValueError(f"Cannot approve booking with status: {booking.status.value}")
        
        booking.status = BookingStatus.CONFIRMED
        booking.confirmed_at = datetime.utcnow()
        booking.updated_at = datetime.utcnow()
        
        if provider_notes:
            booking.provider_notes = provider_notes
        
        return booking
    
    async def decline_booking(
        self,
        booking: Booking,
        reason: str,
    ) -> Booking:
        """Decline a booking."""
        if booking.status in [BookingStatus.COMPLETED, BookingStatus.CANCELLED]:
            raise ValueError(f"Cannot decline booking with status: {booking.status.value}")
        
        booking.status = BookingStatus.DECLINED
        booking.decline_reason = reason
        booking.updated_at = datetime.utcnow()
        
        return booking
    
    async def mark_arrived(self, booking: Booking) -> Booking:
        """Mark customer as arrived."""
        if booking.status != BookingStatus.CONFIRMED:
            raise ValueError("Can only mark arrival for confirmed bookings")
        
        booking.status = BookingStatus.ARRIVED
        booking.arrived_at = datetime.utcnow()
        booking.updated_at = datetime.utcnow()
        
        return booking
    
    async def mark_completed(self, booking: Booking) -> Booking:
        """Mark booking as completed."""
        if booking.status not in [BookingStatus.CONFIRMED, BookingStatus.ARRIVED]:
            raise ValueError("Can only complete confirmed or arrived bookings")
        
        booking.status = BookingStatus.COMPLETED
        booking.completed_at = datetime.utcnow()
        booking.updated_at = datetime.utcnow()
        
        return booking
    
    async def cancel_booking(
        self,
        booking: Booking,
        reason: Optional[str] = None,
    ) -> Booking:
        """Cancel a booking."""
        if booking.status in [BookingStatus.COMPLETED, BookingStatus.CANCELLED]:
            raise ValueError(f"Cannot cancel booking with status: {booking.status.value}")
        
        booking.status = BookingStatus.CANCELLED
        if reason:
            booking.provider_notes = reason
        booking.updated_at = datetime.utcnow()
        
        return booking
    
    async def list_bookings(
        self,
        provider_id: UUID,
        status_filter: Optional[List[BookingStatus]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[Booking], int]:
        """List bookings with filters and pagination."""
        query = select(Booking).where(Booking.provider_id == provider_id)
        count_query = select(func.count(Booking.id)).where(Booking.provider_id == provider_id)
        
        if status_filter:
            query = query.where(Booking.status.in_(status_filter))
            count_query = count_query.where(Booking.status.in_(status_filter))
        
        if start_date:
            query = query.where(Booking.slot_start >= start_date)
            count_query = count_query.where(Booking.slot_start >= start_date)
        
        if end_date:
            query = query.where(Booking.slot_end <= end_date)
            count_query = count_query.where(Booking.slot_end <= end_date)
        
        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        query = query.order_by(Booking.slot_start.desc())
        query = query.offset((page - 1) * size).limit(size)
        
        result = await self.db.execute(query)
        bookings = list(result.scalars().all())
        
        return bookings, total
    
    async def get_today_bookings(self, provider_id: UUID) -> List[Booking]:
        """Get all bookings for today."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        result = await self.db.execute(
            select(Booking)
            .where(Booking.provider_id == provider_id)
            .where(Booking.slot_start >= today_start)
            .where(Booking.slot_start < today_end)
            .order_by(Booking.slot_start)
        )
        
        return list(result.scalars().all())
    
    async def get_upcoming_bookings(
        self,
        provider_id: UUID,
        limit: int = 10,
    ) -> List[Booking]:
        """Get upcoming confirmed bookings."""
        now = datetime.utcnow()
        
        result = await self.db.execute(
            select(Booking)
            .where(Booking.provider_id == provider_id)
            .where(Booking.slot_start >= now)
            .where(Booking.status == BookingStatus.CONFIRMED)
            .order_by(Booking.slot_start)
            .limit(limit)
        )
        
        return list(result.scalars().all())

