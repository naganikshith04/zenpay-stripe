# db/models.py
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True)
    api_key = Column(String, unique=True, index=True)
    company_name = Column(String, nullable=True)
    stripe_connect_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    customers = relationship("Customer", back_populates="user")
    features = relationship("Feature", back_populates="user")

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    metadata_json = Column(JSON, nullable=True)  # ✅ Renamed
    stripe_customer_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="customers")
    usage_events = relationship("UsageEvent", back_populates="customer")

class Feature(Base):
    __tablename__ = "features"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    name = Column(String)
    code = Column(String)
    unit_name = Column(String)
    price_per_unit = Column(Float)
    stripe_price_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    stripe_product_id = Column(String, nullable=True)
    stripe_price_id = Column(String, nullable=True)

    # Relationships
    user = relationship("User", back_populates="features")
    usage_events = relationship("UsageEvent", back_populates="feature")

class UsageEvent(Base):
    __tablename__ = "usage_events"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    customer_id = Column(String, ForeignKey("customers.id"))
    feature_id = Column(String, ForeignKey("features.id"))
    quantity = Column(Float)
    idempotency_key = Column(String, nullable=True)
    reported_to_stripe = Column(Boolean, default=False)
    stripe_usage_record_id = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    customer = relationship("Customer", back_populates="usage_events")
    feature = relationship("Feature", back_populates="usage_events")

class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String)
    customer_id = Column(String, index=True)
    amount = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    description = Column(String)
    type = Column(String)
