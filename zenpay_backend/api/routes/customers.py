# zenpay_backend/api/v1/customers.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import stripe

from api.db.crud.customers import (
    create_customer,
    get_customer,
    get_customers,
    delete_customer,
)
from api.db.session import get_db
from dependencies import get_current_user as get_current_user_by_api_key
from models.request import CustomerCreate
from models.response import CustomerResponse
from api.db.models import User, Customer

router = APIRouter()

from services.stripe import create_stripe_customer  # Add this import
import logging

logger = logging.getLogger(__name__)


def get_customer_by_id(db: Session, customer_id: str):
    return db.query(Customer).filter(Customer.id == customer_id).first()


def get_customer_by_email(db: Session, user_id: str, email: str):
    return (
        db.query(Customer)
        .filter(Customer.user_id == user_id, Customer.email == email)
        .first()
    )


from services.stripe import ensure_stripe_customer


@router.post("", response_model=CustomerResponse)
def create_new_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_by_api_key),
):
    # Check if customer already exists
    db_customer = db.query(Customer).filter_by(id=customer.id, user_id=user.id).first()

    if db_customer:
        db_customer = ensure_stripe_customer(db, db_customer)
        return CustomerResponse(
            id=db_customer.id,
            name=db_customer.name,
            email=db_customer.email,
            metadata=db_customer.metadata_json or {},
            created_at=db_customer.created_at
        )


    # Create Stripe customer
    stripe_customer = stripe.Customer.create(
        name=customer.name, email=customer.email, metadata=customer.metadata or {}
    )

    # Save to DB
    new_customer = Customer(
        id=customer.id,
        name=customer.name,
        email=customer.email,
        metadata_json=customer.metadata,
        stripe_customer_id=stripe_customer.id,
        user_id=user.id,
    )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return CustomerResponse(
        id=new_customer.id,
        name=new_customer.name,
        email=new_customer.email,
        metadata=new_customer.metadata_json or {},
        created_at=new_customer.created_at,
    )


@router.get("/{customer_id}", response_model=CustomerResponse)
def read_customer(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_by_api_key),
):
    """Get a specific customer by ID"""
    db_customer = get_customer(db=db, user_id=current_user.id, customer_id=customer_id)
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return db_customer


@router.get("", response_model=List[CustomerResponse])
def read_customers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_by_api_key),
):
    """Get all customers for the current user"""
    customers = get_customers(db=db, user_id=current_user.id, skip=skip, limit=limit)
    return customers


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_customer(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_by_api_key),
):
    """Delete a customer"""
    success = delete_customer(db=db, user_id=current_user.id, customer_id=customer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Customer not found")
    return None
