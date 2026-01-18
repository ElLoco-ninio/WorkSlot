from sqlmodel import Session, select
from app.database import engine
from app.models import User
from app.auth import get_password_hash
import datetime

def create_fresh_user():
    with Session(engine) as session:
        email = "fresh_user_01@example.com"
        # Cleanup if exists
        distinct_user = session.exec(select(User).where(User.email == email)).first()
        if distinct_user:
            session.delete(distinct_user)
            session.commit()
            print(f"Deleted existing {email}")

        # Create new
        new_user = User(
            email=email,
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_admin=False,
            onboarding_completed=False,
            trial_ends_at=datetime.datetime.utcnow() + datetime.timedelta(days=30)
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        print(f"Created fresh user: {new_user.email} / password123")

if __name__ == "__main__":
    create_fresh_user()
