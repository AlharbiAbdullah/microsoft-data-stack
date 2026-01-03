"""Tests for data validators."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from src.transformers.validators import (
    CustomerValidator,
    ProductValidator,
    SaleValidator,
    Validator,
)


class TestBaseValidator:
    """Tests for base Validator class."""

    def test_is_not_null_valid(self):
        """Test is_not_null with valid values."""
        assert Validator.is_not_null("value", "field") is None
        assert Validator.is_not_null(123, "field") is None
        assert Validator.is_not_null(0, "field") is None

    def test_is_not_null_invalid(self):
        """Test is_not_null with invalid values."""
        assert Validator.is_not_null(None, "field") is not None
        assert Validator.is_not_null("", "field") is not None
        assert Validator.is_not_null("   ", "field") is not None

    def test_is_positive_number_valid(self):
        """Test is_positive_number with valid values."""
        assert Validator.is_positive_number(10, "field") is None
        assert Validator.is_positive_number("99.99", "field") is None
        assert Validator.is_positive_number(0.01, "field") is None

    def test_is_positive_number_invalid(self):
        """Test is_positive_number with invalid values."""
        assert Validator.is_positive_number(0, "field") is not None
        assert Validator.is_positive_number(-5, "field") is not None
        assert Validator.is_positive_number("abc", "field") is not None

    def test_is_valid_email_valid(self):
        """Test is_valid_email with valid emails."""
        assert Validator.is_valid_email("test@example.com", "email") is None
        assert Validator.is_valid_email("user.name+tag@domain.co.uk", "email") is None
        assert Validator.is_valid_email(None, "email") is None  # Null allowed

    def test_is_valid_email_invalid(self):
        """Test is_valid_email with invalid emails."""
        assert Validator.is_valid_email("not-an-email", "email") is not None
        assert Validator.is_valid_email("missing@domain", "email") is not None
        assert Validator.is_valid_email("@nodomain.com", "email") is not None

    def test_is_valid_date_valid(self):
        """Test is_valid_date with valid dates."""
        assert Validator.is_valid_date("2024-01-15", "date") is None
        assert Validator.is_valid_date(date(2024, 1, 15), "date") is None
        assert Validator.is_valid_date(None, "date") is None

    def test_is_valid_date_invalid(self):
        """Test is_valid_date with invalid dates."""
        assert Validator.is_valid_date("not-a-date", "date") is not None
        assert Validator.is_valid_date("2024-13-01", "date") is not None

    def test_is_not_future_date_valid(self):
        """Test is_not_future_date with valid dates."""
        assert Validator.is_not_future_date("2024-01-01", "date") is None
        assert Validator.is_not_future_date(date.today(), "date") is None

    def test_is_not_future_date_invalid(self):
        """Test is_not_future_date with future dates."""
        future = date.today() + timedelta(days=30)
        assert Validator.is_not_future_date(str(future), "date") is not None

    def test_is_in_range_valid(self):
        """Test is_in_range with valid values."""
        assert Validator.is_in_range(5, "field", 0, 10) is None
        assert Validator.is_in_range(0, "field", 0, 10) is None
        assert Validator.is_in_range(10, "field", 0, 10) is None

    def test_is_in_range_invalid(self):
        """Test is_in_range with invalid values."""
        assert Validator.is_in_range(-1, "field", 0, 10) is not None
        assert Validator.is_in_range(11, "field", 0, 10) is not None


class TestProductValidator:
    """Tests for ProductValidator class."""

    def test_validate_valid_product(self):
        """Test validation of a valid product."""
        validator = ProductValidator()
        product = {
            "title": "Test Product",
            "price": "99.99",
            "category": "Electronics",
            "rating_rate": "4.5",
        }
        result = validator.validate(product)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_missing_title(self):
        """Test validation fails for missing title."""
        validator = ProductValidator()
        product = {"title": None, "price": "99.99"}
        result = validator.validate(product)

        assert result.is_valid is False
        assert any("title" in e.lower() for e in result.errors)

    def test_validate_invalid_price(self):
        """Test validation fails for invalid price."""
        validator = ProductValidator()
        product = {"title": "Test", "price": "-10"}
        result = validator.validate(product)

        assert result.is_valid is False
        assert any("price" in e.lower() for e in result.errors)

    def test_validate_invalid_rating(self):
        """Test validation fails for out-of-range rating."""
        validator = ProductValidator()
        product = {"title": "Test", "price": "99.99", "rating_rate": "6.0"}
        result = validator.validate(product)

        assert result.is_valid is False
        assert any("rating" in e.lower() for e in result.errors)


class TestSaleValidator:
    """Tests for SaleValidator class."""

    def test_validate_valid_sale(self):
        """Test validation of a valid sale."""
        validator = SaleValidator()
        sale = {
            "quantity": "2",
            "unit_price": "50.00",
            "total_amount": "100.00",
            "sale_date": "2024-01-15",
        }
        result = validator.validate(sale)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_missing_quantity(self):
        """Test validation fails for missing quantity."""
        validator = SaleValidator()
        sale = {
            "quantity": None,
            "unit_price": "50.00",
            "total_amount": "100.00",
            "sale_date": "2024-01-15",
        }
        result = validator.validate(sale)

        assert result.is_valid is False
        assert any("quantity" in e.lower() for e in result.errors)

    def test_validate_total_mismatch(self):
        """Test validation catches total amount mismatch."""
        validator = SaleValidator()
        sale = {
            "quantity": "2",
            "unit_price": "50.00",
            "total_amount": "200.00",  # Should be 100.00
            "sale_date": "2024-01-15",
        }
        result = validator.validate(sale)

        assert result.is_valid is False
        assert any("total" in e.lower() for e in result.errors)

    def test_validate_future_date(self):
        """Test validation fails for future sale date."""
        validator = SaleValidator()
        future = date.today() + timedelta(days=30)
        sale = {
            "quantity": "1",
            "unit_price": "50.00",
            "total_amount": "50.00",
            "sale_date": str(future),
        }
        result = validator.validate(sale)

        assert result.is_valid is False
        assert any("future" in e.lower() for e in result.errors)


class TestCustomerValidator:
    """Tests for CustomerValidator class."""

    def test_validate_valid_customer(self):
        """Test validation of a valid customer."""
        validator = CustomerValidator()
        customer = {
            "email": "test@example.com",
            "registration_date": "2024-01-15",
        }
        result = validator.validate(customer)

        assert result.is_valid is True

    def test_validate_invalid_email(self):
        """Test validation catches invalid email."""
        validator = CustomerValidator()
        customer = {"email": "not-an-email"}
        result = validator.validate(customer)

        assert result.is_valid is False
        assert any("email" in e.lower() for e in result.errors)
