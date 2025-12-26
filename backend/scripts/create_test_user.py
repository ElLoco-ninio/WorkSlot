"""Script to create a test user account."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import async_session_maker
from app.core.security import hash_password
from app.models import User, Subscription, PlanType, SubscriptionStatus


async def create_test_user():
    """Create or update test user account."""
    test_email = "test@example.com"
    test_password = "Test123!@#"
    test_business_name = "Test Business"
    
    async with async_session_maker() as session:
        try:
            # Check if test user exists
            result = await session.execute(
                select(User).where(User.email == test_email.lower())
            )
            test_user = result.scalar_one_or_none()
            
            if test_user:
                # Update existing test user
                print(f"Test user found: {test_email}")
                test_user.password_hash = hash_password(test_password)
                test_user.is_active = True
                test_user.is_verified = True
                print("Test user account updated.")
            else:
                # Create new test user
                print(f"Creating test user account: {test_email}")
                test_user = User(
                    email=test_email.lower(),
                    password_hash=hash_password(test_password),
                    business_name=test_business_name,
                    timezone="UTC",
                    is_active=True,
                    is_verified=True,
                )
                session.add(test_user)
                await session.flush()
                
                # Create Basic subscription for test user
                subscription = Subscription(
                    user_id=test_user.id,
                    plan_type=PlanType.BASIC,
                    status=SubscriptionStatus.ACTIVE,
                )
                session.add(subscription)
                print("Test user account created successfully!")
            
            await session.commit()
            print(f"\nTest User Credentials:")
            print(f"  Email: {test_email}")
            print(f"  Password: {test_password}")
            print(f"  Business: {test_business_name}")
            print(f"  Plan: Basic (Active)")
            
        except Exception as e:
            await session.rollback()
            print(f"Error creating test user account: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(create_test_user())

