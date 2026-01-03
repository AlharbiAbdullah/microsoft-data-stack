"""Raw layer loader for inserting extracted data into raw tables."""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from src.connectors.api_connector import (
    ExtractionResult,
    flatten_cart_record,
    flatten_product_record,
    flatten_user_record,
)
from src.connectors.file_connector import (
    FileExtractionResult,
    transform_csv_customer,
    transform_csv_product,
    transform_csv_sale,
)
from src.database import get_cursor

logger = logging.getLogger(__name__)


class RawLoader:
    """Loader for inserting data into raw layer tables."""

    def __init__(self, batch_id: UUID):
        self.batch_id = batch_id

    def load_api_products(self, result: ExtractionResult) -> int:
        """Load products from API into raw.api_products."""
        if not result.success or not result.records:
            logger.warning(f"No records to load for {result.source_name}")
            return 0

        records_loaded = 0
        with get_cursor() as cursor:
            for record in result.records:
                flat = flatten_product_record(record)
                cursor.execute(
                    """
                    INSERT INTO raw.api_products (
                        source_id, title, price, description, category,
                        image_url, rating_rate, rating_count, raw_json,
                        source_name, batch_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        flat["source_id"],
                        flat["title"],
                        flat["price"],
                        flat["description"],
                        flat["category"],
                        flat["image_url"],
                        flat["rating_rate"],
                        flat["rating_count"],
                        flat["raw_json"],
                        result.source_name,
                        str(self.batch_id),
                    ),
                )
                records_loaded += 1

        logger.info(f"Loaded {records_loaded} products to raw.api_products")
        return records_loaded

    def load_api_users(self, result: ExtractionResult) -> int:
        """Load users from API into raw.api_users."""
        if not result.success or not result.records:
            logger.warning(f"No records to load for {result.source_name}")
            return 0

        records_loaded = 0
        with get_cursor() as cursor:
            for record in result.records:
                flat = flatten_user_record(record)
                cursor.execute(
                    """
                    INSERT INTO raw.api_users (
                        source_id, email, username, password_hash,
                        firstname, lastname, city, street, zipcode,
                        phone, raw_json, source_name, batch_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        flat["source_id"],
                        flat["email"],
                        flat["username"],
                        flat["password_hash"],
                        flat["firstname"],
                        flat["lastname"],
                        flat["city"],
                        flat["street"],
                        flat["zipcode"],
                        flat["phone"],
                        flat["raw_json"],
                        result.source_name,
                        str(self.batch_id),
                    ),
                )
                records_loaded += 1

        logger.info(f"Loaded {records_loaded} users to raw.api_users")
        return records_loaded

    def load_api_carts(self, result: ExtractionResult) -> int:
        """Load carts from API into raw.api_carts."""
        if not result.success or not result.records:
            logger.warning(f"No records to load for {result.source_name}")
            return 0

        records_loaded = 0
        with get_cursor() as cursor:
            for record in result.records:
                flat = flatten_cart_record(record)
                cursor.execute(
                    """
                    INSERT INTO raw.api_carts (
                        source_id, user_id, cart_date, products_json,
                        raw_json, source_name, batch_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        flat["source_id"],
                        flat["user_id"],
                        flat["cart_date"],
                        flat["products_json"],
                        flat["raw_json"],
                        result.source_name,
                        str(self.batch_id),
                    ),
                )
                records_loaded += 1

        logger.info(f"Loaded {records_loaded} carts to raw.api_carts")
        return records_loaded

    def load_csv_products(self, result: FileExtractionResult) -> int:
        """Load products from CSV into raw.csv_products."""
        if not result.success or not result.records:
            logger.warning(f"No records to load for {result.source_name}")
            return 0

        records_loaded = 0
        with get_cursor() as cursor:
            for record in result.records:
                transformed = transform_csv_product(record)
                cursor.execute(
                    """
                    INSERT INTO raw.csv_products (
                        product_id, product_name, category, price, cost,
                        stock_quantity, supplier, raw_line, file_name,
                        line_number, batch_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        transformed["product_id"],
                        transformed["product_name"],
                        transformed["category"],
                        transformed["price"],
                        transformed["cost"],
                        transformed["stock_quantity"],
                        transformed["supplier"],
                        transformed["raw_line"],
                        transformed["file_name"],
                        transformed["line_number"],
                        str(self.batch_id),
                    ),
                )
                records_loaded += 1

        logger.info(f"Loaded {records_loaded} products to raw.csv_products")
        return records_loaded

    def load_csv_customers(self, result: FileExtractionResult) -> int:
        """Load customers from CSV into raw.csv_customers."""
        if not result.success or not result.records:
            logger.warning(f"No records to load for {result.source_name}")
            return 0

        records_loaded = 0
        with get_cursor() as cursor:
            for record in result.records:
                transformed = transform_csv_customer(record)
                cursor.execute(
                    """
                    INSERT INTO raw.csv_customers (
                        customer_id, first_name, last_name, email, phone,
                        city, state, country, registration_date, raw_line,
                        file_name, line_number, batch_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        transformed["customer_id"],
                        transformed["first_name"],
                        transformed["last_name"],
                        transformed["email"],
                        transformed["phone"],
                        transformed["city"],
                        transformed["state"],
                        transformed["country"],
                        transformed["registration_date"],
                        transformed["raw_line"],
                        transformed["file_name"],
                        transformed["line_number"],
                        str(self.batch_id),
                    ),
                )
                records_loaded += 1

        logger.info(f"Loaded {records_loaded} customers to raw.csv_customers")
        return records_loaded

    def load_csv_sales(self, result: FileExtractionResult) -> int:
        """Load sales from CSV into raw.csv_sales."""
        if not result.success or not result.records:
            logger.warning(f"No records to load for {result.source_name}")
            return 0

        records_loaded = 0
        with get_cursor() as cursor:
            for record in result.records:
                transformed = transform_csv_sale(record)
                cursor.execute(
                    """
                    INSERT INTO raw.csv_sales (
                        sale_id, customer_id, product_id, quantity, unit_price,
                        total_amount, sale_date, payment_method, raw_line,
                        file_name, line_number, batch_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        transformed["sale_id"],
                        transformed["customer_id"],
                        transformed["product_id"],
                        transformed["quantity"],
                        transformed["unit_price"],
                        transformed["total_amount"],
                        transformed["sale_date"],
                        transformed["payment_method"],
                        transformed["raw_line"],
                        transformed["file_name"],
                        transformed["line_number"],
                        str(self.batch_id),
                    ),
                )
                records_loaded += 1

        logger.info(f"Loaded {records_loaded} sales to raw.csv_sales")
        return records_loaded
