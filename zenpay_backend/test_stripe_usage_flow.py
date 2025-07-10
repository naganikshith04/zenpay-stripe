import requests
import stripe
import os
import time

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8000/api/v1"
API_KEY = "zp_test_key" # Your API key for your ZenPay backend
STRIPE_API_KEY = "" # Your Stripe secret key

stripe.api_key = STRIPE_API_KEY

HEADERS = {
    "Content-Type": "application/json",
    "api-key": API_KEY
}

# --- Helper Functions ---
def create_customer(customer_id: str, name: str, email: str):
    print(f"\n--- Creating Customer: {name} ({customer_id}) ---")
    payload = {
        "id": customer_id,
        "name": name,
        "email": email
    }
    response = requests.post(f"{BASE_URL}/customers", headers=HEADERS, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    response.raise_for_status()
    return response.json()

def create_product(name: str, code: str, unit_name: str, price_per_unit: float):
    print(f"\n--- Creating Product: {name} ({code}) ---")
    payload = {
        "name": name,
        "code": code,
        "unit_name": unit_name,
        "price_per_unit": price_per_unit
    }
    response = requests.post(f"{BASE_URL}/products", headers=HEADERS, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    response.raise_for_status()
    return response.json()

def create_stripe_subscription(stripe_customer_id: str, stripe_price_id: str):
    print(f"\n--- Creating Stripe Subscription for Customer {stripe_customer_id} to Price {stripe_price_id} ---")
    try:
        future_timestamp = int(time.time()) + 60  # 60 seconds in the future
        subscription = stripe.Subscription.create(
            customer=stripe_customer_id,
            items=[{"price": stripe_price_id}],
            collection_method='charge_automatically', # Or 'send_invoice'
            billing_cycle_anchor=future_timestamp, # Start billing cycle immediately
        )
        print(f"Stripe Subscription Created: {subscription.id}")
        # Give Stripe a moment to process
        time.sleep(2)
        return subscription
    except stripe.error.StripeError as e:
        print(f"Error creating Stripe subscription: {e}")
        raise

def track_usage(customer_id: str, product_code: str, quantity: float, idempotency_key: str = None):
    print(f"\n--- Tracking Usage for Customer {customer_id}, Product {product_code}, Quantity {quantity} ---")
    payload = {
        "customer_id": customer_id,
        "product": product_code,
        "quantity": quantity
    }
    if idempotency_key:
        payload["idempotency_key"] = idempotency_key

    response = requests.post(f"{BASE_URL}/usage/track", headers=HEADERS, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    response.raise_for_status()
    return response.json()

# --- Main Execution Flow ---
if __name__ == "__main__":
    try:
        # 1. Create a Customer
        customer_data = create_customer(
            customer_id="test_customer_123",
            name="Test User",
            email="test@example.com"
        )
        zenpay_customer_id = customer_data["id"]
        stripe_customer_id = customer_data["stripe_customer_id"]

        # 2. Create a Product
        product_data = create_product(
            name="API Calls",
            code="api_calls_test",
            unit_name="call",
            price_per_unit=0.01
        )
        zenpay_product_code = product_data["code"]
        stripe_price_id = product_data["stripe_price_id"]

        # 3. Create a Stripe Subscription
        # This is crucial for usage reporting to work correctly in Stripe
        stripe_subscription = create_stripe_subscription(
            stripe_customer_id=stripe_customer_id,
            stripe_price_id=stripe_price_id
        )
        # Extract the subscription item ID from the created subscription
        # This is what report_usage_to_stripe expects
        stripe_subscription_item_id = stripe_subscription.items.data[0].id
        print(f"Extracted Stripe Subscription Item ID: {stripe_subscription_item_id}")

        # 4. Track Usage
        # You can run this multiple times to track more usage
        usage_event = track_usage(
            customer_id=zenpay_customer_id,
            product_code=zenpay_product_code,
            quantity=100,
            idempotency_key="usage_event_1_test"
        )

        print("\n--- Usage Tracking Flow Completed Successfully ---")
        print("Please check your Stripe dashboard for the created customer, product, subscription, and usage records.")

    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")
        if e.response:
            print(f"Response Content: {e.response.text}")
    except stripe.error.StripeError as e:
        print(f"Stripe API Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")