# api/routes/features.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

# Import models
from db.models import Feature, UsageEvent, User
from api.db.session import get_db
from dependencies import get_current_user
from models.request import FeatureCreate, FeatureUpdate
from models.response import FeatureResponse

features_router = APIRouter()

@features_router.post("/create", response_model=FeatureResponse)
def create_feature(
    feature: FeatureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new billable feature"""
    # Check if feature code already exists for this user
    existing_feature = db.query(Feature).filter(
        Feature.user_id == current_user.id,
        Feature.code == feature.code
    ).first()
    
    if existing_feature:
        raise HTTPException(
            status_code=409,
            detail=f"Feature with code '{feature.code}' already exists"
        )
    
    # Create new feature
    new_feature = Feature(
        user_id=current_user.id,
        name=feature.name,
        code=feature.code,
        unit_name=feature.unit_name,
        price_per_unit=feature.price_per_unit
    )
    
    db.add(new_feature)
    db.commit()
    db.refresh(new_feature)
    
    return {
        "id": new_feature.id,
        "name": new_feature.name,
        "code": new_feature.code,
        "unit_name": new_feature.unit_name,
        "price_per_unit": new_feature.price_per_unit,
        "created_at": new_feature.created_at
    }

@features_router.get("/list", response_model=List[FeatureResponse])
def list_features(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all features for the current user"""
    features = db.query(Feature).filter(
        Feature.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    result = []
    for feature in features:
        result.append({
            "id": feature.id,
            "name": feature.name,
            "code": feature.code,
            "unit_name": feature.unit_name,
            "price_per_unit": feature.price_per_unit,
            "created_at": feature.created_at
        })
    
    return result

@features_router.get("/{feature_id}", response_model=FeatureResponse)
def get_feature(
    feature_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific feature by ID"""
    feature = db.query(Feature).filter(
        Feature.user_id == current_user.id,
        Feature.id == feature_id
    ).first()
    
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    
    return {
        "id": feature.id,
        "name": feature.name,
        "code": feature.code,
        "unit_name": feature.unit_name,
        "price_per_unit": feature.price_per_unit,
        "created_at": feature.created_at
    }

@features_router.get("/code/{feature_code}", response_model=FeatureResponse)
def get_feature_by_code(
    feature_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific feature by code"""
    feature = db.query(Feature).filter(
        Feature.user_id == current_user.id,
        Feature.code == feature_code
    ).first()
    
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    
    return {
        "id": feature.id,
        "name": feature.name,
        "code": feature.code,
        "unit_name": feature.unit_name,
        "price_per_unit": feature.price_per_unit,
        "created_at": feature.created_at
    }

@features_router.put("/{feature_id}", response_model=FeatureResponse)
def update_feature(
    feature_id: str,
    feature_data: FeatureUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing feature"""
    feature = db.query(Feature).filter(
        Feature.user_id == current_user.id,
        Feature.id == feature_id
    ).first()
    
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    
    # Update fields if provided
    if feature_data.name is not None:
        feature.name = feature_data.name
    
    if feature_data.unit_name is not None:
        feature.unit_name = feature_data.unit_name
    
    if feature_data.price_per_unit is not None:
        feature.price_per_unit = feature_data.price_per_unit
    
    db.commit()
    db.refresh(feature)
    
    return {
        "id": feature.id,
        "name": feature.name,
        "code": feature.code,
        "unit_name": feature.unit_name,
        "price_per_unit": feature.price_per_unit,
        "created_at": feature.created_at
    }

@features_router.delete("/{feature_id}")
def delete_feature(
    feature_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a feature"""
    feature = db.query(Feature).filter(
        Feature.user_id == current_user.id,
        Feature.id == feature_id
    ).first()
    
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    
    # Check if this feature has any usage events
    usage_count = db.query(UsageEvent).filter(
        UsageEvent.user_id == current_user.id,
        UsageEvent.feature_code == feature.code
    ).count()
    
    if usage_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete feature that has {usage_count} usage events"
        )
    
    db.delete(feature)
    db.commit()
    
    return {"message": "Feature deleted successfully"}