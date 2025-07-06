# zenpay_backend/api/v1/credits.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from api.db.crud.credits import add_credits, use_credits, get_credit_balance, get_credit_transactions
from api.db.crud.customers import get_customer
from api.db.session import get_db
from dependencies import get_current_user as get_current_user_by_api_key
from models.request import CreditAdd, CreditTopUpRequest
from models.response import CreditTransactionResponse, CreditBalance
from api.db.models import User
from core.exceptions import CustomerNotFoundError

router = APIRouter()

@router.post("/add", response_model=CreditTransactionResponse)
def add_customer_credits(
    credit_data: CreditAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_by_api_key)
):
    """Add credits to a customer account"""
    try:
        transaction = add_credits(
            db=db,
            user_id=current_user.id,
            customer_id=credit_data.customer_id,
            amount=credit_data.amount,
            description=credit_data.description
        )
        return transaction
    except CustomerNotFoundError:
        raise HTTPException(status_code=404, detail="Customer not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/use", response_model=CreditTransactionResponse)
def use_customer_credits(
    credit_data: CreditAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_by_api_key)
):
    """Use (deduct) credits from a customer account"""
    try:
        transaction = use_credits(
            db=db,
            user_id=current_user.id,
            customer_id=credit_data.customer_id,
            amount=credit_data.amount,
            description=credit_data.description
        )
        return transaction
    except CustomerNotFoundError:
        raise HTTPException(status_code=404, detail="Customer not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/balance/{customer_id}", response_model=CreditBalance)
def get_customer_credit_balance(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_by_api_key)
):
    """Get current credit balance for a customer"""
    # Verify customer exists
    customer = get_customer(db, current_user.id, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    balance = get_credit_balance(db, current_user.id, customer_id)
    return CreditBalance(customer_id=customer_id, balance=balance)

@router.get("/transactions/{customer_id}", response_model=List[CreditTransactionResponse])
def get_customer_credit_transactions(
    customer_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_by_api_key)
):
    """Get credit transaction history for a customer"""
    # Verify customer exists
    customer = get_customer(db, current_user.id, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    transactions = get_credit_transactions(
        db, current_user.id, customer_id, skip, limit
    )
    return transactions

@router.post("/topup", response_model=CreditTransactionResponse)
def topup_credits(
    topup_data: CreditTopUpRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_by_api_key)
):
    transaction = add_credits(
        db=db,
        user_id=current_user.id,
        customer_id=topup_data.customer_id,
        amount=topup_data.amount
    )
    return CreditTransactionResponse(
        id=transaction.id,
        customer_id=transaction.customer_id,
        amount=transaction.amount,
        timestamp=transaction.timestamp,
        type=transaction.type
    )
