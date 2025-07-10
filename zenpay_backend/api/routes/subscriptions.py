from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.db.session import get_db
from api.dependencies import get_current_user_by_api_key
from api.db.models import User
from api.models.request import SubscriptionCreate
from api.db.crud.subscriptions import create_subscription
from api.db.crud.customers import get_customer
from api.db.crud.products import get_product_by_code
from api.models.response import CustomerResponse, ProductResponse # Assuming these exist

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_new_subscription(
    subscription_data: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_by_api_key)
):
    # Verify customer and product exist for the user
    customer = get_customer(db, current_user.id, subscription_data.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    product = get_product_by_code(db, current_user.id, subscription_data.product_code)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        db_subscription = create_subscription(
            db=db,
            user_id=current_user.id,
            customer_id=customer.id,
            product_id=product.id
        )
        return {
            "message": "Subscription created successfully",
            "subscription_id": db_subscription.id,
            "stripe_subscription_id": db_subscription.stripe_subscription_id,
            "stripe_subscription_item_id": db_subscription.stripe_subscription_item_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
