# zenpay_backend/core/exceptions.py
class ZenPayException(Exception):
    """Base exception for all ZenPay errors"""
    pass

class CustomerNotFoundError(ZenPayException):
    """Raised when a customer is not found"""
    pass

class InsufficientCreditsError(ZenPayException):
    """Raised when a customer has insufficient credits"""
    pass

class FeatureNotFoundError(ZenPayException):
    """Raised when a feature is not found"""
    pass

class UsageTrackingError(ZenPayException):
    """Raised when there's an error tracking usage"""
    pass

class StripeIntegrationError(ZenPayException):
    """Raised when there's an error with Stripe integration"""
    pass