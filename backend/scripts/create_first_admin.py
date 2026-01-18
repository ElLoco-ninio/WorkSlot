import sys
import os
# Add the parent directory (backend) to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from app.database import engine, init_db
from app.models import User
from app.auth import get_password_hash
from datetime import datetime
import sys

def create_admin(email, password):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        if user:
            print(f"User {email} already exists")
            return
        
        hashed_password = get_password_hash(password)
        admin_user = User(
            email=email,
            hashed_password=hashed_password,
            is_admin=True,
            trial_ends_at=datetime(2030, 1, 1), # Long expiry for admin
            onboarding_completed=True
        )
        session.add(admin_user)
        session.commit()
        print(f"Admin user {email} created successfully")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_first_admin.py <email> <password>")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    # init_db() # Ensure tables exist
    create_admin(email, password)
