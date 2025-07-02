# zenpay_backend/db/crud/customers.py
from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session

from ..models import Customer, User

def create_customer(
    db: Session,
    user_id: str,
    customer_id: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    stripe_customer_id: Optional[str] = None
) -> Customer:
    """
    Create a new customer or update if exists
    """
    # Check if customer already exists
    customer = db.query(Customer).filter(
        Customer.user_id == user_id,
        Customer.id == customer_id
    ).first()
    
    if customer:
        # Update existing customer
        if name is not None:
            customer.name = name
        if email is not None:
            customer.email = email
        if metadata is not None:
            customer.metadata = metadata
        if stripe_customer_id is not None:
            customer.stripe_customer_id = stripe_customer_id
    else:
        # Create new customer
        customer = Customer(
            id=customer_id,
            user_id=user_id,
            name=name,
            email=email,
            metadata=metadata,
            stripe_customer_id=stripe_customer_id
        )
        db.add(customer)
    
    db.commit()
    db.refresh(customer)
    return customer

def get_customer(db: Session, user_id: str, customer_id: str) -> Optional[Customer]:
    """
    Get a customer by ID
    """
    return db.query(Customer).filter(
        Customer.user_id == user_id,
        Customer.id == customer_id
    ).first()

def get_customers(db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[Customer]:
    """
    Get all customers for a user
    """
    return db.query(Customer).filter(
        Customer.user_id == user_id
    ).offset(skip).limit(limit).all()

def delete_customer(db: Session, user_id: str, customer_id: str) -> bool:
    """
    Delete a customer
    """
    customer = db.query(Customer).filter(
        Customer.user_id == user_id,
        Customer.id == customer_id
    ).first()
    
    if customer:
        db.delete(customer)
        db.commit()
        return True
    return False

def update_stripe_customer_id(db: Session, user_id: str, customer_id: str, stripe_customer_id: str) -> Optional[Customer]:
    """
    Update a customer's Stripe ID
    """
    customer = db.query(Customer).filter(
        Customer.user_id == user_id,
        Customer.id == customer_id
    ).first()
    
    if customer:
        customer.stripe_customer_id = stripe_customer_id
        db.commit()
        db.refresh(customer)
    
    return customer