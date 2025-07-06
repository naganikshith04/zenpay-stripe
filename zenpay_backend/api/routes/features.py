# api/routes/features.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import stripe

# Import models
from api.db.models import Feature, UsageEvent, User
from api.services.stripe import update_product_name, create_metered_price
from api.db.session import get_db
from dependencies import get_current_user
from models.request import FeatureCreate, FeatureUpdate
from models.response import FeatureResponse

features_router = APIRouter()


@features_router.post("/create", response_model=FeatureResponse)
def create_feature(
    feature: FeatureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new billable feature and sync with Stripe"""
    # Check if feature code already exists for this user
    existing_feature = (
        db.query(Feature)
        .filter(Feature.user_id == current_user.id, Feature.code == feature.code)
        .first()
    )

    if existing_feature:
        raise HTTPException(
            status_code=409, detail=f"Feature with code '{feature.code}' already exists"
        )

    # 🧾 Create Stripe Product
    stripe_product = stripe.Product.create(
        name=feature.name, metadata={"code": feature.code, "user_id": current_user.id}
    )

    # 💲 Create Stripe Price
    stripe_price = stripe.Price.create(
        unit_amount=int(
            feature.price_per_unit * 100
        ),  # Stripe requires amount in cents
        currency="usd",
        recurring={"interval": "month"},
        product=stripe_product.id,
    )

    # Save to DB
    new_feature = Feature(
        user_id=current_user.id,
        name=feature.name,
        code=feature.code,
        unit_name=feature.unit_name,
        price_per_unit=feature.price_per_unit,
        stripe_product_id=stripe_product.id,
        stripe_price_id=stripe_price.id,
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
        "created_at": new_feature.created_at,
    }


@features_router.get("/list", response_model=List[FeatureResponse])
def list_features(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all features for the current user"""
    features = (
        db.query(Feature)
        .filter(Feature.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for feature in features:
        result.append(
            {
                "id": feature.id,
                "name": feature.name,
                "code": feature.code,
                "unit_name": feature.unit_name,
                "price_per_unit": feature.price_per_unit,
                "created_at": feature.created_at,
            }
        )

    return result


@features_router.get("/{feature_id}", response_model=FeatureResponse)
def get_feature(
    feature_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific feature by ID"""
    feature = (
        db.query(Feature)
        .filter(Feature.user_id == current_user.id, Feature.id == feature_id)
        .first()
    )

    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")

    return {
        "id": feature.id,
        "name": feature.name,
        "code": feature.code,
        "unit_name": feature.unit_name,
        "price_per_unit": feature.price_per_unit,
        "created_at": feature.created_at,
    }


@features_router.get("/code/{feature_code}", response_model=FeatureResponse)
def get_feature_by_code(
    feature_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific feature by code"""
    feature = (
        db.query(Feature)
        .filter(Feature.user_id == current_user.id, Feature.code == feature_code)
        .first()
    )

    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")

    return {
        "id": feature.id,
        "name": feature.name,
        "code": feature.code,
        "unit_name": feature.unit_name,
        "price_per_unit": feature.price_per_unit,
        "created_at": feature.created_at,
    }


@features_router.put("/{feature_id}", response_model=FeatureResponse)
def update_feature(
    feature_id: str,
    feature_data: FeatureUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    feature = (
        db.query(Feature)
        .filter(Feature.user_id == current_user.id, Feature.id == feature_id)
        .first()
    )

    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")

    # Sync changes
    stripe_updated = False

    if feature_data.name and feature_data.name != feature.name:
        feature.name = feature_data.name
        update_product_name(
            feature.stripe_product_id, feature.name, current_user.stripe_connect_id
        )
        stripe_updated = True

    if feature_data.unit_name:
        feature.unit_name = feature_data.unit_name  # Not used in Stripe directly

    if (
        feature_data.price_per_unit
        and feature_data.price_per_unit != feature.price_per_unit
    ):
        feature.price_per_unit = feature_data.price_per_unit
        new_price = create_metered_price(
            stripe_account=current_user.stripe_connect_id,
            product_id=feature.stripe_product_id,
            unit_amount=feature.price_per_unit,
            currency="usd",
        )

        feature.stripe_price_id = new_price["id"]
        stripe_updated = True

    db.commit()
    db.refresh(feature)

    return {
        "id": feature.id,
        "name": feature.name,
        "code": feature.code,
        "unit_name": feature.unit_name,
        "price_per_unit": feature.price_per_unit,
        "created_at": feature.created_at,
    }


@features_router.delete("/{feature_id}")
def delete_feature(
    feature_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a feature"""
    feature = (
        db.query(Feature)
        .filter(Feature.user_id == current_user.id, Feature.id == feature_id)
        .first()
    )

    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")

    # Check if this feature has any usage events
    usage_count = (
        db.query(UsageEvent)
        .filter(
            UsageEvent.user_id == current_user.id,
            UsageEvent.feature_code == feature.code,
        )
        .count()
    )

    if usage_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete feature that has {usage_count} usage events",
        )

    db.delete(feature)
    db.commit()

    return {"message": "Feature deleted successfully"}
