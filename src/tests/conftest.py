"""Shared fixtures for tests."""

import json
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest


@pytest.fixture
def sample_api_product() -> dict:
    """Sample product from Fake Store API."""
    return {
        "id": 1,
        "title": "Fjallraven Backpack",
        "price": 109.95,
        "description": "Your perfect pack for everyday use",
        "category": "men's clothing",
        "image": "https://example.com/image.jpg",
        "rating": {"rate": 3.9, "count": 120},
    }


@pytest.fixture
def sample_api_user() -> dict:
    """Sample user from Fake Store API."""
    return {
        "id": 1,
        "email": "john@gmail.com",
        "username": "johnd",
        "password": "m38rmF$",
        "name": {"firstname": "John", "lastname": "Doe"},
        "address": {
            "city": "kilcoole",
            "street": "7835 new road",
            "zipcode": "12926-3874",
        },
        "phone": "1-570-236-7033",
    }


@pytest.fixture
def sample_api_cart() -> dict:
    """Sample cart from Fake Store API."""
    return {
        "id": 1,
        "userId": 1,
        "date": "2024-01-01",
        "products": [
            {"productId": 1, "quantity": 2},
            {"productId": 5, "quantity": 1},
        ],
    }


@pytest.fixture
def sample_csv_dir() -> Path:
    """Create temporary directory with sample CSV files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir)

        # Products CSV
        products_content = """product_id,product_name,category,price,cost,stock_quantity,supplier
P001,Test Product,Electronics,99.99,50.00,100,TestSupplier"""
        (path / "products.csv").write_text(products_content)

        # Customers CSV
        customers_content = """customer_id,first_name,last_name,email,phone,city,state,country,registration_date
C001,John,Doe,john@test.com,555-1234,New York,NY,USA,2024-01-01"""
        (path / "customers.csv").write_text(customers_content)

        # Sales CSV
        sales_content = """sale_id,customer_id,product_id,quantity,unit_price,total_amount,sale_date,payment_method
S001,C001,P001,2,99.99,199.98,2024-01-15,credit_card"""
        (path / "sales.csv").write_text(sales_content)

        yield path


@pytest.fixture
def batch_id():
    """Generate a batch ID for testing."""
    return uuid4()
