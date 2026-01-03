"""Data mart builder - creates aggregated analytics views."""

import logging
from uuid import UUID

from src.database import get_cursor

logger = logging.getLogger(__name__)


class MartBuilder:
    """Builder for data mart tables."""

    def __init__(self, batch_id: UUID):
        self.batch_id = batch_id

    def build_all(self) -> dict[str, int]:
        """Build all data marts."""
        results = {}
        results["sales_daily"] = self.build_sales_daily()
        results["product_performance"] = self.build_product_performance()
        results["customer_summary"] = self.build_customer_summary()
        results["category_analysis"] = self.build_category_analysis()

        logger.info(f"All marts built: {results}")
        return results

    def build_sales_daily(self) -> int:
        """Build daily sales summary mart."""
        with get_cursor() as cursor:
            # Clear existing data (full refresh)
            cursor.execute("TRUNCATE TABLE mart.sales_daily")

            # Rebuild from facts
            cursor.execute(
                """
                INSERT INTO mart.sales_daily (
                    date_key, full_date, year, month_num, month_name,
                    day_name, is_weekend, total_orders, total_quantity,
                    total_revenue, total_cost, total_profit, avg_order_value,
                    unique_customers, unique_products
                )
                SELECT
                    d.date_key,
                    d.full_date,
                    d.year,
                    d.month_num,
                    d.month_name,
                    d.day_name,
                    d.is_weekend,
                    COUNT(DISTINCT f.sale_id) AS total_orders,
                    SUM(f.quantity) AS total_quantity,
                    SUM(f.total_amount) AS total_revenue,
                    SUM(f.cost_amount) AS total_cost,
                    SUM(f.total_amount) - ISNULL(SUM(f.cost_amount), 0) AS total_profit,
                    AVG(f.total_amount) AS avg_order_value,
                    COUNT(DISTINCT f.customer_key) AS unique_customers,
                    COUNT(DISTINCT f.product_key) AS unique_products
                FROM dw.fact_sales f
                INNER JOIN dw.dim_date d ON f.date_key = d.date_key
                GROUP BY
                    d.date_key, d.full_date, d.year, d.month_num,
                    d.month_name, d.day_name, d.is_weekend
                """
            )
            rows = cursor.rowcount

        logger.info(f"Built mart.sales_daily: {rows} rows")
        return rows

    def build_product_performance(self) -> int:
        """Build product performance mart."""
        with get_cursor() as cursor:
            cursor.execute("TRUNCATE TABLE mart.product_performance")

            cursor.execute(
                """
                INSERT INTO mart.product_performance (
                    product_key, product_id, title, category, price,
                    total_orders, total_quantity_sold, total_revenue,
                    total_profit, avg_quantity_per_order,
                    first_sale_date, last_sale_date, days_since_last_sale,
                    revenue_rank, quantity_rank
                )
                SELECT
                    p.product_key,
                    p.product_id,
                    p.title,
                    p.category,
                    p.price,
                    COUNT(DISTINCT f.sale_id) AS total_orders,
                    SUM(f.quantity) AS total_quantity_sold,
                    SUM(f.total_amount) AS total_revenue,
                    SUM(f.total_amount) - ISNULL(SUM(f.cost_amount), 0) AS total_profit,
                    AVG(CAST(f.quantity AS DECIMAL(10,2))) AS avg_quantity_per_order,
                    MIN(d.full_date) AS first_sale_date,
                    MAX(d.full_date) AS last_sale_date,
                    DATEDIFF(DAY, MAX(d.full_date), GETDATE()) AS days_since_last_sale,
                    RANK() OVER (ORDER BY SUM(f.total_amount) DESC) AS revenue_rank,
                    RANK() OVER (ORDER BY SUM(f.quantity) DESC) AS quantity_rank
                FROM dw.dim_product p
                INNER JOIN dw.fact_sales f ON p.product_key = f.product_key
                INNER JOIN dw.dim_date d ON f.date_key = d.date_key
                WHERE p.is_current = 1
                GROUP BY
                    p.product_key, p.product_id, p.title, p.category, p.price
                """
            )
            rows = cursor.rowcount

        logger.info(f"Built mart.product_performance: {rows} rows")
        return rows

    def build_customer_summary(self) -> int:
        """Build customer summary mart."""
        with get_cursor() as cursor:
            cursor.execute("TRUNCATE TABLE mart.customer_summary")

            cursor.execute(
                """
                INSERT INTO mart.customer_summary (
                    customer_key, customer_id, full_name, email, city, country,
                    total_orders, total_quantity, total_spent, avg_order_value,
                    first_purchase_date, last_purchase_date,
                    days_since_last_purchase, customer_tenure_days,
                    customer_segment
                )
                SELECT
                    c.customer_key,
                    c.customer_id,
                    c.full_name,
                    c.email,
                    c.city,
                    c.country,
                    COUNT(DISTINCT f.sale_id) AS total_orders,
                    SUM(f.quantity) AS total_quantity,
                    SUM(f.total_amount) AS total_spent,
                    AVG(f.total_amount) AS avg_order_value,
                    MIN(d.full_date) AS first_purchase_date,
                    MAX(d.full_date) AS last_purchase_date,
                    DATEDIFF(DAY, MAX(d.full_date), GETDATE()) AS days_since_last_purchase,
                    DATEDIFF(DAY, MIN(d.full_date), GETDATE()) AS customer_tenure_days,
                    c.customer_segment
                FROM dw.dim_customer c
                INNER JOIN dw.fact_sales f ON c.customer_key = f.customer_key
                INNER JOIN dw.dim_date d ON f.date_key = d.date_key
                WHERE c.is_current = 1
                GROUP BY
                    c.customer_key, c.customer_id, c.full_name, c.email,
                    c.city, c.country, c.customer_segment
                """
            )
            rows = cursor.rowcount

        logger.info(f"Built mart.customer_summary: {rows} rows")
        return rows

    def build_category_analysis(self) -> int:
        """Build category analysis mart."""
        with get_cursor() as cursor:
            cursor.execute("TRUNCATE TABLE mart.category_analysis")

            cursor.execute(
                """
                INSERT INTO mart.category_analysis (
                    category, year, month_num, product_count, total_orders,
                    total_quantity, total_revenue, total_profit,
                    avg_product_price, unique_customers
                )
                SELECT
                    p.category,
                    d.year,
                    d.month_num,
                    COUNT(DISTINCT p.product_key) AS product_count,
                    COUNT(DISTINCT f.sale_id) AS total_orders,
                    SUM(f.quantity) AS total_quantity,
                    SUM(f.total_amount) AS total_revenue,
                    SUM(f.total_amount) - ISNULL(SUM(f.cost_amount), 0) AS total_profit,
                    AVG(p.price) AS avg_product_price,
                    COUNT(DISTINCT f.customer_key) AS unique_customers
                FROM dw.dim_product p
                INNER JOIN dw.fact_sales f ON p.product_key = f.product_key
                INNER JOIN dw.dim_date d ON f.date_key = d.date_key
                WHERE p.is_current = 1
                GROUP BY p.category, d.year, d.month_num
                """
            )
            rows = cursor.rowcount

        logger.info(f"Built mart.category_analysis: {rows} rows")
        return rows
