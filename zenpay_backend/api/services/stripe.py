# zenpay_backend/services/stripe.py

import stripe
from sqlalchemy.orm import Session

from zenpay_backend.core.config import settings
from zenpay_backend.db.crud import usage as usage_crud
from zenpay_backend.db.models import UsageEvent

# Initialize Stripe with our API key
stripe.api_key = settings.STRIPE_API_KEY

async def report_usage_to_stripe(db: Session, usage_event_id: str) -> bool:
    """
    Report a usage event to Stripe
    """
    # Get the usage event
    usage_event = db.query(UsageEvent).filter(UsageEvent.id == usage_event_id).first()
    if not usage_event or usage_event.reported_to_stripe:
        return False
    
    # Get the related data
    user = usage_event.user
    customer = usage_event.customer
    feature = usage_event.feature
    
    # We need all these to report to Stripe
    if not (user.stripe_connect_id and customer.stripe_customer_id and feature.stripe_price_id):
        return False
    
    try:
        # Create usage record in Stripe
        response = stripe.SubscriptionItem.create_usage_record(
            # This assumes the subscription_item_id is stored in stripe_price_id
            # You may need a different model structure for this
            feature.stripe_price_id,  
            quantity=int(usage_event.quantity),
            timestamp=int(usage_event.timestamp.timestamp()),
            action='increment',
            stripe_account=user.stripe_connect_id
        )
        
        # Update the usage event as reported
        usage_crud.mark_usage_as_reported(db, usage_event.id, response.id)
        return True
    except Exception as e:
        # In a real system, you'd want to log this error
        print(f"Error reporting usage to Stripe: {e}")
        return False

def create_stripe_customer(user_stripe_account: str, customer_name: str, customer_email: str = None):
    """
    Create a customer in Stripe
    """
    return stripe.Customer.create(
        name=customer_name,
        email=customer_email,
        stripe_account=user_stripe_account
    )

def create_stripe_product_and_price(
    user_stripe_account: str,
    product_name: str,
    unit_name: str,
    price_per_unit: float
):
    """
    Create a product and price in Stripe
    """
    # Create product
    product = stripe.Product.create(
        name=product_name,
        stripe_account=user_stripe_account
    )
    
    # Create price
    price = stripe.Price.create(
        product=product.id,
        unit_amount=int(price_per_unit * 100),  # Convert to cents
        currency="usd",
        recurring={"usage_type": "metered"},
        stripe_account=user_stripe_account
    )
    
    return product, price