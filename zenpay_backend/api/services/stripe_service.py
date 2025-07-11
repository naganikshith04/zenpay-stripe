# zenpay_backend/services/stripe.py

from typing import Optional
import stripe
from sqlalchemy.orm import Session

from api.core.config import settings
from api.db.crud import usage as usage_crud
from api.db.models import UsageEvent, Customer
from sqlalchemy.orm import Session

import logging

logger = logging.getLogger(__name__)

# Initialize Stripe with our API key
stripe.api_key = settings.STRIPE_API_KEY

def _get_or_create_meter(event_name: str, display_name: str):
    """
    Helper to get or create a Stripe Meter.
    """
    try:
        # Try to retrieve an existing meter
        meters = stripe.billing.Meter.list(limit=100) # Fetch a reasonable number of meters
        for meter in meters.data:
            if meter.event_name == event_name:
                return meter
    except stripe.error.StripeError as e:
        logger.warning(f"Could not retrieve meter {event_name}: {e}")

    # If not found, create a new meter
    try:
        meter = stripe.billing.Meter.create(
            display_name=display_name,
            event_name=event_name,
            default_aggregation={"formula": "sum"},
            customer_mapping={"event_payload_key": "stripe_customer_id", "type": "by_id"},
            value_settings={"event_payload_key": "value"},
        )
        logger.info(f"Created new Stripe Meter: {meter.id}")
        return meter
    except stripe.error.StripeError as e:
        logger.error(f"Error creating Stripe Meter {event_name}: {e}")
        raise

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
    name: str, email: str, metadata: dict
):
    return stripe.Customer.create(
        name=name,
        email=email,
        metadata=metadata,
    )


def create_stripe_product_and_price(
    product_name: str, price_per_unit: float, product_code: str, event_name: str, quantity_payload_key: str
):
    """
    Create a product and metered price in Stripe
    """
    # Ensure the meter exists
    meter = _get_or_create_meter(event_name=event_name, display_name=product_name + " Usage")

    # Create product
    product = stripe.Product.create(
        name=product_name
    )

    # Create metered price
    price_data = {
        "product": product.id,
        "unit_amount": int(price_per_unit * 100),  # Convert to cents
        "currency": "usd",
        "recurring": {"interval": "month", "usage_type": "metered", "meter": meter.id},
        "billing_scheme": "per_unit",
        "lookup_key": f"{event_name}_{product_code}", # Use a unique lookup key
    }

    price = stripe.Price.create(**price_data)

    return product, price


def update_stripe_product_price(
    stripe_product_id: str, old_stripe_price_id: str, new_price_per_unit: float
):
    """
    Deactivates the old price and creates a new price for a Stripe product.
    """
    # Deactivate the old price
    if old_stripe_price_id:
        try:
            stripe.Price.modify(old_stripe_price_id, active=False)
        except stripe.error.InvalidRequestError as e:
            # Ignore if the price is already archived
            if "archived" not in str(e).lower():
                raise

    # Create a new price
    price_data = {
        "product": stripe_product_id,
        "unit_amount": int(new_price_per_unit * 100),  # Convert to cents
        "currency": "usd",
        "recurring": {"interval": "month"},
    }

    new_price = stripe.Price.create(**price_data)

    return new_price

def update_product_name(product_id: str, new_name: str):
    """
    Update the name of a Stripe product.
    """
    stripe.Product.modify(product_id, name=new_name)

def get_subscription_item_id(stripe_customer_id: str, stripe_price_id: str) -> Optional[str]:
    """
    Retrieves the subscription item ID for a given customer and price.
    """
    try:
        subscriptions = stripe.Subscription.list(customer=stripe_customer_id, status='active')
        for subscription in subscriptions.auto_paging_iter():
            for item in subscription.items.data:
                if item.price.id == stripe_price_id:
                    return item.id
        return None
    except Exception as e:
        logger.error(f"Error getting subscription item ID: {e}")
        return None
