# zenpay_backend/db/crud/credits.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List

from ..models import CreditTransaction, Customer, User
from ...core.exceptions import CustomerNotFoundError

def add_credits(
    db: Session, 
    user_id: str,
    customer_id: str,
    amount: float,
    description: Optional[str] = None
) -> CreditTransaction:
    """Add credits to a customer account"""
    # Verify customer exists
    customer = db.query(Customer).filter(
        Customer.user_id == user_id,
        Customer.id == customer_id
    ).first()
    
    if not customer:
        raise CustomerNotFoundError(f"Customer {customer_id} not found")
    
    # Create credit transaction
    transaction = CreditTransaction(
        user_id=user_id,
        customer_id=customer_id,
        amount=amount,  # Positive amount = credit addition
        description=description or "Credit addition"
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return transaction

def use_credits(
    db: Session,
    user_id: str,
    customer_id: str,
    amount: float,
    description: Optional[str] = None
) -> CreditTransaction:
    """Use credits (deduct from balance)"""
    # Verify customer exists
    customer = db.query(Customer).filter(
        Customer.user_id == user_id,
        Customer.id == customer_id
    ).first()
    
    if not customer:
        raise CustomerNotFoundError(f"Customer {customer_id} not found")
    
    # Check if sufficient credits are available
    balance = get_credit_balance(db, user_id, customer_id)
    if balance < amount:
        raise ValueError(f"Insufficient credits: balance {balance}, requested {amount}")
    
    # Create credit transaction (negative = deduction)
    transaction = CreditTransaction(
        user_id=user_id,
        customer_id=customer_id,
        amount=-amount,  # Negative amount = credit deduction
        description=description or "Credit usage"
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return transaction

def get_credit_balance(
    db: Session,
    user_id: str,
    customer_id: str
) -> float:
    """Get current credit balance for a customer"""
    # Sum all transactions for this customer
    balance = db.query(func.sum(CreditTransaction.amount)).filter(
        CreditTransaction.user_id == user_id,
        CreditTransaction.customer_id == customer_id
    ).scalar()
    
    return float(balance or 0)

def get_credit_transactions(
    db: Session,
    user_id: str,
    customer_id: str,
    skip: int = 0,
    limit: int = 100
) -> List[CreditTransaction]:
    """Get transaction history for a customer"""
    return db.query(CreditTransaction).filter(
        CreditTransaction.user_id == user_id,
        CreditTransaction.customer_id == customer_id
    ).order_by(CreditTransaction.timestamp.desc()).offset(skip).limit(limit).all()