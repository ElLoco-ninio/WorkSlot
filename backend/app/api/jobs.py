from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.booking import Booking, BookingStatus

router = APIRouter()

@router.post("/expire-bookings", status_code=status.HTTP_200_OK)
async def expire_bookings(
    db: AsyncSession = Depends(get_db),
):
    """
    Background job to expire bookings that have exceeded their hold duration.
    This should be called periodically (e.g., every minute) by a cron job.
    """
    now = datetime.utcnow()
    
    # query for bookings that are AWAITING_PAYMENT and hold_expires_at < now
    query = select(Booking).where(
        and_(
            Booking.status == BookingStatus.AWAITING_PAYMENT,
            Booking.hold_expires_at < now
        )
    )
    
    result = await db.execute(query)
    expired_bookings = result.scalars().all()
    
    count = 0
    for booking in expired_bookings:
        booking.status = BookingStatus.EXPIRED
        booking.expired_at = now
        count += 1
    
    if count > 0:
        await db.commit()
        
    return {"message": f"Expired {count} bookings", "count": count}
