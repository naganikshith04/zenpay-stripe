# zenpay_backend/db/crud/usage.py
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

import stripe

from ..models import UsageEvent, Product, Customer
from core.exceptions import CustomerNotFoundError, ProductNotFoundError, InsufficientCreditsError
from .credits import get_credit_balance, use_credits

def track_usage(
    db: Session,
    user_id: str,
    customer_id: str,
    product_code: str,
    quantity: float,
    idempotency_key: Optional[str] = None,
    use_customer_credits: bool = True
) -> UsageEvent:
    """
    Track usage of a product and optionally deduct credits
    """
    # Check if customer exists
    customer = db.query(Customer).filter(
        Customer.user_id == user_id,
        Customer.id == customer_id
    ).first()
    
    if not customer:
        raise CustomerNotFoundError(f"Customer {customer_id} not found")
    
    # Find the product by code
    product = db.query(Product).filter(
        Product.user_id == user_id,
        Product.code == product_code
    ).first()
    
    if not product:
        raise ProductNotFoundError(f"Product {product_code} not found")
    
    # Check idempotency key if provided
    if idempotency_key:
        existing = db.query(UsageEvent).filter(
            UsageEvent.user_id == user_id,
            UsageEvent.idempotency_key == idempotency_key
        ).first()
        
        if existing:
            return existing
    
    # Calculate cost
    cost = quantity * product.price_per_unit
    
    # Check if using credits and if sufficient credits are available
    if use_customer_credits:
        balance = get_credit_balance(db, user_id, customer_id)
        if balance < cost:
            raise InsufficientCreditsError(f"Insufficient credits: balance {balance}, required {cost}")
        
        # Deduct credits
        use_credits(
            db=db,
            user_id=user_id,
            customer_id=customer_id,
            amount=cost,
            description=f"Usage: {product.name} x {quantity}"
        )
    
    # Create usage event
    usage_event = UsageEvent(
        user_id=user_id,
        customer_id=customer_id,
        product_id=product.id,
        quantity=quantity,
        idempotency_key=idempotency_key
    )
    
    db.add(usage_event)
    db.commit()
    db.refresh(usage_event)
    
    return usage_event


def report_usage_to_stripe(stripe_subscription_item_id: str, quantity: int, timestamp: datetime):
    print(f"[Stripe] Reporting usage: subscription_item={stripe_subscription_item_id}, quantity={quantity}, time={timestamp}")
    try:
        response = stripe.SubscriptionItem.create_usage_record(
            stripe_subscription_item_id,
            quantity=quantity,
            timestamp=int(timestamp.timestamp()),
            action='increment',
        )
        print(f"[Stripe] Usage record response: {response}")
    except Exception as e:
        print(f"[Stripe] Stripe error: {e}")
        raise

    
    
def get_usage_events(
    db: Session,
    user_id: str,
    customer_id: Optional[str] = None,
    product_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
) -> List[UsageEvent]:
    """
    Get usage events with optional filtering
    """
    query = db.query(UsageEvent).filter(UsageEvent.user_id == user_id)
    
    if customer_id:
        query = query.filter(UsageEvent.customer_id == customer_id)
    
    if product_id:
        query = query.filter(UsageEvent.product_id == product_id)
    
    if start_date:
        query = query.filter(UsageEvent.timestamp >= start_date)
    
    if end_date:
        query = query.filter(UsageEvent.timestamp <= end_date)
    
    return query.order_by(UsageEvent.timestamp.desc()).offset(skip).limit(limit).all()