"""API connector for extracting data from REST APIs."""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Result of an API extraction operation."""

    source_name: str
    endpoint: str
    records: list[dict[str, Any]]
    records_count: int
    extracted_at: datetime
    raw_response: str
    success: bool
    error_message: str | None = None


class APIConnector:
    """Connector for extracting data from REST APIs."""

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = self._create_session(max_retries)

    def _create_session(self, max_retries: int) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def extract(self, endpoint: str, source_name: str) -> ExtractionResult:
        """
        Extract data from an API endpoint.

        Args:
            endpoint: API endpoint path (e.g., '/products')
            source_name: Name to identify this data source

        Returns:
            ExtractionResult with extracted records and metadata
        """
        url = f"{self.base_url}{endpoint}"
        extracted_at = datetime.now(timezone.utc)

        logger.info(f"Extracting from {url}")

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            records = data if isinstance(data, list) else [data]

            logger.info(f"Extracted {len(records)} records from {source_name}")

            return ExtractionResult(
                source_name=source_name,
                endpoint=endpoint,
                records=records,
                records_count=len(records),
                extracted_at=extracted_at,
                raw_response=response.text,
                success=True,
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to extract from {url}: {e}")
            return ExtractionResult(
                source_name=source_name,
                endpoint=endpoint,
                records=[],
                records_count=0,
                extracted_at=extracted_at,
                raw_response="",
                success=False,
                error_message=str(e),
            )


class FakeStoreAPIConnector(APIConnector):
    """Connector specifically for the Fake Store API."""

    BASE_URL = "https://fakestoreapi.com"

    def __init__(self):
        super().__init__(self.BASE_URL)

    def extract_products(self) -> ExtractionResult:
        """Extract all products from Fake Store API."""
        return self.extract("/products", "api_products")

    def extract_users(self) -> ExtractionResult:
        """Extract all users from Fake Store API."""
        return self.extract("/users", "api_users")

    def extract_carts(self) -> ExtractionResult:
        """Extract all carts (sales) from Fake Store API."""
        return self.extract("/carts", "api_carts")

    def extract_all(self) -> dict[str, ExtractionResult]:
        """Extract all available data from Fake Store API."""
        return {
            "products": self.extract_products(),
            "users": self.extract_users(),
            "carts": self.extract_carts(),
        }


def flatten_user_record(user: dict[str, Any]) -> dict[str, Any]:
    """Flatten nested user record from Fake Store API."""
    name = user.get("name", {})
    address = user.get("address", {})

    return {
        "source_id": user.get("id"),
        "email": user.get("email"),
        "username": user.get("username"),
        "password_hash": user.get("password"),
        "firstname": name.get("firstname"),
        "lastname": name.get("lastname"),
        "city": address.get("city"),
        "street": address.get("street"),
        "zipcode": address.get("zipcode"),
        "phone": user.get("phone"),
        "raw_json": json.dumps(user),
    }


def flatten_product_record(product: dict[str, Any]) -> dict[str, Any]:
    """Flatten product record from Fake Store API."""
    rating = product.get("rating", {})

    return {
        "source_id": product.get("id"),
        "title": product.get("title"),
        "price": str(product.get("price")),
        "description": product.get("description"),
        "category": product.get("category"),
        "image_url": product.get("image"),
        "rating_rate": str(rating.get("rate")),
        "rating_count": str(rating.get("count")),
        "raw_json": json.dumps(product),
    }


def flatten_cart_record(cart: dict[str, Any]) -> dict[str, Any]:
    """Flatten cart record from Fake Store API."""
    return {
        "source_id": cart.get("id"),
        "user_id": cart.get("userId"),
        "cart_date": cart.get("date"),
        "products_json": json.dumps(cart.get("products", [])),
        "raw_json": json.dumps(cart),
    }
