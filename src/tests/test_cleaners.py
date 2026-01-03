"""Tests for data cleaning utilities."""

from datetime import date
from decimal import Decimal

import pytest

from src.transformers.cleaners import (
    calculate_date_key,
    clean_date,
    clean_decimal,
    clean_email,
    clean_integer,
    clean_phone,
    clean_string,
    determine_customer_segment,
    determine_region,
    generate_full_name,
)


class TestCleanString:
    """Tests for clean_string function."""

    def test_clean_string_normal(self):
        """Test cleaning normal strings."""
        assert clean_string("  hello  ") == "hello"
        assert clean_string("test") == "test"

    def test_clean_string_empty(self):
        """Test cleaning empty/null strings."""
        assert clean_string(None) is None
        assert clean_string("") is None
        assert clean_string("   ") is None

    def test_clean_string_numeric(self):
        """Test cleaning numeric values."""
        assert clean_string(123) == "123"
        assert clean_string(45.67) == "45.67"


class TestCleanDecimal:
    """Tests for clean_decimal function."""

    def test_clean_decimal_valid(self):
        """Test cleaning valid decimal values."""
        assert clean_decimal("99.99") == Decimal("99.99")
        assert clean_decimal(100) == Decimal("100")
        assert clean_decimal("1,234.56") == Decimal("1234.56")

    def test_clean_decimal_invalid(self):
        """Test cleaning invalid decimal values."""
        assert clean_decimal(None) is None
        assert clean_decimal("abc") is None
        assert clean_decimal("abc", Decimal("0")) == Decimal("0")


class TestCleanInteger:
    """Tests for clean_integer function."""

    def test_clean_integer_valid(self):
        """Test cleaning valid integer values."""
        assert clean_integer("100") == 100
        assert clean_integer(50) == 50
        assert clean_integer("1,000") == 1000
        assert clean_integer("99.9") == 99

    def test_clean_integer_invalid(self):
        """Test cleaning invalid integer values."""
        assert clean_integer(None) is None
        assert clean_integer("abc") is None
        assert clean_integer("abc", 0) == 0


class TestCleanDate:
    """Tests for clean_date function."""

    def test_clean_date_iso_format(self):
        """Test cleaning ISO format dates."""
        assert clean_date("2024-01-15") == date(2024, 1, 15)
        assert clean_date("2024-01-15T10:30:00") == date(2024, 1, 15)

    def test_clean_date_object(self):
        """Test cleaning date objects."""
        d = date(2024, 1, 15)
        assert clean_date(d) == d

    def test_clean_date_invalid(self):
        """Test cleaning invalid dates."""
        assert clean_date(None) is None
        assert clean_date("not-a-date") is None
        assert clean_date("2024-13-01") is None


class TestCleanEmail:
    """Tests for clean_email function."""

    def test_clean_email_valid(self):
        """Test cleaning valid emails."""
        assert clean_email("Test@Example.COM") == "test@example.com"
        assert clean_email("  user@domain.org  ") == "user@domain.org"

    def test_clean_email_invalid(self):
        """Test cleaning invalid emails."""
        assert clean_email(None) is None
        assert clean_email("not-an-email") is None


class TestCleanPhone:
    """Tests for clean_phone function."""

    def test_clean_phone_valid(self):
        """Test cleaning valid phone numbers."""
        assert clean_phone("+1-555-123-4567") == "+1-555-123-4567"
        assert clean_phone("(555) 123-4567") == "(555) 123-4567"

    def test_clean_phone_invalid(self):
        """Test cleaning invalid phone numbers."""
        assert clean_phone(None) is None


class TestGenerateFullName:
    """Tests for generate_full_name function."""

    def test_full_name_both_parts(self):
        """Test generating full name from both parts."""
        assert generate_full_name("John", "Doe") == "John Doe"

    def test_full_name_first_only(self):
        """Test generating name with first name only."""
        assert generate_full_name("John", None) == "John"
        assert generate_full_name("John", "") == "John"

    def test_full_name_last_only(self):
        """Test generating name with last name only."""
        assert generate_full_name(None, "Doe") == "Doe"

    def test_full_name_neither(self):
        """Test generating name with neither part."""
        assert generate_full_name(None, None) is None


class TestDetermineRegion:
    """Tests for determine_region function."""

    def test_us_regions(self):
        """Test US regional classification."""
        assert determine_region("USA", "NY") == "Northeast"
        assert determine_region("USA", "CA") == "West"
        assert determine_region("USA", "TX") == "Southwest"
        assert determine_region("USA", "IL") == "Midwest"
        assert determine_region("USA", "FL") == "Southeast"

    def test_international_regions(self):
        """Test international regional classification."""
        assert determine_region("Germany") == "Europe"
        assert determine_region("Japan") == "Asia Pacific"
        assert determine_region("Brazil") == "Latin America"

    def test_unknown_region(self):
        """Test unknown regions."""
        assert determine_region("Unknown Country") == "International"
        assert determine_region(None) is None


class TestCalculateDateKey:
    """Tests for calculate_date_key function."""

    def test_calculate_date_key_valid(self):
        """Test calculating date key."""
        assert calculate_date_key(date(2024, 1, 15)) == 20240115
        assert calculate_date_key(date(2024, 12, 31)) == 20241231

    def test_calculate_date_key_null(self):
        """Test calculating date key for null."""
        assert calculate_date_key(None) is None


class TestDetermineCustomerSegment:
    """Tests for determine_customer_segment function."""

    def test_premium_segment(self):
        """Test premium customer classification."""
        assert determine_customer_segment(Decimal("1000"), 5) == "Premium"
        assert determine_customer_segment(Decimal("500"), 10) == "Premium"

    def test_regular_segment(self):
        """Test regular customer classification."""
        assert determine_customer_segment(Decimal("500"), 3) == "Regular"
        assert determine_customer_segment(Decimal("300"), 5) == "Regular"

    def test_occasional_segment(self):
        """Test occasional customer classification."""
        assert determine_customer_segment(Decimal("100"), 2) == "Occasional"
        assert determine_customer_segment(Decimal("150"), 1) == "Occasional"

    def test_new_segment(self):
        """Test new customer classification."""
        assert determine_customer_segment(Decimal("50"), 1) == "New"
        assert determine_customer_segment(Decimal("0"), 0) == "New"
