"""Availability management and slot calculation service."""
from datetime import datetime, date, time, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Availability, BlockedDate, Booking, BookingStatus
from app.schemas import TimeSlot, DayAvailability


class AvailabilityService:
    """Service for managing availability and calculating available slots."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_weekly_schedule(self, user_id: UUID) -> List[Availability]:
        """Get the weekly availability schedule for a user."""
        result = await self.db.execute(
            select(Availability)
            .where(Availability.user_id == user_id)
            .order_by(Availability.day_of_week)
        )
        return list(result.scalars().all())
    
    async def set_day_availability(
        self,
        user_id: UUID,
        day_of_week: int,
        start_time: time,
        end_time: time,
        slot_duration_minutes: int = 60,
        buffer_minutes: int = 0,
        is_available: bool = True,
    ) -> Availability:
        """Set or update availability for a specific day of the week."""
        # Check if entry exists
        result = await self.db.execute(
            select(Availability)
            .where(Availability.user_id == user_id)
            .where(Availability.day_of_week == day_of_week)
        )
        availability = result.scalar_one_or_none()
        
        if availability:
            # Update existing
            availability.start_time = start_time
            availability.end_time = end_time
            availability.slot_duration_minutes = slot_duration_minutes
            availability.buffer_minutes = buffer_minutes
            availability.is_available = is_available
            availability.updated_at = datetime.utcnow()
        else:
            # Create new
            availability = Availability(
                user_id=user_id,
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
                slot_duration_minutes=slot_duration_minutes,
                buffer_minutes=buffer_minutes,
                is_available=is_available,
            )
            self.db.add(availability)
        
        await self.db.flush()
        return availability
    
    async def create_default_availability(self, user_id: UUID) -> List[Availability]:
        """Create default availability schedule (Mon-Fri 9am-5pm)."""
        schedules = []
        default_start = time(9, 0)
        default_end = time(17, 0)
        
        # Monday to Friday (0-4)
        for day in range(5):
            avail = await self.set_day_availability(
                user_id=user_id,
                day_of_week=day,
                start_time=default_start,
                end_time=default_end,
                slot_duration_minutes=60,
                buffer_minutes=0,
                is_available=True,
            )
            schedules.append(avail)
        
        # Saturday and Sunday (5-6) - unavailable by default
        for day in range(5, 7):
            avail = await self.set_day_availability(
                user_id=user_id,
                day_of_week=day,
                start_time=default_start,
                end_time=default_end,
                slot_duration_minutes=60,
                buffer_minutes=0,
                is_available=False,
            )
            schedules.append(avail)
        
        return schedules
    
    async def get_blocked_dates(
        self,
        user_id: UUID,
        start_date: date,
        end_date: date,
    ) -> List[BlockedDate]:
        """Get blocked dates within a date range."""
        result = await self.db.execute(
            select(BlockedDate)
            .where(BlockedDate.user_id == user_id)
            .where(BlockedDate.date >= start_date)
            .where(BlockedDate.date <= end_date)
        )
        return list(result.scalars().all())
    
    async def add_blocked_date(
        self,
        user_id: UUID,
        blocked_date: date,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None,
        reason: Optional[str] = None,
    ) -> BlockedDate:
        """Add a blocked date."""
        blocked = BlockedDate(
            user_id=user_id,
            date=blocked_date,
            start_time=start_time,
            end_time=end_time,
            reason=reason,
        )
        self.db.add(blocked)
        await self.db.flush()
        return blocked
    
    async def remove_blocked_date(self, user_id: UUID, blocked_id: UUID) -> bool:
        """Remove a blocked date."""
        result = await self.db.execute(
            select(BlockedDate)
            .where(BlockedDate.id == blocked_id)
            .where(BlockedDate.user_id == user_id)
        )
        blocked = result.scalar_one_or_none()
        
        if blocked:
            await self.db.delete(blocked)
            return True
        return False
    
    async def get_existing_bookings(
        self,
        provider_id: UUID,
        start_date: date,
        end_date: date,
    ) -> List[Booking]:
        """Get existing bookings that could conflict with new slots."""
        start_datetime = datetime.combine(start_date, time.min)
        end_datetime = datetime.combine(end_date, time.max)
        
        result = await self.db.execute(
            select(Booking)
            .where(Booking.provider_id == provider_id)
            .where(Booking.slot_start >= start_datetime)
            .where(Booking.slot_end <= end_datetime)
            .where(Booking.status.in_([
                BookingStatus.PENDING,
                BookingStatus.VERIFIED,
                BookingStatus.CONFIRMED,
                BookingStatus.ARRIVED,
            ]))
        )
        return list(result.scalars().all())
    
    async def calculate_available_slots(
        self,
        provider_id: UUID,
        start_date: date,
        end_date: date,
        timezone: str = "UTC",
    ) -> List[DayAvailability]:
        """
        Calculate available time slots for a date range.
        
        This considers:
        - Weekly availability schedule
        - Blocked dates
        - Existing bookings
        - Buffer time between slots
        """
        # Get weekly schedule
        weekly_schedule = await self.get_weekly_schedule(provider_id)
        schedule_by_day = {a.day_of_week: a for a in weekly_schedule}
        
        # Get blocked dates
        blocked_dates = await self.get_blocked_dates(provider_id, start_date, end_date)
        blocked_by_date = {}
        for bd in blocked_dates:
            if bd.date not in blocked_by_date:
                blocked_by_date[bd.date] = []
            blocked_by_date[bd.date].append(bd)
        
        # Get existing bookings
        existing_bookings = await self.get_existing_bookings(provider_id, start_date, end_date)
        bookings_by_date = {}
        for booking in existing_bookings:
            booking_date = booking.slot_start.date()
            if booking_date not in bookings_by_date:
                bookings_by_date[booking_date] = []
            bookings_by_date[booking_date].append(booking)
        
        # Generate slots for each day
        days = []
        current_date = start_date
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        # Don't show slots in the past
        now = datetime.utcnow()
        
        while current_date <= end_date:
            day_of_week = current_date.weekday()
            availability = schedule_by_day.get(day_of_week)
            
            slots = []
            
            # Check if day is available
            if availability and availability.is_available:
                # Check if entire day is blocked
                is_fully_blocked = False
                if current_date in blocked_by_date:
                    for blocked in blocked_by_date[current_date]:
                        if blocked.start_time is None and blocked.end_time is None:
                            is_fully_blocked = True
                            break
                
                if not is_fully_blocked:
                    # Generate time slots
                    slot_duration = timedelta(minutes=availability.slot_duration_minutes)
                    buffer = timedelta(minutes=availability.buffer_minutes)
                    
                    current_time = datetime.combine(current_date, availability.start_time)
                    end_time = datetime.combine(current_date, availability.end_time)
                    
                    while current_time + slot_duration <= end_time:
                        slot_end = current_time + slot_duration
                        is_available = True
                        
                        # Skip slots in the past
                        if current_time < now:
                            is_available = False
                        
                        # Check if slot is blocked
                        if current_date in blocked_by_date:
                            for blocked in blocked_by_date[current_date]:
                                if blocked.start_time and blocked.end_time:
                                    block_start = datetime.combine(current_date, blocked.start_time)
                                    block_end = datetime.combine(current_date, blocked.end_time)
                                    if not (slot_end <= block_start or current_time >= block_end):
                                        is_available = False
                                        break
                        
                        # Check if slot conflicts with existing booking
                        if current_date in bookings_by_date:
                            for booking in bookings_by_date[current_date]:
                                if not (slot_end <= booking.slot_start or current_time >= booking.slot_end):
                                    is_available = False
                                    break
                        
                        slots.append(TimeSlot(
                            start=current_time,
                            end=slot_end,
                            available=is_available,
                        ))
                        
                        current_time = slot_end + buffer
            
            days.append(DayAvailability(
                date=current_date,
                day_name=day_names[day_of_week],
                slots=slots,
            ))
            
            current_date += timedelta(days=1)
        
        return days
    
    async def is_slot_available(
        self,
        provider_id: UUID,
        slot_start: datetime,
        slot_end: datetime,
    ) -> bool:
        """Check if a specific time slot is available."""
        slot_date = slot_start.date()
        
        # Get day's availability
        available_days = await self.calculate_available_slots(
            provider_id,
            slot_date,
            slot_date,
        )
        
        if not available_days:
            return False
        
        day = available_days[0]
        
        # Find matching slot
        for slot in day.slots:
            if slot.start == slot_start and slot.end == slot_end:
                return slot.available
        
        return False

