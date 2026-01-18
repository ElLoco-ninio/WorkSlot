from datetime import datetime, timedelta, date, time
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from contextlib import asynccontextmanager
from .database import init_db, engine
from .models import User, UserRead, AccessRequest, AccessRequestCreate, AccessRequestRead, Profile, ProfileCreate, ProfileRead
from .auth import verify_password, create_access_token, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
from .deps import get_session, get_current_admin, get_current_user

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup
    init_db()
    yield
    # On shutdown

app = FastAPI(title="WorkSlot V1", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "is_admin": user.is_admin,
        "onboarding_completed": user.onboarding_completed
    }

@app.post("/api/access-requests", response_model=AccessRequestRead)
async def create_access_request(request: AccessRequestCreate, session: Session = Depends(get_session)):
    db_request = AccessRequest.model_validate(request)
    session.add(db_request)
    session.commit()
    session.refresh(db_request)
    return db_request

@app.get("/api/admin/access-requests", response_model=List[AccessRequestRead])
async def read_access_requests(session: Session = Depends(get_session), admin: User = Depends(get_current_admin)):
    requests = session.exec(select(AccessRequest).order_by(AccessRequest.created_at.desc())).all()
    return requests

@app.get("/api/admin/users", response_model=List[UserRead])
async def read_users(session: Session = Depends(get_session), admin: User = Depends(get_current_admin)):
    users = session.exec(select(User)).all()
    return users

