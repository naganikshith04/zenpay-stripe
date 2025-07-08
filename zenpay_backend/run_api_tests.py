# test_api_standalone.py
import requests
import json
import sys
import uuid
import time

BASE_URL = "http://localhost:8000/api/v1"

# Use the latest API key from server output
API_KEY = ""

def check_server_health():
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Server is up and running!")
            return True
        else:
            print("❌ Server returned unexpected status code:", response.status_code)
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running?")
        return False

def create_customer():
    customer_id = f"cust_{uuid.uuid4().hex[:8]}"
    
    url = f"{BASE_URL}/customers/create"
    headers = {
        "api-key": API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "id": customer_id,
        "name": "Test Customer",
        "email": "customer@example.com",
        "metadata": {"plan": "premium"}
    }
    
    try:
        print(f"Making request to: {url}")
        print(f"Headers: {headers}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, headers=headers, json=data)
        print(f"Response status code: {response.status_code}")
        print(f"Response body: {response.text}")
        
        response.raise_for_status()
        print("✅ Customer created successfully!")
        print(json.dumps(response.json(), indent=2))
        return customer_id
    except requests.exceptions.RequestException as e:
        print("❌ Failed to create customer:")
        if hasattr(e, 'response') and e.response:
            print(f"Status code: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        else:
            print(f"Error: {str(e)}")
        return None

def track_usage(customer_id):
    url = f"{BASE_URL}/usage/track"
    headers = {
        "api-key": API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "customer_id": customer_id,
        "product": "api_calls",
        "quantity": 5,
        "idempotency_key": f"test_{uuid.uuid4().hex}"
    }
    
    try:
        print(f"Making request to: {url}")
        print(f"Headers: {headers}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, headers=headers, json=data)
        print(f"Response status code: {response.status_code}")
        print(f"Response body: {response.text}")
        
        response.raise_for_status()
        print("✅ Usage tracked successfully!")
        print(json.dumps(response.json(), indent=2))
        return True
    except requests.exceptions.RequestException as e:
        print("❌ Failed to track usage:")
        if hasattr(e, 'response') and e.response:
            print(f"Status code: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        else:
            print(f"Error: {str(e)}")
        return False

def test_idempotency(customer_id):
    idempotency_key = f"test_idempotency_{uuid.uuid4().hex}"
    
    url = f"{BASE_URL}/usage/track"
    headers = {
        "api-key": API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "customer_id": customer_id,
        "product": "api_calls",
        "quantity": 7,
        "idempotency_key": idempotency_key
    }
    
    try:
        print("Making first request with idempotency key...")
        response1 = requests.post(url, headers=headers, json=data)
        response1.raise_for_status()
        first_id = response1.json().get("id")
        print(f"✅ First request succeeded. ID: {first_id}")
        
        # Change quantity but keep same idempotency key
        data["quantity"] = 10
        
        print("Making second request with same idempotency key...")
        response2 = requests.post(url, headers=headers, json=data)
        response2.raise_for_status()
        second_id = response2.json().get("id")
        print(f"✅ Second request succeeded. ID: {second_id}")
        
        if first_id == second_id:
            print("✅ Idempotency check passed! Both requests returned same ID.")
            return True
        else:
            print("❌ Idempotency check failed! Different IDs returned.")
            return False
            
    except requests.exceptions.RequestException as e:
        print("❌ Idempotency test failed:")
        if hasattr(e, 'response') and e.response:
            print(f"Status code: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        else:
            print(f"Error: {str(e)}")
        return False

def test_api_flow():
    print("Starting ZenPay API Test...\n")
    
    # Check server health
    if not check_server_health():
        print("\n❌ Test failed: Server is not responding")
        sys.exit(1)
    
    # Create customer
    print("\n1. Creating test customer...")
    customer_id = create_customer()
    
    if not customer_id:
        print("\n❌ Test failed: Could not create customer")
        sys.exit(1)
    
    print("\n2. Tracking usage for customer...")
    if not track_usage(customer_id):
        print("\n❌ Test failed: Could not track usage")
        sys.exit(1)
    
    print("\n3. Testing idempotency...")
    if not test_idempotency(customer_id):
        print("\n❌ Test failed: Idempotency test failed")
        sys.exit(1)
    
    print("\n✅ All tests passed!")
    print("API test completed successfully!")

if __name__ == "__main__":
    test_api_flow()