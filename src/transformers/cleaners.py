"""Data cleaning and transformation utilities."""

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


def clean_string(value: Any) -> str | None:
    """Clean and normalize a string value."""
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned if cleaned else None


def clean_decimal(value: Any, default: Decimal | None = None) -> Decimal | None:
    """Clean and convert value to Decimal."""
    if value is None:
        return default
    try:
        cleaned = str(value).strip().replace(",", "")
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return default


def clean_integer(value: Any, default: int | None = None) -> int | None:
    """Clean and convert value to integer."""
    if value is None:
        return default
    try:
        cleaned = str(value).strip().replace(",", "")
        return int(float(cleaned))
    except (ValueError, TypeError):
        return default


def clean_date(value: Any) -> date | None:
    """Clean and convert value to date."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    # Try common date formats
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%SZ",
        "%m/%d/%Y",
        "%d/%m/%Y",
    ]

    value_str = str(value).strip()[:26]  # Limit length for parsing
    for fmt in formats:
        try:
            return datetime.strptime(value_str[:len(fmt) + 5], fmt).date()
        except ValueError:
            continue

    return None


def clean_email(value: Any) -> str | None:
    """Clean and normalize email address."""
    if value is None:
        return None
    cleaned = str(value).strip().lower()
    return cleaned if "@" in cleaned else None


def clean_phone(value: Any) -> str | None:
    """Clean phone number, keeping only digits and standard separators."""
    if value is None:
        return None
    # Keep digits, +, -, and spaces
    cleaned = re.sub(r"[^\d+\-\s()]", "", str(value))
    return cleaned.strip() if cleaned else None


def generate_full_name(first_name: Any, last_name: Any) -> str | None:
    """Generate full name from first and last name."""
    first = clean_string(first_name)
    last = clean_string(last_name)

    if first and last:
        return f"{first} {last}"
    return first or last


def determine_region(country: str | None, state: str | None = None) -> str | None:
    """Determine region based on country/state."""
    if not country:
        return None

    country_lower = country.lower()

    # US regions
    us_regions = {
        "northeast": ["ny", "nj", "pa", "ct", "ma", "ri", "vt", "nh", "me"],
        "southeast": ["fl", "ga", "nc", "sc", "va", "wv", "md", "de", "dc"],
        "midwest": ["il", "oh", "mi", "in", "wi", "mn", "ia", "mo", "nd", "sd", "ne", "ks"],
        "southwest": ["tx", "ok", "nm", "az"],
        "west": ["ca", "wa", "or", "nv", "ut", "co", "wy", "mt", "id", "ak", "hi"],
    }

    if country_lower in ["usa", "us", "united states"]:
        if state:
            state_lower = state.lower()
            for region, states in us_regions.items():
                if state_lower in states:
                    return region.title()
        return "USA"

    # International regions
    region_mapping = {
        "north america": ["canada", "mexico"],
        "europe": [
            "uk",
            "united kingdom",
            "germany",
            "france",
            "italy",
            "spain",
            "netherlands",
        ],
        "asia pacific": ["china", "japan", "australia", "india", "singapore"],
        "latin america": ["brazil", "argentina", "chile", "colombia"],
    }

    for region, countries in region_mapping.items():
        if country_lower in countries:
            return region.title()

    return "International"


def calculate_date_key(dt: date | None) -> int | None:
    """Calculate date key in YYYYMMDD format."""
    if dt is None:
        return None
    return int(dt.strftime("%Y%m%d"))


def determine_customer_segment(total_spent: Decimal, order_count: int) -> str:
    """Determine customer segment based on spending behavior."""
    if total_spent >= 1000 or order_count >= 10:
        return "Premium"
    if total_spent >= 500 or order_count >= 5:
        return "Regular"
    if total_spent >= 100 or order_count >= 2:
        return "Occasional"
    return "New"
