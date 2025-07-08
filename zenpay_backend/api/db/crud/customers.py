# zenpay_backend/db/crud/customers.py
from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
import stripe

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
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer with this ID already exists",
        )

    # Create a customer in Stripe
    if not stripe_customer_id:
        stripe_customer = stripe.Customer.create(
            name=name,
            email=email,
            metadata={"user_id": user_id, "customer_id": customer_id}
        )
        stripe_customer_id = stripe_customer.id

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

def update_customer(
    db: Session,
    user_id: str,
    customer_id: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[Customer]:
    """
    Update a customer's details in the local DB and Stripe.
    """
    customer = db.query(Customer).filter(
        Customer.user_id == user_id,
        Customer.id == customer_id
    ).first()

    if not customer:
        return None

    # Update local database
    if name is not None:
        customer.name = name
    if email is not None:
        customer.email = email
    if metadata is not None:
        customer.metadata = metadata

    # Update Stripe customer
    if customer.stripe_customer_id:
        stripe.Customer.modify(
            customer.stripe_customer_id,
            name=customer.name,
            email=customer.email,
            metadata={"user_id": user_id, "customer_id": customer.id}
        )

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
        if customer.stripe_customer_id:
            try:
                stripe.Customer.delete(customer.stripe_customer_id)
            except stripe.error.InvalidRequestError:
                # Customer might have been already deleted in Stripe
                pass

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