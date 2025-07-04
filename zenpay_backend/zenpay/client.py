from .api import create_customer, track_usage

class ZenPay:
    def __init__(self, api_key: str, base_url: str = "http://localhost:3000"):
        self.api_key = api_key
        self.base_url = base_url

    def create_customer(self, customer_data: dict):
        return create_customer(self.base_url, self.api_key, customer_data)

    def track_usage(self, usage_data: dict):
        return track_usage(self.base_url, self.api_key, usage_data)
