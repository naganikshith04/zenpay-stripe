# api/routes/customers.py
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

# Import models and dependencies
from db.session import get_db
from db.models import User, Customer
from dependencies import get_current_user
from models.request import CustomerCreate
from models.response import CustomerResponse
from zenpay_backend.zenpay_backend.app import CustomerDB

# Create router
router = APIRouter()

@router.post("/create", response_model=CustomerResponse)
def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new customer"""
    # Check if customer already exists
    db_customer = db.query(Customer).filter(
        Customer.user_id == current_user.id,
        Customer.id == customer.id
    ).first()
    
    # Convert metadata to JSON string
    metadata_str = json.dumps(customer.metadata) if customer.metadata else None
    
    # In create_customer function:
    if db_customer:
        # Update existing customer
        if customer.name is not None:
            db_customer.name = customer.name
        if customer.email is not None:
            db_customer.email = customer.email
        if customer.metadata is not None:
            db_customer.metadata_json = metadata_str  # Changed from metadata to metadata_json
    else:
        # Create new customer
        db_customer = CustomerDB(
            id=customer.id,
            user_id=current_user.id,
            name=customer.name,
            email=customer.email,
            metadata_json=metadata_str  # Changed from metadata to metadata_json
        )
    
    db.commit()
    db.refresh(db_customer)
    
    # Convert back to response model
    return {
        "id": db_customer.id,
        "name": db_customer.name,
        "email": db_customer.email,
        "metadata": json.loads(db_customer.metadata) if db_customer.metadata else None,
        "created_at": db_customer.created_at
    }

@router.get("/list", response_model=List[CustomerResponse])
def list_customers(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all customers"""
    customers = db.query(Customer).filter(
        Customer.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    result = []
    for customer in customers:
        result.append({
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "metadata": json.loads(customer.metadata) if customer.metadata else None,
            "created_at": customer.created_at
        })
    
    return result

@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific customer"""
    customer = db.query(Customer).filter(
        Customer.user_id == current_user.id,
        Customer.id == customer_id
    ).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "metadata": json.loads(customer.metadata_json) if customer.metadata_json else None,  # Changed from metadata to metadata_json
        "created_at": customer.created_at
    }