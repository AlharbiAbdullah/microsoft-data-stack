"""Data Warehouse loader - loads dimensions and facts from staging."""

import logging
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from src.database import execute_query, get_cursor
from src.transformers.cleaners import (
    calculate_date_key,
    determine_customer_segment,
    determine_region,
)

logger = logging.getLogger(__name__)


class DimensionLoader:
    """Loader for dimension tables."""

    def __init__(self, batch_id: UUID):
        self.batch_id = batch_id

    def load_dim_product(self) -> dict[str, int]:
        """
        Load products from staging to dim_product.

        Implements SCD Type 2 for tracking historical changes.
        """
        stats = {"processed": 0, "inserted": 0, "updated": 0, "unchanged": 0}

        staging_products = execute_query(
            """
            SELECT
                source_product_id + '-' + source_system AS product_id,
                title, category, price, cost, description, image_url,
                rating_rate, rating_count, stock_quantity, supplier
            FROM staging.products
            WHERE is_valid = 1
            """
        )

        for record in staging_products:
            stats["processed"] += 1
            result = self._upsert_dim_product(record)
            stats[result] += 1

        logger.info(f"dim_product load complete: {stats}")
        return stats

    def load_dim_customer(self) -> dict[str, int]:
        """Load customers from staging to dim_customer."""
        stats = {"processed": 0, "inserted": 0, "updated": 0, "unchanged": 0}

        staging_customers = execute_query(
            """
            SELECT
                source_customer_id + '-' + source_system AS customer_id,
                email, first_name, last_name, full_name, phone,
                city, state, country, registration_date
            FROM staging.customers
            WHERE is_valid = 1
            """
        )

        for record in staging_customers:
            stats["processed"] += 1
            # Add derived fields
            record["region"] = determine_region(
                record.get("country"), record.get("state")
            )
            record["customer_segment"] = "New"  # Will be updated after fact load

            result = self._upsert_dim_customer(record)
            stats[result] += 1

        logger.info(f"dim_customer load complete: {stats}")
        return stats

    def _upsert_dim_product(self, record: dict[str, Any]) -> str:
        """Insert or update product dimension. Returns operation type."""
        with get_cursor() as cursor:
            # Check for existing current record
            cursor.execute(
                """
                SELECT product_key, price, cost, stock_quantity
                FROM dw.dim_product
                WHERE product_id = ? AND is_current = 1
                """,
                (record["product_id"],),
            )
            existing = cursor.fetchone()

            if existing:
                # Check if any SCD Type 2 fields changed
                old_price = existing[1]
                old_cost = existing[2]
                new_price = record.get("price")
                new_cost = record.get("cost")

                price_changed = (
                    old_price != new_price if new_price is not None else False
                )
                cost_changed = old_cost != new_cost if new_cost is not None else False

                if price_changed or cost_changed:
                    # Close old record
                    cursor.execute(
                        """
                        UPDATE dw.dim_product
                        SET effective_to = CAST(GETDATE() AS DATE),
                            is_current = 0,
                            updated_at = GETDATE()
                        WHERE product_key = ?
                        """,
                        (existing[0],),
                    )
                    # Insert new version
                    self._insert_dim_product(cursor, record)
                    return "updated"
                else:
                    # Update non-SCD fields only
                    cursor.execute(
                        """
                        UPDATE dw.dim_product SET
                            title = ?, category = ?, description = ?,
                            image_url = ?, rating_rate = ?, rating_count = ?,
                            stock_quantity = ?, supplier = ?, updated_at = GETDATE()
                        WHERE product_key = ?
                        """,
                        (
                            record["title"],
                            record["category"],
                            record.get("description"),
                            record.get("image_url"),
                            record.get("rating_rate"),
                            record.get("rating_count"),
                            record.get("stock_quantity"),
                            record.get("supplier"),
                            existing[0],
                        ),
                    )
                    return "unchanged"
            else:
                self._insert_dim_product(cursor, record)
                return "inserted"

    def _insert_dim_product(self, cursor, record: dict[str, Any]) -> None:
        """Insert new product dimension record."""
        cursor.execute(
            """
            INSERT INTO dw.dim_product (
                product_id, title, category, price, cost, description,
                image_url, rating_rate, rating_count, stock_quantity, supplier,
                effective_from, effective_to, is_current
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CAST(GETDATE() AS DATE), '9999-12-31', 1)
            """,
            (
                record["product_id"],
                record["title"],
                record["category"],
                record.get("price"),
                record.get("cost"),
                record.get("description"),
                record.get("image_url"),
                record.get("rating_rate"),
                record.get("rating_count"),
                record.get("stock_quantity"),
                record.get("supplier"),
            ),
        )

    def _upsert_dim_customer(self, record: dict[str, Any]) -> str:
        """Insert or update customer dimension. Returns operation type."""
        with get_cursor() as cursor:
            cursor.execute(
                """
                SELECT customer_key, city, country
                FROM dw.dim_customer
                WHERE customer_id = ? AND is_current = 1
                """,
                (record["customer_id"],),
            )
            existing = cursor.fetchone()

            if existing:
                old_city = existing[1]
                old_country = existing[2]

                # SCD Type 2 on location changes
                location_changed = (
                    old_city != record.get("city")
                    or old_country != record.get("country")
                )

                if location_changed:
                    cursor.execute(
                        """
                        UPDATE dw.dim_customer
                        SET effective_to = CAST(GETDATE() AS DATE),
                            is_current = 0,
                            updated_at = GETDATE()
                        WHERE customer_key = ?
                        """,
                        (existing[0],),
                    )
                    self._insert_dim_customer(cursor, record)
                    return "updated"
                else:
                    cursor.execute(
                        """
                        UPDATE dw.dim_customer SET
                            email = ?, first_name = ?, last_name = ?, full_name = ?,
                            phone = ?, region = ?, updated_at = GETDATE()
                        WHERE customer_key = ?
                        """,
                        (
                            record.get("email"),
                            record.get("first_name"),
                            record.get("last_name"),
                            record.get("full_name"),
                            record.get("phone"),
                            record.get("region"),
                            existing[0],
                        ),
                    )
                    return "unchanged"
            else:
                self._insert_dim_customer(cursor, record)
                return "inserted"

    def _insert_dim_customer(self, cursor, record: dict[str, Any]) -> None:
        """Insert new customer dimension record."""
        cursor.execute(
            """
            INSERT INTO dw.dim_customer (
                customer_id, email, first_name, last_name, full_name, phone,
                city, state, country, region, registration_date, customer_segment,
                effective_from, effective_to, is_current
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CAST(GETDATE() AS DATE), '9999-12-31', 1)
            """,
            (
                record["customer_id"],
                record.get("email"),
                record.get("first_name"),
                record.get("last_name"),
                record.get("full_name"),
                record.get("phone"),
                record.get("city"),
                record.get("state"),
                record.get("country"),
                record.get("region"),
                record.get("registration_date"),
                record.get("customer_segment", "New"),
            ),
        )


