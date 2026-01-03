"""Tests for data connectors."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.connectors.api_connector import (
    APIConnector,
    ExtractionResult,
    FakeStoreAPIConnector,
    flatten_cart_record,
    flatten_product_record,
    flatten_user_record,
)
from src.connectors.file_connector import (
    FileConnector,
    SampleDataConnector,
    transform_csv_customer,
    transform_csv_product,
    transform_csv_sale,
)


class TestAPIConnector:
    """Tests for APIConnector class."""

    def test_extract_success(self):
        """Test successful API extraction."""
        with patch("requests.Session.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = [{"id": 1, "name": "test"}]
            mock_response.text = '[{"id": 1, "name": "test"}]'
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            connector = APIConnector("https://api.example.com")
            result = connector.extract("/test", "test_source")

            assert result.success is True
            assert result.records_count == 1
            assert result.source_name == "test_source"

    def test_extract_failure(self):
        """Test API extraction failure handling."""
        with patch("requests.Session.get") as mock_get:
            mock_get.side_effect = Exception("Connection failed")

            connector = APIConnector("https://api.example.com")
            result = connector.extract("/test", "test_source")

            assert result.success is False
            assert result.records_count == 0
            assert "Connection failed" in result.error_message


class TestFlattenFunctions:
    """Tests for API record flattening functions."""

    def test_flatten_product_record(self, sample_api_product):
        """Test flattening of product record."""
        flat = flatten_product_record(sample_api_product)

        assert flat["source_id"] == 1
        assert flat["title"] == "Fjallraven Backpack"
        assert flat["price"] == "109.95"
        assert flat["category"] == "men's clothing"
        assert flat["rating_rate"] == "3.9"
        assert flat["rating_count"] == "120"
        assert "raw_json" in flat

    def test_flatten_user_record(self, sample_api_user):
        """Test flattening of user record."""
        flat = flatten_user_record(sample_api_user)

        assert flat["source_id"] == 1
        assert flat["email"] == "john@gmail.com"
        assert flat["firstname"] == "John"
        assert flat["lastname"] == "Doe"
        assert flat["city"] == "kilcoole"
        assert "raw_json" in flat

    def test_flatten_cart_record(self, sample_api_cart):
        """Test flattening of cart record."""
        flat = flatten_cart_record(sample_api_cart)

        assert flat["source_id"] == 1
        assert flat["user_id"] == 1
        assert flat["cart_date"] == "2024-01-01"
        assert "products_json" in flat
        assert "raw_json" in flat


class TestFileConnector:
    """Tests for FileConnector class."""

    def test_extract_csv_success(self, sample_csv_dir):
        """Test successful CSV extraction."""
        connector = FileConnector(sample_csv_dir)
        result = connector.extract_csv("products.csv", "test_products")

        assert result.success is True
        assert result.records_count == 1
        assert result.records[0]["product_id"] == "P001"
        assert result.records[0]["product_name"] == "Test Product"

    def test_extract_csv_file_not_found(self, sample_csv_dir):
        """Test CSV extraction with missing file."""
        connector = FileConnector(sample_csv_dir)
        result = connector.extract_csv("nonexistent.csv", "test_source")

        assert result.success is False
        assert result.records_count == 0
        assert "not found" in result.error_message.lower()

    def test_extract_csv_adds_metadata(self, sample_csv_dir):
        """Test that CSV extraction adds file metadata."""
        connector = FileConnector(sample_csv_dir)
        result = connector.extract_csv("products.csv", "test_products")

        assert result.records[0]["_file_name"] == "products.csv"
        assert result.records[0]["_line_number"] == 2


class TestTransformFunctions:
    """Tests for CSV transform functions."""

    def test_transform_csv_product(self):
        """Test CSV product transformation."""
        record = {
            "product_id": "P001",
            "product_name": "Test",
            "category": "Electronics",
            "price": "99.99",
            "cost": "50.00",
            "stock_quantity": "100",
            "supplier": "TestCo",
            "_file_name": "products.csv",
            "_line_number": 2,
            "_raw_line": "P001,Test,Electronics,99.99,50.00,100,TestCo",
        }
        transformed = transform_csv_product(record)

        assert transformed["product_id"] == "P001"
        assert transformed["product_name"] == "Test"
        assert transformed["file_name"] == "products.csv"
        assert transformed["line_number"] == 2

    def test_transform_csv_customer(self):
        """Test CSV customer transformation."""
        record = {
            "customer_id": "C001",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@test.com",
            "phone": "555-1234",
            "city": "NYC",
            "state": "NY",
            "country": "USA",
            "registration_date": "2024-01-01",
            "_file_name": "customers.csv",
            "_line_number": 2,
            "_raw_line": "test,raw,line",
        }
        transformed = transform_csv_customer(record)

        assert transformed["customer_id"] == "C001"
        assert transformed["email"] == "john@test.com"

    def test_transform_csv_sale(self):
        """Test CSV sale transformation."""
        record = {
            "sale_id": "S001",
            "customer_id": "C001",
            "product_id": "P001",
            "quantity": "2",
            "unit_price": "99.99",
            "total_amount": "199.98",
            "sale_date": "2024-01-15",
            "payment_method": "credit_card",
            "_file_name": "sales.csv",
            "_line_number": 2,
            "_raw_line": "test,raw,line",
        }
        transformed = transform_csv_sale(record)

        assert transformed["sale_id"] == "S001"
        assert transformed["quantity"] == "2"
        assert transformed["payment_method"] == "credit_card"
