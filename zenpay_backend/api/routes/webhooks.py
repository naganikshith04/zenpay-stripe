# zenpay_backend/api/routes/webhooks.py
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
import stripe
import os
import logging

from api.db.session import get_db
from api.db.crud.customers import create_customer, delete_customer
from api.db.crud.products import create_product, delete_product, update_product
from api.db.models import User # Assuming User model is needed for context

router = APIRouter()
logger = logging.getLogger(__name__)

# This should ideally come from your config or environment variables
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

@router.post("/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    if not STRIPE_WEBHOOK_SECRET:
        logger.error("Stripe webhook secret not configured.")
        raise HTTPException(status_code=500, detail="Webhook secret not configured.")

    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"Invalid signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    event_type = event['type']
    data = event['data']['object']

    logger.info(f"Received Stripe event: {event_type}")

    try:
        if event_type == 'customer.created' or event_type == 'customer.updated':
            # For simplicity, assuming user_id can be derived or is fixed for webhooks
            # In a real app, you'd map this to your internal user
            user_id = "your_default_user_id_for_webhooks" # TODO: Replace with actual user ID logic
            
            create_customer(
                db=db,
                user_id=user_id,
                customer_id=data['id'],
                name=data.get('name'),
                email=data.get('email'),
                metadata=data.get('metadata'),
                stripe_customer_id=data['id']
            )
            logger.info(f"Customer {data['id']} synced.")

        elif event_type == 'customer.deleted':
            user_id = "your_default_user_id_for_webhooks" # TODO: Replace with actual user ID logic
            delete_customer(db=db, user_id=user_id, customer_id=data['id'])
            logger.info(f"Customer {data['id']} deleted.")

        elif event_type == 'product.created' or event_type == 'product.updated':
            user_id = "your_default_user_id_for_webhooks" # TODO: Replace with actual user ID logic
            
            # Stripe Product object doesn't directly have 'code', 'unit_name', 'price_per_unit'
            # You'd need to fetch associated Price objects or infer from metadata
            # For now, we'll just update name and assume other fields are handled elsewhere or not critical for webhook sync
            
            # If product.created, create it. If product.updated, update it.
            # This assumes your create_product can handle updates if product_code exists
            create_product( # Using create_product as it handles update if exists
                db=db,
                user_id=user_id,
                name=data.get('name'),
                code=data['id'], # Using Stripe product ID as code for simplicity
                unit_name="unit", # Placeholder
                price_per_unit=0.0, # Placeholder
                stripe_product_id=data['id']
            )
            logger.info(f"Product {data['id']} synced.")

        elif event_type == 'product.deleted':
            user_id = "your_default_user_id_for_webhooks" # TODO: Replace with actual user ID logic
            # Note: delete_product archives in Stripe, but here we delete from local DB
            delete_product(db=db, user_id=user_id, product_id=data['id'])
            logger.info(f"Product {data['id']} deleted.")

        # Add more event types as needed (e.g., invoice.paid, checkout.session.completed)

    except Exception as e:
        logger.error(f"Error handling Stripe event {event_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Error handling event: {e}")

    return {"status": "success"}
