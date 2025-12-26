import pytest
import uuid
from datetime import datetime, timedelta
from fastapi import HTTPException
from app.models import User, Booking, BookingStatus
from app.api.provider import confirm_booking_payment

# Mocks
class MockDB:
    def __init__(self):
        self.committed = False
    async def execute(self, query):
        return self
    def scalar_one_or_none(self):
        return self.result
    async def commit(self):
        self.committed = True

@pytest.mark.asyncio
async def test_confirm_booking_success():
    # Setup
    user = User(id=uuid.uuid4(), email="provider@test.com")
    booking = Booking(
        id=uuid.uuid4(),
        provider_id=user.id,
        status=BookingStatus.AWAITING_PAYMENT,
        hold_expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    
    db = MockDB()
    db.result = booking
    
    # Action
    response = await confirm_booking_payment(str(booking.id), user, db)
    
    # Assert
    assert booking.status == BookingStatus.CONFIRMED
    assert booking.hold_expires_at is None
    assert booking.confirmed_at is not None
    assert db.committed is True

@pytest.mark.asyncio
async def test_confirm_booking_expired_failure():
    # Setup
    user = User(id=uuid.uuid4(), email="provider@test.com")
    booking = Booking(
        id=uuid.uuid4(),
        provider_id=user.id,
        status=BookingStatus.EXPIRED, # Already expired
        hold_expires_at=datetime.utcnow() - timedelta(minutes=10)
    )
    
    db = MockDB()
    db.result = booking
    
    # Action & Assert
    with pytest.raises(HTTPException) as exc:
        await confirm_booking_payment(str(booking.id), user, db)
    assert exc.value.status_code == 409
    assert "expired" in exc.value.detail.lower()

@pytest.mark.asyncio
async def test_confirm_booking_wrong_status_failure():
    # Setup
    user = User(id=uuid.uuid4(), email="provider@test.com")
    booking = Booking(
        id=uuid.uuid4(),
        provider_id=user.id,
        status=BookingStatus.PENDING, # Wrong status
    )
    
    db = MockDB()
    db.result = booking
    
    # Action & Assert
    with pytest.raises(HTTPException) as exc:
        await confirm_booking_payment(str(booking.id), user, db)
    assert exc.value.status_code == 400
