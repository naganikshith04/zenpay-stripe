import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from zenpay_backend.db.models import Base, User, product
from zenpay_backend.core.security import get_password_hash, generate_api_key

# Use an in-memory SQLite database for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create the database tables
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
        hashed_password=get_password_hash("password123"),
        api_key=generate_api_key()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_products(db_session, test_user):
    product1 = product(
        user_id=test_user.id,
        name="API Calls",
        code="api_calls",
        unit_name="call",
        price_per_unit=0.01
    )
    
    product2 = product(
        user_id=test_user.id,
        name="Storage",
        code="storage",
        unit_name="GB",
        price_per_unit=0.50
    )
    
    db_session.add(product1)
    db_session.add(product2)
    db_session.commit()
    
    return [product1, product2]