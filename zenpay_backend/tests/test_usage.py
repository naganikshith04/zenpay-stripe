import pytest
from zenpay_backend.db.crud.usage import create_usage_event, get_usage_by_customer
from zenpay_backend.db.crud.customers import create_customer

def test_create_usage_event(db_session, test_user, test_products):
    # Create a customer first
    customer = create_customer(
        db=db_session,
        user_id=test_user.id,
        customer_id="test_customer",
        name="Test Customer"
    )
    
    # Create usage event
    event = create_usage_event(
        db=db_session,
        user_id=test_user.id,
        customer_id="test_customer",
        product_code="api_calls",
        quantity=5,
        idempotency_key="test_idempotency_key"
    )
    
    # Verify event was created
    assert event is not None
    assert event.user_id == test_user.id
    assert event.customer_id == "test_customer"
    assert event.quantity == 5
    
    # Verify product is correct
    product = test_products[0]  # The API calls product
    assert event.product_id == product.id

def test_idempotency(db_session, test_user, test_products):
    # Create a customer
    customer = create_customer(
        db=db_session,
        user_id=test_user.id,
        customer_id="test_customer",
        name="Test Customer"
    )
    
    # Create first usage event
    event1 = create_usage_event(
        db=db_session,
        user_id=test_user.id,
        customer_id="test_customer",
        product_code="api_calls",
        quantity=5,
        idempotency_key="same_key"
    )
    
    # Create second usage event with same idempotency key
    event2 = create_usage_event(
        db=db_session,
        user_id=test_user.id,
        customer_id="test_customer",
        product_code="api_calls",
        quantity=10,  # Different quantity
        idempotency_key="same_key"  # Same key
    )
    
    # Should return the first event, not create a new one
    assert event1.id == event2.id
    assert event2.quantity == 5  # Should keep original quantity

def test_get_usage_by_customer(db_session, test_user, test_products):
    # Create a customer
    customer = create_customer(
        db=db_session,
        user_id=test_user.id,
        customer_id="test_customer",
        name="Test Customer"
    )
    
    # Create multiple usage events
    create_usage_event(
        db=db_session,
        user_id=test_user.id,
        customer_id="test_customer",
        product_code="api_calls",
        quantity=5
    )
    
    create_usage_event(
        db=db_session,
        user_id=test_user.id,
        customer_id="test_customer",
        product_code="storage",
        quantity=2
    )
    
    # Get usage events for this customer
    events = get_usage_by_customer(
        db=db_session,
        user_id=test_user.id,
        customer_id="test_customer"
    )
    
    # Verify we got both events
    assert len(events) == 2