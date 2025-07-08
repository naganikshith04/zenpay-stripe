# zenpay_backend/api/v1/customers.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from api.db.crud.customers import (
    create_customer,
    get_customer,
    get_customers,
    delete_customer,
    update_customer,
)
from api.db.session import get_db
from dependencies import get_current_user_by_api_key
from models.request import CustomerCreate, CustomerUpdate
from models.response import CustomerResponse
from api.db.models import User

router = APIRouter()

@router.post("", response_model=CustomerResponse)
def create_new_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_by_api_key),
):
    db_customer = create_customer(
        db=db,
        user_id=user.id,
        customer_id=customer.id,
        name=customer.name,
        email=customer.email,
        metadata=customer.metadata,
    )
    return db_customer

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

@router.patch("/{customer_id}", response_model=CustomerResponse)
def update_existing_customer(
    customer_id: str,
    customer: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_by_api_key),
):
    """Update a customer"""
    updated_customer = update_customer(
        db=db,
        user_id=current_user.id,
        customer_id=customer_id,
        name=customer.name,
        email=customer.email,
        metadata=customer.metadata,
    )
    if not updated_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return updated_customer

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
