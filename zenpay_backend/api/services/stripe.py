# zenpay_backend/services/stripe.py

import stripe
from sqlalchemy.orm import Session

from api.core.config import settings
from api.db.crud import usage as usage_crud
from api.db.models import UsageEvent, Customer
from sqlalchemy.orm import Session

import logging

logger = logging.getLogger(__name__)

# Initialize Stripe with our API key
stripe.api_key = ""


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
    product = usage_event.product

    # We need all these to report to Stripe
    if not (
        user.stripe_connect_id
        and customer.stripe_customer_id
        and product.stripe_price_id
    ):
        return False

    try:
        # Create usage record in Stripe
        response = stripe.SubscriptionItem.create_usage_record(
            # This assumes the subscription_item_id is stored in stripe_price_id
            # You may need a different model structure for this
            product.stripe_price_id,
            quantity=int(usage_event.quantity),
            timestamp=int(usage_event.timestamp.timestamp()),
            action="increment",
            stripe_account=user.stripe_connect_id,
        )

        # Update the usage event as reported
        usage_crud.mark_usage_as_reported(db, usage_event.id, response.id)
        return True
    except Exception as e:
        # In a real system, you'd want to log this error
        print(f"Error reporting usage to Stripe: {e}")
        return False


def ensure_stripe_customer(db: Session, db_customer: Customer) -> Customer:
    try:
        # Check if Stripe customer exists
        stripe.Customer.retrieve(db_customer.stripe_customer_id)
    except stripe.error.InvalidRequestError:
        # Stripe customer missing — recreate it
        stripe_customer = stripe.Customer.create(
            name=db_customer.name,
            email=db_customer.email,
            metadata=db_customer.metadata_json or {},
        )
        db_customer.stripe_customer_id = stripe_customer.id
        db.commit()
        db.refresh(db_customer)
    return db_customer


def create_stripe_customer(
    name: str, email: str, metadata: dict, user_stripe_account: str
):
    return stripe.Customer.create(
        name=name,
        email=email,
        metadata=metadata,
        stripe_account=user_stripe_account,
    )


def create_stripe_product_and_price(
    user_stripe_account: str, product_name: str, unit_name: str, price_per_unit: float
):
    """
    Create a product and price in Stripe
    """
    # Create product
    product = stripe.Product.create(
        name=product_name, stripe_account=user_stripe_account
    )

    # Create price
    price = stripe.Price.create(
        product=product.id,
        unit_amount=int(price_per_unit * 100),  # Convert to cents
        currency="usd",
        recurring={"usage_type": "metered"},
        stripe_account=user_stripe_account,
    )

    return product, price


def create_metered_price(stripe_account, product_id, unit_amount, currency="usd"):
    # Create a meter first
    meter = stripe.billing.Meter.create(
        name="usage",
        aggregation_method="sum",
        event_name="usage_event",  # Make sure this matches your reported usage
        stripe_account=stripe_account,
    )

    # Now create the price using the meter
    return stripe.Price.create(
        unit_amount=int(unit_amount * 100),
        currency=currency,
        recurring={"interval": "month", "usage_type": "metered"},
        product=product_id,
        meter=meter.id,
        stripe_account=stripe_account,
    )


def update_product_name(product_id: str, new_name: str, user_stripe_account: str):
    """
    Update the name of a Stripe product.
    """
    stripe.Product.modify(product_id, name=new_name, stripe_account=user_stripe_account)
