# api/routes/products.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import stripe

# Import models
from api.db.models import Product, UsageEvent, User
from api.services.stripe_service import update_product_name, create_stripe_product_and_price
from api.db.session import get_db
from api.dependencies import get_current_user_by_api_key
from models.request import ProductCreate, ProductUpdate
from models.response import ProductResponse

router = APIRouter()


@router.post("/", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_by_api_key),
):
    """Create a new billable product and sync with Stripe"""
    existing_product = (
        db.query(Product)
        .filter(Product.user_id == current_user.id, Product.code == product.code)
        .first()
    )

    if existing_product:
        raise HTTPException(
            status_code=409, detail=f"Product with code '{product.code}' already exists"
        )

    stripe_product = stripe.Product.create(
        name=product.name, metadata={"code": product.code, "user_id": current_user.id}
    )

    stripe_price = stripe.Price.create(
        unit_amount=int(product.price_per_unit * 100),
        currency="usd",
        recurring={"interval": "month"},
        product=stripe_product.id,
    )

    new_product = Product(
        user_id=current_user.id,
        name=product.name,
        code=product.code,
        unit_name=product.unit_name,
        price_per_unit=product.price_per_unit,
        stripe_product_id=stripe_product.id,
        stripe_price_id=stripe_price.id,
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return {
        "id": new_product.id,
        "name": new_product.name,
        "code": new_product.code,
        "unit_name": new_product.unit_name,
        "price_per_unit": new_product.price_per_unit,
        "created_at": new_product.created_at,
    }


@router.get("/list", response_model=List[ProductResponse])
def list_products(
    skip: int = 0,
    limit: int = 100,
    sync_with_stripe: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_by_api_key),
):
    """List all products for the current user, optionally enriched with Stripe data"""
    products = (
        db.query(Product)
        .filter(Product.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for product in products:
        enriched = {
            "id": product.id,
            "name": product.name,
            "code": product.code,
            "unit_name": product.unit_name,
            "price_per_unit": product.price_per_unit,
            "created_at": product.created_at,
        }

        if sync_with_stripe:
            try:
                stripe_product = stripe.Product.retrieve(product.stripe_product_id)
                stripe_price = stripe.Price.retrieve(product.stripe_price_id)
                enriched.update({
                    "stripe_product_active": stripe_product.active,
                    "stripe_price_active": stripe_price.active,
                    "price_per_unit": stripe_price.unit_amount / 100, # Update price_per_unit
                })
            except stripe.error.StripeError as e:
                enriched["stripe_sync_error"] = str(e.user_message or e)

        result.append(enriched)

    return result


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_by_api_key),
    sync_with_stripe: bool = False,
):
    product = (
        db.query(Product)
        .filter(Product.user_id == current_user.id, Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if sync_with_stripe:
        try:
            stripe_price = stripe.Price.retrieve(product.stripe_price_id)
            product.price_per_unit = stripe_price.unit_amount / 100
        except stripe.error.StripeError as e:
            # Log the error or handle it as appropriate
            pass

    return {
        "id": product.id,
        "name": product.name,
        "code": product.code,
        "unit_name": product.unit_name,
        "price_per_unit": product.price_per_unit,
        "created_at": product.created_at,
    }


@router.get("/code/{product_code}", response_model=ProductResponse)
def get_product_by_code(
    product_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_by_api_key),
    sync_with_stripe: bool = False,
):
    product = (
        db.query(Product)
        .filter(Product.user_id == current_user.id, Product.code == product_code)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if sync_with_stripe:
        try:
            stripe_price = stripe.Price.retrieve(product.stripe_price_id)
            product.price_per_unit = stripe_price.unit_amount / 100
        except stripe.error.StripeError as e:
            # Log the error or handle it as appropriate
            pass

    return {
        "id": product.id,
        "name": product.name,
        "code": product.code,
        "unit_name": product.unit_name,
        "price_per_unit": product.price_per_unit,
        "created_at": product.created_at,
    }


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: str,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_by_api_key),
):
    product = (
        db.query(Product)
        .filter(Product.user_id == current_user.id, Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product_data.name and product_data.name != product.name:
        product.name = product_data.name
        update_product_name(
            product.stripe_product_id, product.name
        )

    if product_data.unit_name:
        product.unit_name = product_data.unit_name

    if (
        product_data.price_per_unit
        and product_data.price_per_unit != product.price_per_unit
    ):
        product.price_per_unit = product_data.price_per_unit

        from api.services.stripe_service import update_stripe_product_price

        new_price = update_stripe_product_price(
            stripe_product_id=product.stripe_product_id,
            old_stripe_price_id=product.stripe_price_id,
            new_price_per_unit=product_data.price_per_unit,
        )

        product.stripe_price_id = new_price.id
        product.price_per_unit = new_price.unit_amount / 100 # Update local price with Stripe's

    db.commit()
    db.refresh(product)

    return {
        "id": product.id,
        "name": product.name,
        "code": product.code,
        "unit_name": product.unit_name,
        "price_per_unit": product.price_per_unit,
        "created_at": product.created_at,
    }


@router.delete("/{product_id}")
def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_by_api_key),
):
    product = (
        db.query(Product)
        .filter(Product.user_id == current_user.id, Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    usage_count = (
        db.query(UsageEvent)
        .filter(
            UsageEvent.user_id == current_user.id,
            UsageEvent.Product_id == product.id,
        )
        .count()
    )

    if usage_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete product that has {usage_count} usage events",
        )

    stripe.Product.modify(product.stripe_product_id, active=False)
    db.delete(product)
    db.commit()

    return {"message": "Product deleted successfully"}
