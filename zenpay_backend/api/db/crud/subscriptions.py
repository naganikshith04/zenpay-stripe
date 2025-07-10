from sqlalchemy.orm import Session
from typing import Optional, List
import stripe
import time

from ..models import Subscription, Customer, Product
from core.exceptions import CustomerNotFoundError, ProductNotFoundError

def create_subscription(
    db: Session,
    user_id: str,
    customer_id: str,
    product_id: str
) -> Subscription:
    """
    Create a new subscription in the local DB and Stripe.
    """
    customer = db.query(Customer).filter(Customer.id == customer_id, Customer.user_id == user_id).first()
    if not customer or not customer.stripe_customer_id:
        raise CustomerNotFoundError(f"Customer {customer_id} not found or missing Stripe ID")

    product = db.query(Product).filter(Product.id == product_id, Product.user_id == user_id).first()
    if not product or not product.stripe_price_id:
        raise ProductNotFoundError(f"Product {product_id} not found or missing Stripe Price ID")

    # Create subscription in Stripe
    try:
        # Calculate a future timestamp for billing_cycle_anchor
        future_timestamp = int(time.time()) + 60 # 60 seconds in the future

        stripe_subscription = stripe.Subscription.create(
            customer=customer.stripe_customer_id,
            items=[{"price": product.stripe_price_id}],
            
        )
        stripe_subscription_item_id = stripe_subscription['items']['data'][0]['id']
    except stripe.error.StripeError as e:
        raise Exception(f"Stripe error creating subscription: {e}")

    # Create subscription in local DB
    db_subscription = Subscription(
        user_id=user_id,
        customer_id=customer.id,
        product_id=product.id,
        stripe_subscription_id=stripe_subscription.id,
        stripe_subscription_item_id=stripe_subscription_item_id,
        status=stripe_subscription.status
    )
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)

    return db_subscription

def get_subscription_by_customer_and_product(
    db: Session,
    user_id: str,
    customer_id: str,
    product_id: str
) -> Optional[Subscription]:
    """
    Get a subscription by customer and product IDs.
    """
    return db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.customer_id == customer_id,
        Subscription.product_id == product_id
    ).first()

def get_subscription_by_stripe_item_id(
    db: Session,
    user_id: str,
    stripe_subscription_item_id: str
) -> Optional[Subscription]:
    """
    Get a subscription by its Stripe subscription item ID.
    """
    return db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.stripe_subscription_item_id == stripe_subscription_item_id
    ).first()
