# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import database models and create tables
from db.models import Base
from db.session import engine
Base.metadata.create_all(bind=engine)

# Import routers
from api.routes.customers import router as customers_router

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

# Include routers
app.include_router(customers_router, prefix="/api/v1/customers", tags=["customers"])

# Create a test user for development
def create_test_user():
    from db.session import SessionLocal
    from db.models import User
    
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