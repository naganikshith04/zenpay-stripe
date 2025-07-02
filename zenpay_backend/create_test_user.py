# scripts/create_test_user.py
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from zenpay_backend.db.session import SessionLocal
from zenpay_backend.db.models import User

# After creating tables
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
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Authentication dependency
def get_current_user(api_key: str = Header(..., convert_underscores=False, alias="api-key"), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.api_key == api_key).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return user

# Initialize test user
TEST_API_KEY = create_test_user()

if __name__ == "__main__":
    create_test_user()