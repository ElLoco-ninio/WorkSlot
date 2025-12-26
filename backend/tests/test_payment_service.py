import pytest
from unittest.mock import MagicMock, patch
from app.services.payment_service import PaymentService
from app.models.subscription import PlanType
from app.models import User
from fastapi import HTTPException

@pytest.mark.asyncio
async def test_create_customer_new():
    """Test creating a new customer for a user without one."""
    user = MagicMock(spec=User)
    user.id = "uuid-123"
    user.email = "test@example.com"
    user.business_name = "Test Biz"
    user.subscription.stripe_customer_id = None

    with patch('stripe.Customer.create') as mock_create:
        mock_create.return_value.id = "cus_123"
        
        customer_id = await PaymentService.create_customer(user)
        
        assert customer_id == "cus_123"
        mock_create.assert_called_once_with(
            email="test@example.com",
            metadata={"user_id": "uuid-123", "business_name": "Test Biz"}
        )

@pytest.mark.asyncio
async def test_create_customer_existing():
    """Test retrieving existing customer id."""
    user = MagicMock(spec=User)
    user.subscription.stripe_customer_id = "cus_existing"
    
    customer_id = await PaymentService.create_customer(user)
    assert customer_id == "cus_existing"

@pytest.mark.asyncio
async def test_create_checkout_session():
    """Test successful checkout session creation."""
    user = MagicMock(spec=User)
    user.id = "uuid-123"
    plan = PlanType.PRO
    customer_id = "cus_123"
    
    with patch('stripe.checkout.Session.create') as mock_create:
        mock_create.return_value.url = "https://stripe.com/checkout/123"
        
        url = await PaymentService.create_checkout_session(user, plan, customer_id)
        
        assert url == "https://stripe.com/checkout/123"
        mock_create.assert_called_once()
        args = mock_create.call_args[1]
        assert args['customer'] == customer_id
        assert args['mode'] == 'subscription'
        assert args['metadata']['user_id'] == "uuid-123"
        assert args['metadata']['plan_type'] == "pro"

@pytest.mark.asyncio
async def test_webhook_construction():
    """Test webhook event construction."""
    payload = b'events'
    sig = 'signature'
    
    with patch('stripe.Webhook.construct_event') as mock_construct:
        mock_construct.return_value = {"type": "test"}
        
        event = await PaymentService.construct_webhook_event(payload, sig)
        
        assert event == {"type": "test"}
        mock_construct.assert_called_once()
