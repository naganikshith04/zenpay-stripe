# main.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "api"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.features import features_router
from api.v1.usage import router as usage_router
from api.v1.credits import router as credits_router

from api.db.models import Base
from api.db.session import engine

Base.metadata.create_all(bind=engine)

# Import routers
from api.routes.customers import router as customers_router

# Create the FastAPI app
app = FastAPI(
    title="ZenPay API",
    description="API for usage-based billing with Stripe",
    version="0.1.0"
)

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("✅ LOADING MAIN.PY")
# Create database tables

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(customers_router, prefix="/api/v1/customers", tags=["customers"])

# Create a test user for development
def create_test_user():
    from api.db.session import SessionLocal
    from api.db.models import User
    
    db = SessionLocal()
    try:
        # Check if test user exists
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
            print(f"Using existing test user with API key: {test_user.api_key}")
        return test_user.api_key
    finally:
        db.close()

app.include_router(features_router, prefix="/api/v1/features", tags=["features"])
app.include_router(usage_router, prefix="/api/v1/usage", tags=["usage"])
app.include_router(credits_router, prefix="/api/v1/credits")

# Initialize test user
TEST_API_KEY = create_test_user()

@app.get("/")
def root():
    return {
        "message": "Welcome to ZenPay API",
        "docs_url": "/docs",
        "test_api_key": TEST_API_KEY
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}