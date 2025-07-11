# zenpay_backend/db/crud/products.py
from sqlalchemy.orm import Session
from typing import List, Optional
import stripe
from fastapi import HTTPException, status

from ..models import Product, User
from core.exceptions import ProductNotFoundError

def create_product(
    db: Session,
    user_id: str,
    name: str,
    code: str,
    unit_name: str,
    price_per_unit: float,
    stripe_product_id: Optional[str] = None,
    stripe_price_id: Optional[str] = None
) -> Product:
    """Create a new product"""
    # Check if product code already exists for this user
    existing = db.query(Product).filter(
        Product.user_id == user_id,
        Product.code == code
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product with this code already exists",
        )
    
    # Create product and price in Stripe
    if not stripe_product_id or not stripe_price_id:
        from api.services.stripe_service import create_stripe_product_and_price
        stripe_product, stripe_price = create_stripe_product_and_price(
            product_name=name,
            price_per_unit=price_per_unit,
            event_name="zenpay_tokens",
            quantity_payload_key="value"
        )
        stripe_product_id = stripe_product.id
        stripe_price_id = stripe_price.id

    # Create new product
    product = Product(
        user_id=user_id,
        name=name,
        code=code,
        unit_name=unit_name,
        price_per_unit=price_per_unit,
        stripe_product_id=stripe_product_id,
        stripe_price_id=stripe_price_id
    )
    
    db.add(product)
    db.commit()
    db.refresh(product)
    
    return product

def update_product(
    db: Session,
    user_id: str,
    product_id: str,
    name: Optional[str] = None,
    unit_name: Optional[str] = None,
    price_per_unit: Optional[float] = None
) -> Optional[Product]:
    """Update a product's details in the local DB and Stripe."""
    product = db.query(Product).filter(
        Product.user_id == user_id,
        Product.id == product_id
    ).first()

    if not product:
        return None

    # Store old price for comparison
    old_price = product.price_per_unit

    # Update local database
    if name is not None:
        product.name = name
    if unit_name is not None:
        product.unit_name = unit_name
    if price_per_unit is not None:
        product.price_per_unit = price_per_unit

    # Update Stripe product
    if product.stripe_product_id:
        if name is not None:
            stripe.Product.modify(product.stripe_product_id, name=product.name)
        
        if price_per_unit is not None and price_per_unit != old_price:
            from api.services.stripe_service import update_stripe_product_price

            new_stripe_price = update_stripe_product_price(
                stripe_product_id=product.stripe_product_id,
                old_stripe_price_id=product.stripe_price_id,
                new_price_per_unit=price_per_unit,
            )
            product.stripe_price_id = new_stripe_price.id
            product.price_per_unit = new_stripe_price.unit_amount / 100

    db.commit()
    db.refresh(product)
    return product

def get_product_by_code(
    db: Session,
    user_id: str,
    code: str
) -> Optional[Product]:
    """Get a product by its code"""
    return db.query(Product).filter(
        Product.user_id == user_id,
        Product.code == code
    ).first()

def get_products(
    db: Session,
    user_id: str,
    skip: int = 0,
    limit: int = 100
) -> List[Product]:
    """Get all products for a user"""
    return db.query(Product).filter(
        Product.user_id == user_id
    ).offset(skip).limit(limit).all()

def delete_product(
    db: Session,
    user_id: str,
    product_id: str
) -> bool:
    """Delete a product"""
    product = db.query(Product).filter(
        Product.user_id == user_id,
        Product.id == product_id
    ).first()
    
    if product:
        if product.stripe_product_id:
            try:
                stripe.Product.modify(product.stripe_product_id, active=False)
            except stripe.error.InvalidRequestError:
                # Product might have been already archived in Stripe
                pass
        db.delete(product)
        db.commit()
        return True
    
    return False