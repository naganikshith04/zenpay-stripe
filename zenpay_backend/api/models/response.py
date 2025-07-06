# models/response.py
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Dict, Any

class CustomerResponse(BaseModel):
    id: str
    name: Optional[str] = None
    email: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    
class UsageEventResponse(BaseModel):
    id: str
    customer_id: str
    feature: str
    quantity: float
    timestamp: datetime

class FeatureResponse(BaseModel):
    id: str
    name: str
    code: str
    unit_name: str
    price_per_unit: float
    created_at: datetime  # Keep as datetime

    class Config:
        from_attributes = True  # Use this for Pydantic v2 compatibility
        

class CreditTopUpResponse(BaseModel):
    customer_id: str
    new_balance: float


class CreditTransactionResponse(BaseModel):
    id: str
    customer_id: str
    amount: float
    timestamp: datetime
    type: str  # e.g., "topup", "usage"
    
class CreditBalance(BaseModel):
    customer_id: str
    balance: float