@app.post("/api/admin/users", response_model=UserRead)
async def create_user_manual(email: str, session: Session = Depends(get_session), admin: User = Depends(get_current_admin)):
    # check existing
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Generate temp password (random 8 chars)
    import secrets
    temp_password = secrets.token_urlsafe(8)
    hashed = get_password_hash(temp_password)
    
    new_user = User(
        email=email,
        hashed_password=hashed,
        is_admin=False,
        trial_ends_at=datetime.utcnow() + timedelta(days=30),
        onboarding_completed=True, # Skip onboarding wizard
        is_active=True
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    # Auto-create empty profile
    base_slug = email.split("@")[0].lower().replace(".", "-")
    profile = Profile(
        user_id=new_user.id,
        business_name="New Business", # Placeholder
        business_category="Uncategorized",
        service_area="Remote",
        slug=f"{base_slug}-{new_user.id}"
    )
    session.add(profile)
    session.commit()
    
    # TODO: In production this would send email. For V1 we return it or just console log it.
    print(f"CREATED USER: {email} / {temp_password}") 
    return new_user

@app.put("/api/admin/users/{user_id}/status")
async def toggle_user_status(user_id: int, active: bool, session: Session = Depends(get_session), admin: User = Depends(get_current_admin)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = active
    session.add(user)
    session.commit()
    return {"status": "success", "is_active": user.is_active}

@app.post("/api/onboarding", response_model=ProfileRead)
async def complete_onboarding(profile_data: ProfileCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    if current_user.onboarding_completed:
        raise HTTPException(status_code=400, detail="Onboarding already completed")
    
    # Update Password if provided
    if profile_data.new_password:
        current_user.hashed_password = get_password_hash(profile_data.new_password)
        session.add(current_user)

    # Create Profile (exclude inputs that aren't in Profile model)
    profile_dict = profile_data.model_dump(exclude={"new_password"})
    
    # Generate Slug if missing
    if not profile_dict.get("slug"):
        base_slug = profile_dict["business_name"].lower().replace(" ", "-")
        # specific uniqueness check could be here, for V1 just appending ID
        profile_dict["slug"] = f"{base_slug}-{current_user.id}"

    # Inject user_id for validation
    profile_dict["user_id"] = current_user.id

    db_profile = Profile.model_validate(profile_dict)
    # db_profile.user_id = current_user.id # Already in dict
    
    session.add(db_profile)
    
    # Mark Complete
    current_user.onboarding_completed = True
    session.add(current_user)
    
    session.commit()
    session.refresh(db_profile)
    return db_profile

@app.get("/api/profile", response_model=ProfileRead)
async def get_profile(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    profile = session.exec(select(Profile).where(Profile.user_id == current_user.id)).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

from .models import ProfileUpdate
@app.patch("/api/profile", response_model=ProfileRead)
async def update_profile(profile_data: ProfileUpdate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    profile = session.exec(select(Profile).where(Profile.user_id == current_user.id)).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    profile_data_dict = profile_data.model_dump(exclude_unset=True)
    
    # Handle Password Update
    if "new_password" in profile_data_dict:
        new_pwd = profile_data_dict.pop("new_password")
        if new_pwd:
             current_user.hashed_password = get_password_hash(new_pwd)
             session.add(current_user)

    for key, value in profile_data_dict.items():
        setattr(profile, key, value)
        
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile

from datetime import date
from .models import Booking, BookingCreate, BookingRead, Profile
from .utils import generate_slots

# ... existing code ...

@app.get("/api/public/provider/{slug}", response_model=ProfileRead)
async def get_public_provider(slug: str, session: Session = Depends(get_session)):
    profile = session.exec(select(Profile).where(Profile.slug == slug)).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Provider not found")
    return profile

@app.get("/api/public/provider/{slug}/slots")
async def get_provider_slots(slug: str, date_str: str, session: Session = Depends(get_session)):
    # 1. Get Profile
    profile = session.exec(select(Profile).where(Profile.slug == slug)).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Provider not found")
        
    # 2. Parse Date
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format (YYYY-MM-DD)")
        
    # 3. Get Bookings for Date
    # Filter bookings that overlap with this day (simple approach: start_time on same day)
    # Using python filtering for MVP simplicity or proper SQL filter
    # Let's use SQL filter for start_time range
    day_start = datetime.combine(target_date, time.min)
    day_end = datetime.combine(target_date, time.max)
    
    bookings = session.exec(
        select(Booking)
        .where(Booking.provider_id == profile.user_id)
        .where(Booking.start_time >= day_start)
        .where(Booking.start_time <= day_end)
    ).all()
    
    # 4. Generate
    slots = generate_slots(target_date, profile.availability_config, bookings)
    return slots

from fastapi import BackgroundTasks
from .email import email_service

# ... existing imports ...

from sqlalchemy import text

@app.post("/api/public/bookings", response_model=BookingRead)
async def create_booking(booking_data: BookingCreate, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    import os
    
    # Verify Provider
    provider = session.exec(select(User).where(User.id == booking_data.provider_id)).first()
    if not provider:
         raise HTTPException(status_code=404, detail="Provider not found")
    
    # Verify Slot Availability
    collision = session.exec(
        select(Booking)
        .where(Booking.provider_id == booking_data.provider_id)
        .where(Booking.start_time < booking_data.end_time)
        .where(Booking.end_time > booking_data.start_time)
        .where(Booking.status.not_in(["declined", "expired"]))
    ).first()
    
    if collision:
        raise HTTPException(status_code=409, detail="Slot no longer available")

    # Create Booking
    db_booking = Booking(
        provider_id=booking_data.provider_id,
        customer_email=booking_data.customer_email,
        customer_name=booking_data.customer_name,
        customer_comment=booking_data.customer_comment,
        start_time=booking_data.start_time,
        end_time=booking_data.end_time,
        status="pending",
        created_at=datetime.utcnow(),
        hold_expires_at=datetime.utcnow() + timedelta(minutes=30)
    )
    
    session.add(db_booking)
    session.commit()
    session.refresh(db_booking)
    
    # Notify Provider
    dashboard_link = f"{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/dashboard"
    background_tasks.add_task(email_service.send_provider_notification, provider.email, db_booking.customer_name, dashboard_link)
    
    return db_booking


# ...

@app.get("/api/provider/bookings", response_model=List[BookingRead])
async def get_provider_bookings(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    bookings = session.exec(select(Booking).where(Booking.provider_id == current_user.id).order_by(Booking.created_at.desc())).all()
    return bookings

from .models import BookingStatusUpdate, BookingRead

@app.put("/api/provider/bookings/{booking_id}/status")
async def update_booking_status(booking_id: int, update_data: BookingStatusUpdate, background_tasks: BackgroundTasks, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    if update_data.status not in ["confirmed", "declined"]:
         raise HTTPException(status_code=400, detail="Invalid status")
         
    booking = session.get(Booking, booking_id)
    if not booking or booking.provider_id != current_user.id:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    if booking.status == "expired":
        raise HTTPException(status_code=400, detail="Cannot update expired booking")
        
    booking.status = update_data.status
    if update_data.provider_comment:
        booking.provider_comment = update_data.provider_comment
        
    session.add(booking)
    session.commit()
    session.refresh(booking)
    
    # Notify Customer
    provider_profile = session.exec(select(Profile).where(Profile.user_id == current_user.id)).first()
    business_name = provider_profile.business_name if provider_profile else "Provider"
    
    background_tasks.add_task(email_service.send_customer_update, booking.customer_email, booking.status, business_name, booking.provider_comment)
    
    return {"status": "success", "booking_status": booking.status}
    
    return booking

 
