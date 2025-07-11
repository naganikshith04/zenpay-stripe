# models/request.py
from datetime import datetime
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any

class CustomerCreate(BaseModel):
    id: str
    name: Optional[str] = None
    email: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
# Add these to your models section in app.py or in a separate models/request.py file

class ProductCreate(BaseModel):
    name: str
    code: str
    unit_name: str  # e.g., "calls", "GB", "users"
    price_per_unit: float
    meter_id: Optional[str] = None

    @validator('price_per_unit')
    def price_must_be_positive(cls, v):
        if v < 0:
            raise ValueError('price_per_unit must be positive')
        return v

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    unit_name: Optional[str] = None
    price_per_unit: Optional[float] = None

    @validator('price_per_unit')
    def price_must_be_positive(cls, v):
        if v is not None and v < 0:
            raise ValueError('price_per_unit must be positive')
        return v



class ProductResponse(BaseModel):
    id: str
    name: str
    code: str
    unit_name: str
    price_per_unit: float
    created_at: str
    
class UsageTrack(BaseModel):
    customer_id: str
    product: str
    quantity: float
    idempotency_key: Optional[str] = None
    
class CreditTopUpRequest(BaseModel):
    customer_id: str
    amount: float

class CreditAdd(BaseModel):
    customer_id: str
    amount: float
    description: Optional[str] = None

class SubscriptionCreate(BaseModel):
    customer_id: str
    product_code: str

class CheckoutSessionCreate(BaseModel):
    customer_id: str
    price_id: str
    success_url: str
    cancel_url: str

class BillingPortalCreate(BaseModel):
    customer_id: str
    return_url: str
