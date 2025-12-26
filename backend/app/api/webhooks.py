"""Stripe webhook endpoints."""
from fastapi import APIRouter, Request, Header, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.services.payment_service import PaymentService
from app.services.subscription_service import SubscriptionService
from app.models.subscription import PlanType
from app.models import User

router = APIRouter()

@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle Stripe webhooks."""
    payload = await request.body()
    
    try:
        event = await PaymentService.construct_webhook_event(payload, stripe_signature)
    except HTTPException as e:
        raise e

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        await handle_checkout_completed(session, db)
        
    return {"status": "success"}

async def handle_checkout_completed(session: dict, db: AsyncSession):
    """Handle successful checkout session."""
    user_id = session.get("metadata", {}).get("user_id")
    plan_type_str = session.get("metadata", {}).get("plan_type")
    
    if not user_id or not plan_type_str:
        # Log error
        return

    try:
        plan_type = PlanType(plan_type_str)
    except ValueError:
        return

    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.subscription:
        return

    # Update subscription
    sub_service = SubscriptionService(db)
    await sub_service.upgrade_plan(
        user.subscription, 
        plan_type,
        stripe_subscription_id=session.get("subscription"),
        stripe_customer_id=session.get("customer")
    )
    await db.commit()
