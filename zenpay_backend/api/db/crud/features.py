# zenpay_backend/db/crud/features.py
from sqlalchemy.orm import Session
from typing import List, Optional

from ..models import Feature, User
from core.exceptions import FeatureNotFoundError

def create_feature(
    db: Session,
    user_id: str,
    name: str,
    code: str,
    unit_name: str,
    price_per_unit: float,
    stripe_price_id: Optional[str] = None
) -> Feature:
    """Create a new feature"""
    # Check if feature code already exists for this user
    existing = db.query(Feature).filter(
        Feature.user_id == user_id,
        Feature.code == code
    ).first()
    
    if existing:
        # Update existing feature
        existing.name = name
        existing.unit_name = unit_name
        existing.price_per_unit = price_per_unit
        if stripe_price_id:
            existing.stripe_price_id = stripe_price_id
        
        db.commit()
        db.refresh(existing)
        return existing
    
    # Create new feature
    feature = Feature(
        user_id=user_id,
        name=name,
        code=code,
        unit_name=unit_name,
        price_per_unit=price_per_unit,
        stripe_price_id=stripe_price_id
    )
    
    db.add(feature)
    db.commit()
    db.refresh(feature)
    
    return feature

def get_feature_by_code(
    db: Session,
    user_id: str,
    code: str
) -> Optional[Feature]:
    """Get a feature by its code"""
    return db.query(Feature).filter(
        Feature.user_id == user_id,
        Feature.code == code
    ).first()

def get_features(
    db: Session,
    user_id: str,
    skip: int = 0,
    limit: int = 100
) -> List[Feature]:
    """Get all features for a user"""
    return db.query(Feature).filter(
        Feature.user_id == user_id
    ).offset(skip).limit(limit).all()

def delete_feature(
    db: Session,
    user_id: str,
    feature_id: str
) -> bool:
    """Delete a feature"""
    feature = db.query(Feature).filter(
        Feature.user_id == user_id,
        Feature.id == feature_id
    ).first()
    
    if feature:
        db.delete(feature)
        db.commit()
        return True
    
    return False