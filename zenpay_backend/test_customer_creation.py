import requests

url = "http://127.0.0.1:3000/api/v1/customers/create"
headers = {
    "Content-Type": "application/json",
    "api-key": "zp_test_key"
}
data = {
    "id": "cust_12345",
    "name": "Test Corp",
    "email": "billing@testcorp.com",
    "metadata": {
        "tier": "premium"
    }
}

response = requests.post(url, headers=headers, json=data)

print(response.status_code)
print(response.json())