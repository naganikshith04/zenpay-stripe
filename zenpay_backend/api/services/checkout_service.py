# zenpay_backend/api/services/checkout_service.py

import stripe
from api.core.config import settings

stripe.api_key = settings.STRIPE_API_KEY

def create_checkout_session(
    customer_id: str,
    price_id: str,
    success_url: str,
    cancel_url: str,
):
    """
    Create a Stripe Checkout session for a subscription.
    """
    return stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{"price": price_id}],
        mode="subscription",
        success_url=success_url,
        cancel_url=cancel_url,
    )

def create_billing_portal_session(
    customer_id: str,
    return_url: str,
):
    """
    Create a Stripe Billing Portal session for a customer.
    """
    return stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )
