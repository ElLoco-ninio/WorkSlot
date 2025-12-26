"""Subscription management service."""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Subscription, User
from app.models.subscription import PlanType, SubscriptionStatus


class SubscriptionService:
    """Service for managing user subscriptions."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_subscription(self, user_id: UUID) -> Optional[Subscription]:
        """Get subscription for a user."""
        result = await self.db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def create_subscription(
        self,
        user_id: UUID,
        plan_type: PlanType = PlanType.FREE,
    ) -> Subscription:
        """Create a new subscription for a user."""
        subscription = Subscription(
            user_id=user_id,
            plan_type=plan_type,
            status=SubscriptionStatus.ACTIVE,
        )
        self.db.add(subscription)
        await self.db.flush()
        return subscription
    
    async def upgrade_plan(
        self,
        subscription: Subscription,
        new_plan: PlanType,
        stripe_subscription_id: Optional[str] = None,
        stripe_customer_id: Optional[str] = None,
    ) -> Subscription:
        """Upgrade a subscription to a new plan."""
        subscription.plan_type = new_plan
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.updated_at = datetime.utcnow()
        
        if stripe_subscription_id:
            subscription.stripe_subscription_id = stripe_subscription_id
        if stripe_customer_id:
            subscription.stripe_customer_id = stripe_customer_id
        
        # Set billing period for paid plans
        if new_plan != PlanType.FREE:
            subscription.current_period_start = datetime.utcnow()
            subscription.current_period_end = datetime.utcnow() + timedelta(days=30)
        
        await self.db.flush()
        return subscription
    
    async def cancel_subscription(
        self,
        subscription: Subscription,
        cancel_at_period_end: bool = True,
    ) -> Subscription:
        """Cancel a subscription."""
        if cancel_at_period_end:
            subscription.cancel_at_period_end = True
        else:
            subscription.status = SubscriptionStatus.CANCELED
            subscription.plan_type = PlanType.FREE
        
        subscription.updated_at = datetime.utcnow()
        await self.db.flush()
        return subscription
    
    async def activate_trial(
        self,
        subscription: Subscription,
        trial_days: int = 14,
    ) -> Subscription:
        """Activate a trial period for a subscription."""
        subscription.status = SubscriptionStatus.TRIALING
        subscription.plan_type = PlanType.BASIC
        subscription.current_period_start = datetime.utcnow()
        subscription.current_period_end = datetime.utcnow() + timedelta(days=trial_days)
        subscription.updated_at = datetime.utcnow()
        await self.db.flush()
        return subscription
    
    async def check_limits(self, subscription: Subscription) -> dict:
        """Check current usage against plan limits."""
        from sqlalchemy import func
        from app.models import APIKey, Booking
        
        # Count API keys
        api_keys_result = await self.db.execute(
            select(func.count(APIKey.id))
            .where(APIKey.user_id == subscription.user_id)
            .where(APIKey.is_active == True)
        )
        api_key_count = api_keys_result.scalar() or 0
        
        # Count bookings this month
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        bookings_result = await self.db.execute(
            select(func.count(Booking.id))
            .where(Booking.provider_id == subscription.user_id)
            .where(Booking.created_at >= month_start)
        )
        booking_count = bookings_result.scalar() or 0
        
        return {
            "api_keys": {
                "used": api_key_count,
                "limit": subscription.get_api_key_limit(),
                "remaining": max(0, subscription.get_api_key_limit() - api_key_count),
            },
            "bookings": {
                "used": booking_count,
                "limit": subscription.get_booking_limit(),
                "remaining": max(0, subscription.get_booking_limit() - booking_count),
            },
        }
    
    @staticmethod
    def get_plan_features(plan_type: PlanType) -> dict:
        """Get features for a plan type."""
        features = {
            PlanType.FREE: {
                "name": "Free",
                "price": 0,
                "api_keys": 0,
                "bookings_per_month": 0,
                "features": [
                    "Dashboard access",
                    "View booking history",
                ],
            },
            PlanType.BASIC: {
                "name": "Basic",
                "price": 19,
                "api_keys": 1,
                "bookings_per_month": 100,
                "features": [
                    "1 API key",
                    "100 bookings/month",
                    "Email notifications",
                    "Calendar widget",
                    "Basic support",
                ],
            },
            PlanType.PRO: {
                "name": "Pro",
                "price": 49,
                "api_keys": 5,
                "bookings_per_month": 1000,
                "features": [
                    "5 API keys",
                    "1000 bookings/month",
                    "Email notifications",
                    "Calendar widget",
                    "Priority support",
                    "Custom branding",
                    "Analytics",
                ],
            },
        }
        return features.get(plan_type, {})

