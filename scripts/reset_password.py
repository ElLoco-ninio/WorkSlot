import sys
import os
# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlmodel import Session, select
from app.database import engine
from app.models import User
from app.auth import get_password_hash

def reset_password(email: str):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        if not user:
            print(f"User {email} not found!")
            return
        
        new_password = "password"
        user.hashed_password = get_password_hash(new_password)
        session.add(user)
        session.commit()
        print(f"Password for {email} reset to: {new_password}")

if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else "debug_user_01@example.com"
    reset_password(email)
