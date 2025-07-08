# zenpay_backend/api/v1/usage.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from api.db.session import get_db
from api.dependencies import get_current_user_by_api_key
from api.db.models import User
from api.models.request import UsageTrack
from models.response import UsageEventResponse
from api.db.crud.usage import track_usage, get_usage_events
from core.exceptions import CustomerNotFoundError, ProductNotFoundError, InsufficientCreditsError
from api.db.crud.products import get_product_by_code

router = APIRouter()

@router.post("/track", response_model=UsageEventResponse)
def record_usage(
    usage_data: UsageTrack,
    use_credits: bool = Query(True, description="Whether to deduct credits for this usage"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_by_api_key)
):
    """
    Track usage for a customer's product
    """
    try:
        usage_event = track_usage(
            db=db,
            user_id=current_user.id,
            customer_id=usage_data.customer_id,
            product_code=usage_data.product,
            quantity=usage_data.quantity,
            idempotency_key=usage_data.idempotency_key,
            use_customer_credits=use_credits
        )
        
        # Convert to response model
        return UsageEventResponse(
            id=usage_event.id,
            customer_id=usage_event.customer_id,
            product=usage_event.product.code,  # Use product code in response
            quantity=usage_event.quantity,
            timestamp=usage_event.timestamp
        )
    
    except CustomerNotFoundError:
        raise HTTPException(status_code=404, detail="Customer not found")
    except ProductNotFoundError:
        raise HTTPException(status_code=404, detail="Product not found")
    except InsufficientCreditsError as e:
        raise HTTPException(status_code=402, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events", response_model=List[UsageEventResponse])
def get_usage_records(
    customer_id: Optional[str] = None,
    product_code: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_by_api_key)
):
    """
    Get usage events with optional filtering
    """
    # Convert product_code to product_id if provided
    product_id = None
    if product_code:
        
        product = get_product_by_code(db, current_user.id, product_code)
        if product:
            product_id = product.id
        else:
            raise HTTPException(status_code=404, detail=f"Product {product_code} not found")
    
    # Get usage events
    events = get_usage_events(
        db=db,
        user_id=current_user.id,
        customer_id=customer_id,
        product_id=product_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    
    # Convert to response models
    return [
        UsageEventResponse(
            id=event.id,
            customer_id=event.customer_id,
            product=event.product.code,  # Use product code in response
            quantity=event.quantity,
            timestamp=event.timestamp
        ) for event in events
    ]