"""Script to create or update admin account."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import async_session_maker
from app.core.security import hash_password
from app.models import User, Subscription, PlanType, SubscriptionStatus


async def create_admin():
    """Create or update admin account."""
    admin_email = "admin@ctabuilder.com"
    admin_password = "Admin123!@#"
    admin_business_name = "CTABuilder Admin"
    
    async with async_session_maker() as session:
        try:
            # Check if admin exists
            result = await session.execute(
                select(User).where(User.email == admin_email.lower())
            )
            admin_user = result.scalar_one_or_none()
            
            if admin_user:
                # Update existing admin
                print(f"Admin account found: {admin_email}")
                admin_user.password_hash = hash_password(admin_password)
                admin_user.is_active = True
                admin_user.is_verified = True
                # Check if is_admin attribute exists (for backward compatibility)
                if hasattr(admin_user, 'is_admin'):
                    admin_user.is_admin = True
                print("Admin account updated with new password and admin privileges.")
            else:
                # Create new admin
                print(f"Creating admin account: {admin_email}")
                admin_user = User(
                    email=admin_email.lower(),
                    password_hash=hash_password(admin_password),
                    business_name=admin_business_name,
                    timezone="UTC",
                    is_active=True,
                    is_verified=True,
                )
                # Set is_admin if the attribute exists
                if hasattr(admin_user, 'is_admin'):
                    admin_user.is_admin = True
                session.add(admin_user)
                await session.flush()
                
                # Create subscription for admin
                subscription = Subscription(
                    user_id=admin_user.id,
                    plan_type=PlanType.PRO,
                    status=SubscriptionStatus.ACTIVE,
                )
                session.add(subscription)
                print("Admin account created successfully!")
            
            await session.commit()
            print(f"\nAdmin credentials:")
            print(f"  Email: {admin_email}")
            print(f"  Password: {admin_password}")
            print(f"  Admin: True")
            
        except Exception as e:
            await session.rollback()
            print(f"Error creating admin account: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(create_admin())

