# zenpay_backend/db/crud/usage.py
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from ..models import UsageEvent, Feature, Customer
from ...core.exceptions import CustomerNotFoundError, FeatureNotFoundError, InsufficientCreditsError
from .credits import get_credit_balance, use_credits

def track_usage(
    db: Session,
    user_id: str,
    customer_id: str,
    feature_code: str,
    quantity: float,
    idempotency_key: Optional[str] = None,
    use_customer_credits: bool = True
) -> UsageEvent:
    """
    Track usage of a feature and optionally deduct credits
    """
    # Check if customer exists
    customer = db.query(Customer).filter(
        Customer.user_id == user_id,
        Customer.id == customer_id
    ).first()
    
    if not customer:
        raise CustomerNotFoundError(f"Customer {customer_id} not found")
    
    # Find the feature by code
    feature = db.query(Feature).filter(
        Feature.user_id == user_id,
        Feature.code == feature_code
    ).first()
    
    if not feature:
        raise FeatureNotFoundError(f"Feature {feature_code} not found")
    
    # Check idempotency key if provided
    if idempotency_key:
        existing = db.query(UsageEvent).filter(
            UsageEvent.user_id == user_id,
            UsageEvent.idempotency_key == idempotency_key
        ).first()
        
        if existing:
            return existing
    
    # Calculate cost
    cost = quantity * feature.price_per_unit
    
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
            description=f"Usage: {feature.name} x {quantity}"
        )
    
    # Create usage event
    usage_event = UsageEvent(
        user_id=user_id,
        customer_id=customer_id,
        feature_id=feature.id,
        quantity=quantity,
        idempotency_key=idempotency_key
    )
    
    db.add(usage_event)
    db.commit()
    db.refresh(usage_event)
    
    return usage_event

def get_usage_events(
    db: Session,
    user_id: str,
    customer_id: Optional[str] = None,
    feature_id: Optional[str] = None,
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
    
    if feature_id:
        query = query.filter(UsageEvent.feature_id == feature_id)
    
    if start_date:
        query = query.filter(UsageEvent.timestamp >= start_date)
    
    if end_date:
        query = query.filter(UsageEvent.timestamp <= end_date)
    
    return query.order_by(UsageEvent.timestamp.desc()).offset(skip).limit(limit).all()