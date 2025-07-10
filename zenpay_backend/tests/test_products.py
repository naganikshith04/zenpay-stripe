from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from zenpay_backend.main import app
from zenpay_backend.api.db.models import User, Product

client = TestClient(app)

# Mock database and user for testing
@patch('zenpay_backend.api.db.session.get_db')
@patch('zenpay_backend.api.dependencies.get_current_user_by_api_key')
def test_product_creation_and_update(mock_get_user, mock_get_db):
    # Mock user
    mock_user = User(id='test_user', api_key='test_key')
    mock_get_user.return_value = mock_user

    # Mock database session
    mock_db = MagicMock(spec=Session)
    mock_get_db.return_value = mock_db

    # 1. Create a new product
    product_data = {
        'name': 'Test Product',
        'code': 'TP001',
        'unit_name': 'unit',
        'price_per_unit': 10.0
    }
    with patch('zenpay_backend.api.db.crud.products.create_stripe_product_and_price') as mock_create_stripe:
        mock_create_stripe.return_value = (MagicMock(id='stripe_prod_1'), MagicMock(id='stripe_price_1'))
        response = client.post("/products/", json=product_data)

    assert response.status_code == 200
    created_product = response.json()
    assert created_product['name'] == product_data['name']

    # 2. Update the product's price
    update_data = {'price_per_unit': 15.0}
    with patch('zenpay_backend.api.db.crud.products.update_stripe_product_price') as mock_update_stripe:
        mock_update_stripe.return_value = MagicMock(id='stripe_price_2', unit_amount=1500)
        response = client.patch(f"/products/{created_product['id']}", json=update_data)

    assert response.status_code == 200
    updated_product = response.json()
    assert updated_product['price_per_unit'] == 15.0
