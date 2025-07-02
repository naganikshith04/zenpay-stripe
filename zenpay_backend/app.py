# app.py simplified example

from fastapi import FastAPI, APIRouter, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, Column, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import uuid
from datetime import datetime
import json

# Create the FastAPI app
app = FastAPI(
    title="ZenPay API",
    description="API for usage-based billing with Stripe",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE_URL = "sqlite:///./zenpay.db"
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    api_key = Column(String, unique=True, index=True)
    company_name = Column(String, nullable=True)
    stripe_connect_id = Column(String, nullable=True)
    created_at = Column(String, default=lambda: datetime.now().isoformat())

class CustomerDB(Base):
    __tablename__ = "customers"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    metadata_json = Column(String, nullable=True)  # Renamed from metadata
    created_at = Column(String, default=lambda: datetime.now().isoformat())

class Feature(Base):
    __tablename__ = "features"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    name = Column(String)
    code = Column(String)
    unit_name = Column(String)
    price_per_unit = Column(Float)
    created_at = Column(String, default=lambda: datetime.now().isoformat())

class UsageEvent(Base):
    __tablename__ = "usage_events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))
    customer_id = Column(String, ForeignKey("customers.id"))
    feature_code = Column(String)
    quantity = Column(Float)
    idempotency_key = Column(String, nullable=True)
    timestamp = Column(String, default=lambda: datetime.now().isoformat())

# Create the database tables
Base.metadata.create_all(bind=engine)

# Create a test user
def create_test_user():
    db = SessionLocal()
    try:
        # Check if test user already exists
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        
        if not test_user:
            # Create test user
            test_api_key = "zp_test_key"
            test_user = User(
                email="test@example.com",
                api_key=test_api_key,
                company_name="Test Company"
            )
            db.add(test_user)
            db.commit()
            print(f"Test user created with API key: {test_api_key}")
        else:
            print(f"Test user already exists with API key: {test_user.api_key}")
        
        return test_user.api_key
    finally:
        db.close()

# Initialize test user
TEST_API_KEY = create_test_user()

# ---- PYDANTIC MODELS ----

# Customer models
class CustomerCreate(BaseModel):
    id: str
    name: Optional[str] = None
    email: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class CustomerResponse(BaseModel):
    id: str
    name: Optional[str] = None
    email: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: str

# Feature models
class FeatureCreate(BaseModel):
    name: str
    code: str
    unit_name: str
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

class FeatureResponse(BaseModel):
    id: str
    name: str
    code: str
    unit_name: str
    price_per_unit: float
    created_at: str

# Usage models
class UsageTrack(BaseModel):
    customer_id: str
    feature: str
    quantity: float
    idempotency_key: Optional[str] = None

class UsageTrackResponse(BaseModel):
    id: str
    customer_id: str
    feature: str
    quantity: float
    cost: Optional[float] = None
    timestamp: str

# ---- DEPENDENCIES ----
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(api_key: str = Header(..., convert_underscores=False, alias="api-key"), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.api_key == api_key).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return user

# ---- ROUTERS ----
customers_router = APIRouter()
usage_router = APIRouter()
features_router = APIRouter()

# ---- CUSTOMER ROUTES ----
@customers_router.post("/create", response_model=CustomerResponse)
def create_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new customer"""
    # Implementation...

# ---- USAGE ROUTES ----
@usage_router.post("/track", response_model=UsageTrackResponse)
def track_usage(
    usage: UsageTrack,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Track usage for a customer"""
    # Implementation as provided...

# ---- FEATURE ROUTES ----
@features_router.post("/create", response_model=FeatureResponse)
def create_feature(
    feature: FeatureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new billable feature"""
    print(f"Creating feature: {feature}")
    print(f"User ID: {current_user.id}")
    
    # Check if feature code already exists for this user
    existing_feature = db.query(Feature).filter(
        Feature.user_id == current_user.id,
        Feature.code == feature.code
    ).first()
    
    if existing_feature:
        print(f"Feature with code {feature.code} already exists")
        raise HTTPException(
            status_code=409,
            detail=f"Feature with code '{feature.code}' already exists"
        )
    
    try:
        # Create new feature
        new_feature = Feature(
            user_id=current_user.id,
            name=feature.name,
            code=feature.code,
            unit_name=feature.unit_name,
            price_per_unit=feature.price_per_unit
        )
        
        print(f"Adding feature to database: {new_feature}")
        db.add(new_feature)
        db.commit()
        db.refresh(new_feature)
        
        print(f"Feature created with ID: {new_feature.id}")
        
        # Create response dictionary
        response = {
            "id": new_feature.id,
            "name": new_feature.name,
            "code": new_feature.code,
            "unit_name": new_feature.unit_name,
            "price_per_unit": new_feature.price_per_unit,
            "created_at": new_feature.created_at
        }
        print(f"Returning response: {response}")
        return response
    except Exception as e:
        print(f"Error creating feature: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create feature: {str(e)}")

# Include routers
app.include_router(customers_router, prefix="/api/v1/customers", tags=["customers"])
app.include_router(usage_router, prefix="/api/v1/usage", tags=["usage"])
app.include_router(features_router, prefix="/api/v1/features", tags=["features"])

# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Welcome to ZenPay API",
        "docs_url": "/docs",
        "api_key": TEST_API_KEY
    }

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)