from zenpay.client import ZenPay
import uuid

# Initialize ZenPay client
api_key = "zp_test_key"
zenpay_client = ZenPay(api_key=api_key)

def run_full_flow():
    print("--- Starting ZenPay Full Flow Test ---")

    # 1. Create Customer
    customer_id = f"cust_{uuid.uuid4()}"
    customer_data = {
        "id": customer_id,
        "name": "Test Customer",
        "email": "test@example.com",
        "metadata": {"source": "zenpay-flow-test"}
    }
    try:
        customer_response = zenpay_client.create_customer(customer_data)
        print(f"Created Customer: {customer_response}")
    except Exception as e:
        print(f"Error creating customer: {e}")
        return

    # 2. Create Product
    product_code = f"prod_{uuid.uuid4()}"
    product_data = {
        "name": "Test Product",
        "code": product_code,
        "unit_name": "unit",
        "price_per_unit": 10.50
    }
    try:
        product_response = zenpay_client.create_product(product_data)
        print(f"Created Product: {product_response}")
    except Exception as e:
        print(f"Error creating product: {e}")
        return

    # 3. Create Subscription
    subscription_data = {
        "customer_id": customer_id,
        "product_code": product_code
    }
    try:
        subscription_response = zenpay_client.create_subscription(subscription_data)
        print(f"Created Subscription: {subscription_response}")
    except Exception as e:
        print(f"Error creating subscription: {e}")
        return

    # 4. Add Credits
    credit_data = {
        "customer_id": customer_id,
        "amount": 110.00,
        "description": "Initial credit top-up"
    }
    try:
        credit_response = zenpay_client.add_credits(credit_data)
        print(f"Added Credits: {credit_response}")
    except Exception as e:
        print(f"Error adding credits: {e}")
        return

    # 5. Track Usage
    usage_data = {
        "customer_id": customer_id,
        "product": product_code,
        "quantity": 5, # Example quantity
        "idempotency_key": str(uuid.uuid4()),
        "use_credits": True,
        "report_to_stripe": True
    }
    try:
        usage_response = zenpay_client.track_usage(usage_data)
        print(f"Tracked Usage: {usage_response}")
    except Exception as e:
        print(f"Error tracking usage: {e}")
        return

    print("--- ZenPay Full Flow Test Complete ---")

if __name__ == "__main__":
    run_full_flow()
