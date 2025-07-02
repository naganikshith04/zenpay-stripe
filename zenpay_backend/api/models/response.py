# models/response.py
from pydantic import BaseModel
from typing import Optional, Dict, Any

class CustomerResponse(BaseModel):
    id: str
    name: Optional[str] = None
    email: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: str
    
class UsageTrackResponse(BaseModel):
    id: str
    customer_id: str
    feature: str
    quantity: float
    cost: Optional[float] = None
    timestamp: str

class FeatureResponse(BaseModel):
    id: str
    name: str
    code: str
    unit_name: str
    price_per_unit: float
    created_at: str
    
    class Config:
        orm_mode = True  # Add this line to allow ORM model conversion