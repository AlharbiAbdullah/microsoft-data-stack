"""Data validation rules for the transformation layer."""

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Callable


@dataclass
class ValidationResult:
    """Result of a validation check."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)

    def add_error(self, error: str) -> None:
        """Add an error and mark as invalid."""
        self.is_valid = False
        self.errors.append(error)


class Validator:
    """Base validator with common validation rules."""

    @staticmethod
    def is_not_null(value: Any, field_name: str) -> str | None:
        """Check if value is not null/empty."""
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return f"{field_name} cannot be null or empty"
        return None

    @staticmethod
    def is_positive_number(value: Any, field_name: str) -> str | None:
        """Check if value is a positive number."""
        try:
            num = Decimal(str(value))
            if num <= 0:
                return f"{field_name} must be positive, got {value}"
        except (InvalidOperation, ValueError, TypeError):
            return f"{field_name} is not a valid number: {value}"
        return None

    @staticmethod
    def is_non_negative_number(value: Any, field_name: str) -> str | None:
        """Check if value is zero or positive."""
        try:
            num = Decimal(str(value))
            if num < 0:
                return f"{field_name} cannot be negative, got {value}"
        except (InvalidOperation, ValueError, TypeError):
            return f"{field_name} is not a valid number: {value}"
        return None

    @staticmethod
    def is_valid_email(value: Any, field_name: str) -> str | None:
        """Check if value is a valid email format."""
        if value is None:
            return None  # Allow null emails
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, str(value)):
            return f"{field_name} is not a valid email: {value}"
        return None

    @staticmethod
    def is_valid_date(value: Any, field_name: str) -> str | None:
        """Check if value can be parsed as a date."""
        if value is None:
            return None
        try:
            if isinstance(value, (date, datetime)):
                return None
            datetime.strptime(str(value)[:10], "%Y-%m-%d")
        except ValueError:
            return f"{field_name} is not a valid date: {value}"
        return None

    @staticmethod
    def is_not_future_date(value: Any, field_name: str) -> str | None:
        """Check if date is not in the future."""
        if value is None:
            return None
        try:
            if isinstance(value, datetime):
                dt = value.date()
            elif isinstance(value, date):
                dt = value
            else:
                dt = datetime.strptime(str(value)[:10], "%Y-%m-%d").date()

            if dt > date.today():
                return f"{field_name} cannot be in the future: {value}"
        except ValueError:
            pass  # Invalid date handled by is_valid_date
        return None

    @staticmethod
    def is_in_range(
        value: Any, field_name: str, min_val: float, max_val: float
    ) -> str | None:
        """Check if value is within a range."""
        try:
            num = float(value)
            if num < min_val or num > max_val:
                return f"{field_name} must be between {min_val} and {max_val}, got {value}"
        except (ValueError, TypeError):
            return f"{field_name} is not a valid number: {value}"
        return None


class ProductValidator(Validator):
    """Validator for product records."""

    def validate(self, record: dict[str, Any]) -> ValidationResult:
        """Validate a product record."""
        result = ValidationResult(is_valid=True)

        # Required fields
        if error := self.is_not_null(record.get("title"), "title"):
            result.add_error(error)

        if error := self.is_not_null(record.get("price"), "price"):
            result.add_error(error)
        elif error := self.is_positive_number(record.get("price"), "price"):
            result.add_error(error)

        # Optional validations
        if record.get("cost") is not None:
            if error := self.is_non_negative_number(record.get("cost"), "cost"):
                result.add_error(error)

        if record.get("rating_rate") is not None:
            if error := self.is_in_range(record.get("rating_rate"), "rating_rate", 0, 5):
                result.add_error(error)

        return result


class CustomerValidator(Validator):
    """Validator for customer records."""

    def validate(self, record: dict[str, Any]) -> ValidationResult:
        """Validate a customer record."""
        result = ValidationResult(is_valid=True)

        # Email validation (warning level - don't reject)
        if record.get("email"):
            if error := self.is_valid_email(record.get("email"), "email"):
                result.add_error(error)

        # Date validation
        if record.get("registration_date"):
            if error := self.is_valid_date(
                record.get("registration_date"), "registration_date"
            ):
                result.add_error(error)

        return result


class SaleValidator(Validator):
    """Validator for sale records."""

    def validate(self, record: dict[str, Any]) -> ValidationResult:
        """Validate a sale record."""
        result = ValidationResult(is_valid=True)

        # Required fields
        if error := self.is_not_null(record.get("quantity"), "quantity"):
            result.add_error(error)
        elif error := self.is_positive_number(record.get("quantity"), "quantity"):
            result.add_error(error)

        if error := self.is_not_null(record.get("unit_price"), "unit_price"):
            result.add_error(error)
        elif error := self.is_positive_number(record.get("unit_price"), "unit_price"):
            result.add_error(error)

        if error := self.is_not_null(record.get("total_amount"), "total_amount"):
            result.add_error(error)
        elif error := self.is_positive_number(record.get("total_amount"), "total_amount"):
            result.add_error(error)

        # Date validation
        if error := self.is_not_null(record.get("sale_date"), "sale_date"):
            result.add_error(error)
        elif error := self.is_valid_date(record.get("sale_date"), "sale_date"):
            result.add_error(error)
        elif error := self.is_not_future_date(record.get("sale_date"), "sale_date"):
            result.add_error(error)

        # Business rule: total should approximately equal quantity * unit_price
        try:
            qty = Decimal(str(record.get("quantity", 0)))
            price = Decimal(str(record.get("unit_price", 0)))
            total = Decimal(str(record.get("total_amount", 0)))
            expected = qty * price

            # Allow 1% tolerance for rounding
            if abs(total - expected) > expected * Decimal("0.01"):
                result.add_error(
                    f"total_amount ({total}) doesn't match quantity * unit_price ({expected})"
                )
        except (InvalidOperation, ValueError, TypeError):
            pass  # Already caught by other validations

        return result
