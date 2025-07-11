import requests

def create_customer(base_url, api_key, data):
    headers = {"api-key": api_key}
    response = requests.post(f"{base_url}/api/v1/customers/", json=data, headers=headers)
    response.raise_for_status()
    return response.json()

def create_product(base_url, api_key, data):
    headers = {"api-key": api_key}
    response = requests.post(f"{base_url}/api/v1/products/", json=data, headers=headers)
    response.raise_for_status()
    return response.json()

def create_subscription(base_url, api_key, data):
    headers = {"api-key": api_key}
    response = requests.post(f"{base_url}/api/v1/subscriptions/", json=data, headers=headers)
    response.raise_for_status()
    return response.json()

def add_credits(base_url, api_key, data):
    headers = {"api-key": api_key}
    response = requests.post(f"{base_url}/api/v1/credits/add", json=data, headers=headers)
    response.raise_for_status()
    return response.json()

def track_usage(base_url, api_key, data):
    headers = {"api-key": api_key}
    response = requests.post(f"{base_url}/api/v1/usage/track", json=data, headers=headers)
    response.raise_for_status()
    return response.json()