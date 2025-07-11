# models/response.py
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class CustomerResponse(BaseModel):
    id: str
    name: Optional[str] = None
    email: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(None, alias="metadata_json")
    created_at: datetime
    
class UsageEventResponse(BaseModel):
    id: str
    customer_id: str
    product: str
    quantity: float
    timestamp: datetime

class ProductResponse(BaseModel):
    id: str
    name: str
    code: str
    unit_name: str
    price_per_unit: float
    created_at: datetime

    class Config:
        from_attributes = True
        
class CreditTopUpResponse(BaseModel):
    customer_id: str
    new_balance: float

class CreditTransactionResponse(BaseModel):
    id: str
    customer_id: str
    amount: float
    timestamp: datetime
    type: str
    
class CreditBalance(BaseModel):
    customer_id: str
    balance: float

class SubscriptionResponse(BaseModel):
    id: str
    customer_id: str
    product_code: str
    stripe_subscription_id: str
    status: str
    created_at: datetime
    
class SubscriptionCancellationResponse(BaseModel):
    message: str
    
class UsageResponse(BaseModel):
    customer_id: str
    product: str
    total_usage: float
    start_date: datetime
    end_date: datetime
    
class UsageRecordResponse(BaseModel):
    id: str
    customer_id: str
    product: str
    quantity: float
    timestamp: datetime
    
class UsageRecordListResponse(BaseModel):
    records: List[UsageRecordResponse]
    
class UsageRecordCreate(BaseModel):
    customer_id: str
    product: str
    quantity: float
    
class UsageRecordCreateResponse(BaseModel):
    id: str
    customer_id: str
    product: str
    quantity: float
    timestamp: datetime

class CheckoutSessionResponse(BaseModel):
    url: str

class BillingPortalResponse(BaseModel):
    url: str
