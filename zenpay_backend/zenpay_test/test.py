from zenpay import ZenPay

client = ZenPay(api_key="zp_test_key", base_url="http://localhost:3000")

response = client.create_customer({
    "id": "cust_xyz",
    "name": "Test Corp",
    "email": "test@example.com",
    "metadata": {"plan": "pro"}
})
print(response)

usage_response = client.track_usage({
    "customer_id": "cust_xyz",
    "product": "product_code_1",
    "quantity": 5,
    "idempotency_key": "usage-001"
})
print(usage_response)