class FactLoader:
    """Loader for fact tables."""

    def __init__(self, batch_id: UUID):
        self.batch_id = batch_id

    def load_fact_sales(self) -> dict[str, int]:
        """Load sales facts from staging."""
        stats = {"processed": 0, "inserted": 0, "skipped": 0}

        # Get staging sales with dimension lookups
        staging_sales = execute_query(
            """
            SELECT
                s.source_sale_id,
                s.source_customer_id + '-' + s.source_system AS customer_id,
                s.source_product_id + '-' + s.source_system AS product_id,
                s.quantity,
                s.unit_price,
                s.total_amount,
                s.sale_date,
                s.payment_method
            FROM staging.sales s
            WHERE s.is_valid = 1
            """
        )

        for record in staging_sales:
            stats["processed"] += 1

            # Get dimension keys
            date_key = calculate_date_key(record.get("sale_date"))
            product_key = self._get_product_key(record["product_id"])
            customer_key = self._get_customer_key(record["customer_id"])

            if not all([date_key, product_key, customer_key]):
                stats["skipped"] += 1
                logger.warning(
                    f"Skipping sale {record['source_sale_id']}: "
                    f"missing dimension key (date={date_key}, "
                    f"product={product_key}, customer={customer_key})"
                )
                continue

            # Get cost for profit calculation
            cost = self._get_product_cost(product_key)
            cost_amount = (
                cost * record["quantity"] if cost and record["quantity"] else None
            )

            # Insert fact
            if self._insert_fact_sale(
                record, date_key, product_key, customer_key, cost_amount
            ):
                stats["inserted"] += 1
            else:
                stats["skipped"] += 1

        logger.info(f"fact_sales load complete: {stats}")
        return stats

    def _get_product_key(self, product_id: str) -> int | None:
        """Get current product dimension key."""
        result = execute_query(
            """
            SELECT product_key FROM dw.dim_product
            WHERE product_id = ? AND is_current = 1
            """,
            (product_id,),
        )
        return result[0]["product_key"] if result else None

    def _get_customer_key(self, customer_id: str) -> int | None:
        """Get current customer dimension key."""
        result = execute_query(
            """
            SELECT customer_key FROM dw.dim_customer
            WHERE customer_id = ? AND is_current = 1
            """,
            (customer_id,),
        )
        return result[0]["customer_key"] if result else None

    def _get_product_cost(self, product_key: int) -> Decimal | None:
        """Get product cost for profit calculation."""
        result = execute_query(
            "SELECT cost FROM dw.dim_product WHERE product_key = ?",
            (product_key,),
        )
        return result[0]["cost"] if result and result[0]["cost"] else None

    def _insert_fact_sale(
        self,
        record: dict[str, Any],
        date_key: int,
        product_key: int,
        customer_key: int,
        cost_amount: Decimal | None,
    ) -> bool:
        """Insert fact sale record. Returns True if successful."""
        try:
            with get_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO dw.fact_sales (
                        date_key, product_key, customer_key, sale_id,
                        payment_method, quantity, unit_price, total_amount,
                        cost_amount, batch_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        date_key,
                        product_key,
                        customer_key,
                        record["source_sale_id"],
                        record.get("payment_method"),
                        record["quantity"],
                        record["unit_price"],
                        record["total_amount"],
                        cost_amount,
                        str(self.batch_id),
                    ),
                )
                return True
        except Exception as e:
            logger.error(f"Failed to insert fact: {e}")
            return False

    def update_customer_segments(self) -> int:
        """Update customer segments based on purchase history."""
        with get_cursor() as cursor:
            # Calculate totals per customer
            cursor.execute(
                """
                UPDATE c
                SET customer_segment = CASE
                    WHEN totals.total_spent >= 1000 OR totals.order_count >= 10 THEN 'Premium'
                    WHEN totals.total_spent >= 500 OR totals.order_count >= 5 THEN 'Regular'
                    WHEN totals.total_spent >= 100 OR totals.order_count >= 2 THEN 'Occasional'
                    ELSE 'New'
                END,
                updated_at = GETDATE()
                FROM dw.dim_customer c
                INNER JOIN (
                    SELECT
                        customer_key,
                        SUM(total_amount) AS total_spent,
                        COUNT(*) AS order_count
                    FROM dw.fact_sales
                    GROUP BY customer_key
                ) totals ON c.customer_key = totals.customer_key
                WHERE c.is_current = 1
                """
            )
            return cursor.rowcount
