# zenpay_backend/api/routes/usage.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from zenpay_backend.api.dependencies import get_db, get_current_user_by_api_key
from zenpay_backend.db.models import User
from zenpay_backend.db.crud import usage as usage_crud, customers as customers_crud
from zenpay_backend.api.models.request import UsageTrack
from zenpay_backend.api.models.response import UsageEventBase
from zenpay_backend.services import stripe as stripe_service

router = APIRouter()

@router.post("/track", response_model=UsageEventBase)
async def track_usage(
    data: UsageTrack,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_by_api_key)
):
    """
    Track usage for a customer's feature
    """
    # Check if customer exists
    customer = customers_crud.get_customer(db, current_user.id, data.customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {data.customer_id} not found"
        )
    
    # Create usage event
    usage_event = usage_crud.create_usage_event(
        db=db,
        user_id=current_user.id,
        customer_id=data.customer_id,
        feature_code=data.feature,
        quantity=data.quantity,
        idempotency_key=data.idempotency_key
    )
    
    if not usage_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature with code {data.feature} not found"
        )
    
    # Return usage event with feature code instead of ID
    result = UsageEventBase(
        id=usage_event.id,
        customer_id=usage_event.customer_id,
        feature=usage_event.feature.code,
        quantity=usage_event.quantity,
        timestamp=usage_event.timestamp
    )
    
    # Asynchronously report to Stripe if possible
    if current_user.stripe_connect_id and customer.stripe_customer_id and usage_event.feature.stripe_price_id:
        try:
            # This would be better handled by a background task
            await stripe_service.report_usage_to_stripe(db, usage_event.id)
        except Exception:
            # Log the error but don't fail the request
            pass
    
    return result