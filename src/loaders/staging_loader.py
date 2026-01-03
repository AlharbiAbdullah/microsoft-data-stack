"""Staging layer loader - cleans and validates raw data."""

import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from src.database import execute_query, get_cursor
from src.transformers.cleaners import (
    clean_date,
    clean_decimal,
    clean_email,
    clean_integer,
    clean_phone,
    clean_string,
    generate_full_name,
)
from src.transformers.validators import (
    CustomerValidator,
    ProductValidator,
    SaleValidator,
    ValidationResult,
)

logger = logging.getLogger(__name__)


class StagingLoader:
    """Loader for transforming raw data into staging layer."""

    def __init__(self, batch_id: UUID):
        self.batch_id = batch_id
        self.product_validator = ProductValidator()
        self.customer_validator = CustomerValidator()
        self.sale_validator = SaleValidator()

    def load_products(self) -> dict[str, int]:
        """
        Load products from raw layer to staging.

        Merges data from both API and CSV sources.
        """
        stats = {"processed": 0, "inserted": 0, "updated": 0, "rejected": 0}

        # Process API products
        api_products = execute_query(
            """
            SELECT source_id, title, price, description, category,
                   image_url, rating_rate, rating_count, raw_json
            FROM raw.api_products
            WHERE batch_id = (
                SELECT TOP 1 batch_id FROM raw.api_products ORDER BY ingested_at DESC
            )
            """
        )

        for record in api_products:
            stats["processed"] += 1
            cleaned = self._clean_api_product(record)
            result = self.product_validator.validate(cleaned)

            if result.is_valid:
                if self._upsert_staging_product(cleaned, "api"):
                    stats["inserted"] += 1
                else:
                    stats["updated"] += 1
            else:
                stats["rejected"] += 1
                logger.warning(f"Rejected product {record.get('source_id')}: {result.errors}")

        # Process CSV products
        csv_products = execute_query(
            """
            SELECT product_id, product_name, category, price, cost,
                   stock_quantity, supplier
            FROM raw.csv_products
            WHERE batch_id = (
                SELECT TOP 1 batch_id FROM raw.csv_products ORDER BY ingested_at DESC
            )
            """
        )

        for record in csv_products:
            stats["processed"] += 1
            cleaned = self._clean_csv_product(record)
            result = self.product_validator.validate(cleaned)

            if result.is_valid:
                if self._upsert_staging_product(cleaned, "csv"):
                    stats["inserted"] += 1
                else:
                    stats["updated"] += 1
            else:
                stats["rejected"] += 1
                logger.warning(f"Rejected product {record.get('product_id')}: {result.errors}")

        logger.info(f"Products staging complete: {stats}")
        return stats

    def load_customers(self) -> dict[str, int]:
        """Load customers from raw layer to staging."""
        stats = {"processed": 0, "inserted": 0, "updated": 0, "rejected": 0}

        # Process API users
        api_users = execute_query(
            """
            SELECT source_id, email, username, firstname, lastname,
                   city, phone
            FROM raw.api_users
            WHERE batch_id = (
                SELECT TOP 1 batch_id FROM raw.api_users ORDER BY ingested_at DESC
            )
            """
        )

        for record in api_users:
            stats["processed"] += 1
            cleaned = self._clean_api_user(record)
            result = self.customer_validator.validate(cleaned)

            if result.is_valid:
                if self._upsert_staging_customer(cleaned, "api"):
                    stats["inserted"] += 1
                else:
                    stats["updated"] += 1
            else:
                stats["rejected"] += 1
                logger.warning(f"Rejected user {record.get('source_id')}: {result.errors}")

        # Process CSV customers
        csv_customers = execute_query(
            """
            SELECT customer_id, first_name, last_name, email, phone,
                   city, state, country, registration_date
            FROM raw.csv_customers
            WHERE batch_id = (
                SELECT TOP 1 batch_id FROM raw.csv_customers ORDER BY ingested_at DESC
            )
            """
        )

        for record in csv_customers:
            stats["processed"] += 1
            cleaned = self._clean_csv_customer(record)
            result = self.customer_validator.validate(cleaned)

            if result.is_valid:
                if self._upsert_staging_customer(cleaned, "csv"):
                    stats["inserted"] += 1
                else:
                    stats["updated"] += 1
            else:
                stats["rejected"] += 1
                logger.warning(f"Rejected customer {record.get('customer_id')}: {result.errors}")

        logger.info(f"Customers staging complete: {stats}")
        return stats

    def load_sales(self) -> dict[str, int]:
        """Load sales from raw layer to staging."""
        stats = {"processed": 0, "inserted": 0, "updated": 0, "rejected": 0}

        # Process API carts (expand to individual line items)
        api_carts = execute_query(
            """
            SELECT source_id, user_id, cart_date, products_json
            FROM raw.api_carts
            WHERE batch_id = (
                SELECT TOP 1 batch_id FROM raw.api_carts ORDER BY ingested_at DESC
            )
            """
        )

        for cart in api_carts:
            products = json.loads(cart.get("products_json", "[]"))
            for idx, item in enumerate(products):
                stats["processed"] += 1
                cleaned = self._clean_api_cart_item(cart, item, idx)
                result = self.sale_validator.validate(cleaned)

                if result.is_valid:
                    if self._upsert_staging_sale(cleaned, "api"):
                        stats["inserted"] += 1
                    else:
                        stats["updated"] += 1
                else:
                    stats["rejected"] += 1

        # Process CSV sales
        csv_sales = execute_query(
            """
            SELECT sale_id, customer_id, product_id, quantity, unit_price,
                   total_amount, sale_date, payment_method
            FROM raw.csv_sales
            WHERE batch_id = (
                SELECT TOP 1 batch_id FROM raw.csv_sales ORDER BY ingested_at DESC
            )
            """
        )

        for record in csv_sales:
            stats["processed"] += 1
            cleaned = self._clean_csv_sale(record)
            result = self.sale_validator.validate(cleaned)

            if result.is_valid:
                if self._upsert_staging_sale(cleaned, "csv"):
                    stats["inserted"] += 1
                else:
                    stats["updated"] += 1
            else:
                stats["rejected"] += 1
                logger.warning(f"Rejected sale {record.get('sale_id')}: {result.errors}")

        logger.info(f"Sales staging complete: {stats}")
        return stats

    def _clean_api_product(self, record: dict) -> dict:
        """Clean API product record."""
        return {
            "source_product_id": str(record.get("source_id")),
            "title": clean_string(record.get("title")),
            "category": clean_string(record.get("category")),
            "price": clean_decimal(record.get("price")),
            "cost": None,
            "description": clean_string(record.get("description")),
            "image_url": clean_string(record.get("image_url")),
            "rating_rate": clean_decimal(record.get("rating_rate")),
            "rating_count": clean_integer(record.get("rating_count")),
            "stock_quantity": None,
            "supplier": None,
        }

    def _clean_csv_product(self, record: dict) -> dict:
        """Clean CSV product record."""
        return {
            "source_product_id": clean_string(record.get("product_id")),
            "title": clean_string(record.get("product_name")),
            "category": clean_string(record.get("category")),
            "price": clean_decimal(record.get("price")),
            "cost": clean_decimal(record.get("cost")),
            "description": None,
            "image_url": None,
            "rating_rate": None,
            "rating_count": None,
            "stock_quantity": clean_integer(record.get("stock_quantity")),
            "supplier": clean_string(record.get("supplier")),
        }

    def _clean_api_user(self, record: dict) -> dict:
        """Clean API user record."""
        return {
            "source_customer_id": str(record.get("source_id")),
            "email": clean_email(record.get("email")),
            "first_name": clean_string(record.get("firstname")),
            "last_name": clean_string(record.get("lastname")),
            "full_name": generate_full_name(
                record.get("firstname"), record.get("lastname")
            ),
            "phone": clean_phone(record.get("phone")),
            "city": clean_string(record.get("city")),
            "state": None,
            "country": None,
            "registration_date": None,
        }

    def _clean_csv_customer(self, record: dict) -> dict:
        """Clean CSV customer record."""
        return {
            "source_customer_id": clean_string(record.get("customer_id")),
            "email": clean_email(record.get("email")),
            "first_name": clean_string(record.get("first_name")),
            "last_name": clean_string(record.get("last_name")),
            "full_name": generate_full_name(
                record.get("first_name"), record.get("last_name")
            ),
            "phone": clean_phone(record.get("phone")),
            "city": clean_string(record.get("city")),
            "state": clean_string(record.get("state")),
            "country": clean_string(record.get("country")),
            "registration_date": clean_date(record.get("registration_date")),
        }

    def _clean_api_cart_item(self, cart: dict, item: dict, idx: int) -> dict:
        """Clean API cart item into a sale record."""
        # Generate a unique sale ID from cart_id and item index
        sale_id = f"{cart.get('source_id')}-{idx}"

        # Default price lookup (in real scenario, join with products)
        default_price = 50.0  # Placeholder

        quantity = clean_integer(item.get("quantity"), 1)
        unit_price = clean_decimal(default_price)
        total = unit_price * quantity if unit_price and quantity else None

        return {
            "source_sale_id": sale_id,
            "source_customer_id": str(cart.get("user_id")),
            "source_product_id": str(item.get("productId")),
            "quantity": quantity,
            "unit_price": unit_price,
            "total_amount": total,
            "sale_date": clean_date(cart.get("cart_date")),
            "payment_method": "api_cart",
        }

    def _clean_csv_sale(self, record: dict) -> dict:
        """Clean CSV sale record."""
        return {
            "source_sale_id": clean_string(record.get("sale_id")),
            "source_customer_id": clean_string(record.get("customer_id")),
            "source_product_id": clean_string(record.get("product_id")),
            "quantity": clean_integer(record.get("quantity")),
            "unit_price": clean_decimal(record.get("unit_price")),
            "total_amount": clean_decimal(record.get("total_amount")),
            "sale_date": clean_date(record.get("sale_date")),
            "payment_method": clean_string(record.get("payment_method")),
        }

    def _upsert_staging_product(self, record: dict, source: str) -> bool:
        """Insert or update product in staging. Returns True if inserted."""
        with get_cursor() as cursor:
            # Check if exists
            cursor.execute(
                """
                SELECT staging_product_id FROM staging.products
                WHERE source_product_id = ? AND source_system = ?
                """,
                (record["source_product_id"], source),
            )
            existing = cursor.fetchone()

            if existing:
                cursor.execute(
                    """
                    UPDATE staging.products SET
                        title = ?, category = ?, price = ?, cost = ?,
                        description = ?, image_url = ?, rating_rate = ?,
                        rating_count = ?, stock_quantity = ?, supplier = ?,
                        updated_at = GETDATE(), batch_id = ?
                    WHERE source_product_id = ? AND source_system = ?
                    """,
                    (
                        record["title"],
                        record["category"],
                        record["price"],
                        record["cost"],
                        record["description"],
                        record["image_url"],
                        record["rating_rate"],
                        record["rating_count"],
                        record["stock_quantity"],
                        record["supplier"],
                        str(self.batch_id),
                        record["source_product_id"],
                        source,
                    ),
                )
                return False
            else:
                cursor.execute(
                    """
                    INSERT INTO staging.products (
                        source_product_id, source_system, title, category, price,
                        cost, description, image_url, rating_rate, rating_count,
                        stock_quantity, supplier, batch_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record["source_product_id"],
                        source,
                        record["title"],
                        record["category"],
                        record["price"],
                        record["cost"],
                        record["description"],
                        record["image_url"],
                        record["rating_rate"],
                        record["rating_count"],
                        record["stock_quantity"],
                        record["supplier"],
                        str(self.batch_id),
                    ),
                )
                return True

    def _upsert_staging_customer(self, record: dict, source: str) -> bool:
        """Insert or update customer in staging. Returns True if inserted."""
        with get_cursor() as cursor:
            cursor.execute(
                """
                SELECT staging_customer_id FROM staging.customers
                WHERE source_customer_id = ? AND source_system = ?
                """,
                (record["source_customer_id"], source),
            )
            existing = cursor.fetchone()

            if existing:
                cursor.execute(
                    """
                    UPDATE staging.customers SET
                        email = ?, first_name = ?, last_name = ?, full_name = ?,
                        phone = ?, city = ?, state = ?, country = ?,
                        registration_date = ?, updated_at = GETDATE(), batch_id = ?
                    WHERE source_customer_id = ? AND source_system = ?
                    """,
                    (
                        record["email"],
                        record["first_name"],
                        record["last_name"],
                        record["full_name"],
                        record["phone"],
                        record["city"],
                        record["state"],
                        record["country"],
                        record["registration_date"],
                        str(self.batch_id),
                        record["source_customer_id"],
                        source,
                    ),
                )
                return False
            else:
                cursor.execute(
                    """
                    INSERT INTO staging.customers (
                        source_customer_id, source_system, email, first_name,
                        last_name, full_name, phone, city, state, country,
                        registration_date, batch_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record["source_customer_id"],
                        source,
                        record["email"],
                        record["first_name"],
                        record["last_name"],
                        record["full_name"],
                        record["phone"],
                        record["city"],
                        record["state"],
                        record["country"],
                        record["registration_date"],
                        str(self.batch_id),
                    ),
                )
                return True

    def _upsert_staging_sale(self, record: dict, source: str) -> bool:
        """Insert or update sale in staging. Returns True if inserted."""
        with get_cursor() as cursor:
            cursor.execute(
                """
                SELECT staging_sale_id FROM staging.sales
                WHERE source_sale_id = ? AND source_system = ?
                """,
                (record["source_sale_id"], source),
            )
            existing = cursor.fetchone()

            if existing:
                cursor.execute(
                    """
                    UPDATE staging.sales SET
                        source_customer_id = ?, source_product_id = ?,
                        quantity = ?, unit_price = ?, total_amount = ?,
                        sale_date = ?, payment_method = ?,
                        updated_at = GETDATE(), batch_id = ?
                    WHERE source_sale_id = ? AND source_system = ?
                    """,
                    (
                        record["source_customer_id"],
                        record["source_product_id"],
                        record["quantity"],
                        record["unit_price"],
                        record["total_amount"],
                        record["sale_date"],
                        record["payment_method"],
                        str(self.batch_id),
                        record["source_sale_id"],
                        source,
                    ),
                )
                return False
            else:
                cursor.execute(
                    """
                    INSERT INTO staging.sales (
                        source_sale_id, source_system, source_customer_id,
                        source_product_id, quantity, unit_price, total_amount,
                        sale_date, payment_method, batch_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record["source_sale_id"],
                        source,
                        record["source_customer_id"],
                        record["source_product_id"],
                        record["quantity"],
                        record["unit_price"],
                        record["total_amount"],
                        record["sale_date"],
                        record["payment_method"],
                        str(self.batch_id),
                    ),
                )
                return True
