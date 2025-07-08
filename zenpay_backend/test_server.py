# test_server.py

import uvicorn
from api.main import app
from api.db.session import engine
from api.db.models import Base, User, Product
from api.core.security import get_password_hash, generate_api_key
from sqlalchemy.orm import Session

# Create database and sample data for testing
def setup_test_data():
    # Drop and create database tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Create a test session
    from api.db.session import SessionLocal
    db = SessionLocal()
    
    try:
        # Check if test user already exists
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        
        if not test_user:
            # Create test user
            test_user = User(
                email="test@example.com",
                company_name="Test Company",
                hashed_password=get_password_hash("password123"),
                api_key=generate_api_key()
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            
            # Create test products
            product1 = Product(
                user_id=test_user.id,
                name="API Calls",
                code="api_calls",
                unit_name="call",
                price_per_unit=0.01,
                meter_id=None
            )
            
            product2 = Product(
                user_id=test_user.id,
                name="Storage",
                code="storage",
                unit_name="GB",
                price_per_unit=0.50,
                meter_id=None
            )
            
            db.add(product1)
            db.add(product2)
            db.commit()
        
        print("\n=== TEST ENVIRONMENT READY ===")
        print(f"Test User Email: test@example.com")
        print(f"Test User API Key: {test_user.api_key}")
        print("Available products: 'api_calls', 'storage'")
        print("===============================\n")
        
    except Exception as e:
        print(f"Error setting up test data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Setup test data
    setup_test_data()
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000)