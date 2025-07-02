# models/request.py
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any

class CustomerCreate(BaseModel):
    id: str
    name: Optional[str] = None
    email: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
# Add these to your models section in app.py or in a separate models/request.py file

class FeatureCreate(BaseModel):
    name: str
    code: str
    unit_name: str  # e.g., "calls", "GB", "users"
    price_per_unit: float

    @validator('price_per_unit')
    def price_must_be_positive(cls, v):
        if v < 0:
            raise ValueError('price_per_unit must be positive')
        return v

class FeatureUpdate(BaseModel):
    name: Optional[str] = None
    unit_name: Optional[str] = None
    price_per_unit: Optional[float] = None
    
    @validator('price_per_unit')
    def price_must_be_positive(cls, v):
        if v is not None and v < 0:
            raise ValueError('price_per_unit must be positive')
        return v

# Add these to your models/response.py file or in the response models section

class FeatureResponse(BaseModel):
    id: str
    name: str
    code: str
    unit_name: str
    price_per_unit: float
    created_at: str