from .api import create_customer, track_usage, create_product, create_subscription, add_credits

class ZenPay:
    def __init__(self, api_key: str, base_url: str = "http://127.0.0.1:8000"):
        self.api_key = api_key
        self.base_url = base_url

    def create_customer(self, customer_data: dict):
        return create_customer(self.base_url, self.api_key, customer_data)

    def create_product(self, product_data: dict):
        return create_product(self.base_url, self.api_key, product_data)

    def create_subscription(self, subscription_data: dict):
        return create_subscription(self.base_url, self.api_key, subscription_data)

    def add_credits(self, credit_data: dict):
        return add_credits(self.base_url, self.api_key, credit_data)

    def track_usage(self, usage_data: dict):
        return track_usage(self.base_url, self.api_key, usage_data)