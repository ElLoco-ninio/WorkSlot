"""Booking management API endpoints for providers."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_client_ip
from app.models import User, Booking, BookingStatus, AuditLog, AuditAction
from app.schemas import (
    BookingResponse,
    BookingDetailResponse,
    BookingListResponse,
    BookingApprove,
    BookingDecline,
)
from app.services.booking_service import BookingService


router = APIRouter()


@router.get("", response_model=BookingListResponse)
async def list_bookings(
    status_filter: Optional[str] = Query(None, description="Comma-separated status values"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all bookings with optional filters."""
    # Parse status filter
    statuses = None
    if status_filter:
        try:
            statuses = [BookingStatus(s.strip()) for s in status_filter.split(",")]
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status value: {e}",
            )
    
    service = BookingService(db)
    bookings, total = await service.list_bookings(
        provider_id=current_user.id,
        status_filter=statuses,
        start_date=start_date,
        end_date=end_date,
        page=page,
        size=size,
    )
    
    pages = (total + size - 1) // size
    
    return BookingListResponse(
        items=bookings,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/today", response_model=List[BookingResponse])
async def get_today_bookings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all bookings for today."""
    service = BookingService(db)
    bookings = await service.get_today_bookings(current_user.id)
    return bookings


@router.get("/upcoming", response_model=List[BookingResponse])
async def get_upcoming_bookings(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get upcoming confirmed bookings."""
    service = BookingService(db)
    bookings = await service.get_upcoming_bookings(current_user.id, limit)
    return bookings


@router.get("/{booking_id}", response_model=BookingDetailResponse)
async def get_booking(
    booking_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific booking by ID."""
    service = BookingService(db)
    booking = await service.get_booking(booking_id, current_user.id)
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    
    return booking


@router.post("/{booking_id}/approve", response_model=BookingResponse)
async def approve_booking(
    booking_id: UUID,
    approve_data: BookingApprove,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve a pending or verified booking."""
    service = BookingService(db)
    booking = await service.get_booking(booking_id, current_user.id)
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    
    try:
        booking = await service.approve_booking(booking, approve_data.provider_notes)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.BOOKING_APPROVE,
        ip_address=get_client_ip(request),
        metadata={"booking_id": str(booking.id), "customer_email": booking.customer_email},
    )
    db.add(audit_log)
    
    await db.commit()
    
    # TODO: Send confirmation email to customer
    
    return booking


@router.post("/{booking_id}/decline", response_model=BookingResponse)
async def decline_booking(
    booking_id: UUID,
    decline_data: BookingDecline,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Decline a booking."""
    service = BookingService(db)
    booking = await service.get_booking(booking_id, current_user.id)
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    
    try:
        booking = await service.decline_booking(booking, decline_data.reason)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.BOOKING_DECLINE,
        ip_address=get_client_ip(request),
        metadata={
            "booking_id": str(booking.id),
            "customer_email": booking.customer_email,
            "reason": decline_data.reason,
        },
    )
    db.add(audit_log)
    
    await db.commit()
    
    # TODO: Send decline email to customer
    
    return booking


@router.post("/{booking_id}/arrive", response_model=BookingResponse)
async def mark_arrived(
    booking_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark customer as arrived."""
    service = BookingService(db)
    booking = await service.get_booking(booking_id, current_user.id)
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    
    try:
        booking = await service.mark_arrived(booking)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.BOOKING_ARRIVE,
        ip_address=get_client_ip(request),
        metadata={"booking_id": str(booking.id)},
    )
    db.add(audit_log)
    
    await db.commit()
    
    return booking


@router.post("/{booking_id}/complete", response_model=BookingResponse)
async def mark_completed(
    booking_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark booking as completed."""
    service = BookingService(db)
    booking = await service.get_booking(booking_id, current_user.id)
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    
    try:
        booking = await service.mark_completed(booking)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.BOOKING_COMPLETE,
        ip_address=get_client_ip(request),
        metadata={"booking_id": str(booking.id)},
    )
    db.add(audit_log)
    
    await db.commit()
    
    return booking


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: UUID,
    reason: Optional[str] = None,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a booking."""
    service = BookingService(db)
    booking = await service.get_booking(booking_id, current_user.id)
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )
    
    try:
        booking = await service.cancel_booking(booking, reason)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action=AuditAction.BOOKING_CANCEL,
        ip_address=get_client_ip(request) if request else "unknown",
        metadata={"booking_id": str(booking.id), "reason": reason},
    )
    db.add(audit_log)
    
    await db.commit()
    
    # TODO: Send cancellation email to customer
    
    return booking

