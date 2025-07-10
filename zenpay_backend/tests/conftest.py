import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from zenpay_backend.api.db.models import Base, User, Product
from api.core.security import get_password_hash, generate_api_key

# Use an in-memory SQLite database for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Drop and create the database tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Create a session
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def test_user(db_session):
    user = User(
        email="test@example.com",
        company_name="Test Company",
        api_key=generate_api_key()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_products(db_session, test_user):
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
    
    db_session.add(product1)
    db_session.add(product2)
    db_session.commit()
    
    return [product1, product2]