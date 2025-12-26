"""Payment service utilizing Stripe."""
import stripe
from typing import Optional, Dict, Any
from fastapi import HTTPException, status

from app.core.config import settings
from app.models import User
from app.models.subscription import PlanType

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentService:
    """Service for handling payments via Stripe."""
    
    @staticmethod
    async def create_customer(user: User) -> str:
        """
        Create a Stripe customer for the user.
        If user already has a stripe_customer_id, return it.
        """
        if user.subscription and user.subscription.stripe_customer_id:
            return user.subscription.stripe_customer_id
            
        try:
            customer = stripe.Customer.create(
                email=user.email,
                metadata={
                    "user_id": str(user.id),
                    "business_name": user.business_name or ""
                }
            )
            return customer.id
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Payment provider error: {str(e)}"
            )

    @staticmethod
    async def create_checkout_session(
        user: User, 
        plan_type: PlanType,
        customer_id: str
    ) -> str:
        """
        Create a checkout session for subscription upgrade.
        Returns the checkout URL.
        """
        # Map plan types to Stripe Price IDs (configured in settings or here)
        # For a real app, these should be in settings/env vars
        price_mapping = {
            PlanType.BASIC: "price_basic_123", # Replace with env var or constant in production
            PlanType.PRO: "price_pro_456"
        }
        
        # In a real scenario, use settings.STRIPE_PRICE_ID_BASIC, etc.
        # Fallback for dev if not set, though this will fail on real Stripe call if invalid
        price_id = getattr(settings, f"STRIPE_PRICE_ID_{plan_type.name}", None)
        if not price_id:
             # Basic fallback logic for demonstration if env vars missing, 
             # likely won't work without real IDs but prevents code crash
             price_id = f"price_{plan_type.value}_mock" 

        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f"{settings.FRONTEND_URL}/settings?session_id={{CHECKOUT_SESSION_ID}}&success=true",
                cancel_url=f"{settings.FRONTEND_URL}/settings?canceled=true",
                metadata={
                    "user_id": str(user.id),
                    "plan_type": plan_type.value
                }
            )
            if not session.url:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate checkout URL"
                )
            return session.url
            
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Payment provider error: {str(e)}"
            )

    @staticmethod
    async def construct_webhook_event(
        payload: bytes, 
        sig_header: str
    ) -> stripe.Event:
        """Verify and construct webhook event."""
        try:
            return stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payload"
            )
        except stripe.error.SignatureVerificationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature"
            )
