# zenpay_backend/api/v1/usage.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from ....db.session import get_db
from ....dependencies import get_current_user_by_api_key
from ....db.models import User
from ....models.request import UsageTrack
from ....models.response import UsageEventResponse
from ....db.crud.usage import track_usage, get_usage_events
from ....core.exceptions import CustomerNotFoundError, FeatureNotFoundError, InsufficientCreditsError
from ....db.crud.features import get_feature_by_code

router = APIRouter()

@router.post("/track", response_model=UsageEventResponse)
def record_usage(
    usage_data: UsageTrack,
    use_credits: bool = Query(True, description="Whether to deduct credits for this usage"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_by_api_key)
):
    """
    Track usage for a customer's feature
    """
    try:
        usage_event = track_usage(
            db=db,
            user_id=current_user.id,
            customer_id=usage_data.customer_id,
            feature_code=usage_data.feature,
            quantity=usage_data.quantity,
            idempotency_key=usage_data.idempotency_key,
            use_customer_credits=use_credits
        )
        
        # Convert to response model
        return UsageEventResponse(
            id=usage_event.id,
            customer_id=usage_event.customer_id,
            feature=usage_event.feature.code,  # Use feature code in response
            quantity=usage_event.quantity,
            timestamp=usage_event.timestamp
        )
    
    except CustomerNotFoundError:
        raise HTTPException(status_code=404, detail="Customer not found")
    except FeatureNotFoundError:
        raise HTTPException(status_code=404, detail="Feature not found")
    except InsufficientCreditsError as e:
        raise HTTPException(status_code=402, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events", response_model=List[UsageEventResponse])
def get_usage_records(
    customer_id: Optional[str] = None,
    feature_code: Optional[str] = None,
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
    # Convert feature_code to feature_id if provided
    feature_id = None
    if feature_code:
        
        feature = get_feature_by_code(db, current_user.id, feature_code)
        if feature:
            feature_id = feature.id
        else:
            raise HTTPException(status_code=404, detail=f"Feature {feature_code} not found")
    
    # Get usage events
    events = get_usage_events(
        db=db,
        user_id=current_user.id,
        customer_id=customer_id,
        feature_id=feature_id,
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
            feature=event.feature.code,  # Use feature code in response
            quantity=event.quantity,
            timestamp=event.timestamp
        ) for event in events
    ]