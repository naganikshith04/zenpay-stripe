http://127.0.0.1:8000/api/v1/customers
{
        "id": "cust_demo_123",
        "name": "Test Customer",
        "email": "test@example.com",
        "metadata": {
          "source": "curl-test"
        }
      }
http://127.0.0.1:8000/api/v1/products/
{
    "name": "Test Product 121",
    "code": "test-product-code",
    "unit_name": "unit",
    "price_per_unit": 10.50
}

http://127.0.0.1:8000/api/v1/subscriptions/

{"customer_id":
     "cust_demo_123", "product_code":
     "test-product-code2"}

http://127.0.0.1:8000/api/v1/credits/add
{"customer_id": "cust_demo_123", "amount": 110.00,
     "description": "Initial credit top-up"}

curl -X POST
     "http://127.0.0.1:8000/api/v1/usage/
     track" -H "accept: application/json"
     -H "Content-Type: application/json"
     -H "api-key: zp_test_key" -d
     "{\"customer_id\":
     \"cust_demo_123\", \"product\":
     \"test-product-code2\",
     \"quantity\": 2,
     \"idempotency_key\":
     \"test-idempotency-key-123\",
     \"use_credits\": true,
     \"report_to_stripe\": true}"

curl -X POST
     "http://localhost:8000/api/v1/customers/checkout-session" -H
     "Authorization: Bearer zp_test_key" -H "Content-Type:
     application/json" -d '{"customer_id":
     "cust_e73f04e3-42ff-4cff-9bd1-b48ca7160c4a", "price_id":
     "price_1RjcuPGaHerfMWn3nF4Q88AY", "success_url":
     "https://example.com/success", "cancel_url":
     "https://example.com/cancel"}'

l
