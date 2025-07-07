# zenpay_backend/db/crud/products.py
from sqlalchemy.orm import Session
from typing import List, Optional

from ..models import Product, User
from core.exceptions import ProductNotFoundError

def create_product(
    db: Session,
    user_id: str,
    name: str,
    code: str,
    unit_name: str,
    price_per_unit: float,
    stripe_price_id: Optional[str] = None
) -> Product:
    """Create a new product"""
    # Check if product code already exists for this user
    existing = db.query(Product).filter(
        Product.user_id == user_id,
        Product.code == code
    ).first()
    
    if existing:
        # Update existing product
        existing.name = name
        existing.unit_name = unit_name
        existing.price_per_unit = price_per_unit
        if stripe_price_id:
            existing.stripe_price_id = stripe_price_id
        
        db.commit()
        db.refresh(existing)
        return existing
    
    # Create new product
    product = Product(
        user_id=user_id,
        name=name,
        code=code,
        unit_name=unit_name,
        price_per_unit=price_per_unit,
        stripe_price_id=stripe_price_id
    )
    
    db.add(product)
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
        db.delete(product)
        db.commit()
        return True
    
    return False