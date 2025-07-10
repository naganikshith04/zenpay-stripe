# api/routes/products.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from api.db.models import Product, UsageEvent, User

from api.db.crud.products import (
    create_product,
    get_product_by_code,
    get_products,
    delete_product,
    update_product,
)
from api.db.session import get_db
from api.dependencies import get_current_user_by_api_key as get_current_user
from models.request import ProductCreate, ProductUpdate
from models.response import ProductResponse
from api.db.models import User

router = APIRouter()


@router.post("/", response_model=ProductResponse)
def create_new_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new billable product and sync with Stripe"""
    db_product = create_product(
        db=db,
        user_id=current_user.id,
        name=product.name,
        code=product.code,
        unit_name=product.unit_name,
        price_per_unit=product.price_per_unit,
        
    )
    return db_product


@router.get("/", response_model=List[ProductResponse])
def list_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all products for the current user"""
    products = get_products(db=db, user_id=current_user.id, skip=skip, limit=limit)
    return products


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = (
        db.query(Product)
        .filter(Product.user_id == current_user.id, Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


@router.get("/code/{product_code}", response_model=ProductResponse)
def get_product_by_code_route(
    product_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = get_product_by_code(db, current_user.id, product_code)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


@router.patch("/{product_id}", response_model=ProductResponse)
def update_existing_product(
    product_id: str,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated_product = update_product(
        db=db,
        user_id=current_user.id,
        product_id=product_id,
        name=product_data.name,
        unit_name=product_data.unit_name,
        price_per_unit=product_data.price_per_unit,
    )
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return updated_product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    success = delete_product(db=db, user_id=current_user.id, product_id=product_id)

    if not success:
        raise HTTPException(status_code=404, detail="Product not found")

    return None