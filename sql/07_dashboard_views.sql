-- =============================================================================
-- Microsoft Data Stack - Dashboard Views
-- Pre-built views for Superset dashboards
-- =============================================================================

USE datawarehouse;
GO

-- -----------------------------------------------------------------------------
-- View: Sales KPI Summary
-- Used for: Top-level KPI cards
-- -----------------------------------------------------------------------------
IF OBJECT_ID('dw.vw_sales_kpi_summary', 'V') IS NOT NULL
    DROP VIEW dw.vw_sales_kpi_summary;
GO

CREATE VIEW dw.vw_sales_kpi_summary AS
SELECT
    COUNT(DISTINCT sale_key) AS total_orders,
    SUM(quantity) AS total_units_sold,
    SUM(total_amount) AS total_revenue,
    SUM(total_amount) - ISNULL(SUM(cost_amount), 0) AS total_profit,
    AVG(total_amount) AS avg_order_value,
    COUNT(DISTINCT customer_key) AS unique_customers,
    COUNT(DISTINCT product_key) AS unique_products
FROM dw.fact_sales;
GO

-- -----------------------------------------------------------------------------
-- View: Daily Sales Trend
-- Used for: Time series line chart
-- -----------------------------------------------------------------------------
IF OBJECT_ID('dw.vw_daily_sales_trend', 'V') IS NOT NULL
    DROP VIEW dw.vw_daily_sales_trend;
GO

CREATE VIEW dw.vw_daily_sales_trend AS
SELECT
    d.full_date,
    d.day_name,
    d.month_name,
    d.year,
    COUNT(DISTINCT f.sale_key) AS orders,
    SUM(f.quantity) AS units_sold,
    SUM(f.total_amount) AS revenue,
    SUM(f.total_amount) - ISNULL(SUM(f.cost_amount), 0) AS profit
FROM dw.fact_sales f
INNER JOIN dw.dim_date d ON f.date_key = d.date_key
GROUP BY d.full_date, d.day_name, d.month_name, d.year;
GO

-- -----------------------------------------------------------------------------
-- View: Sales by Category
-- Used for: Pie/donut chart, bar chart
-- -----------------------------------------------------------------------------
IF OBJECT_ID('dw.vw_sales_by_category', 'V') IS NOT NULL
    DROP VIEW dw.vw_sales_by_category;
GO

CREATE VIEW dw.vw_sales_by_category AS
SELECT
    p.category,
    COUNT(DISTINCT f.sale_key) AS orders,
    SUM(f.quantity) AS units_sold,
    SUM(f.total_amount) AS revenue,
    SUM(f.total_amount) - ISNULL(SUM(f.cost_amount), 0) AS profit,
    AVG(f.total_amount) AS avg_order_value
FROM dw.fact_sales f
INNER JOIN dw.dim_product p ON f.product_key = p.product_key
WHERE p.is_current = 1
GROUP BY p.category;
GO

-- -----------------------------------------------------------------------------
-- View: Top Products by Revenue
-- Used for: Ranked bar chart, table
-- -----------------------------------------------------------------------------
IF OBJECT_ID('dw.vw_top_products', 'V') IS NOT NULL
    DROP VIEW dw.vw_top_products;
GO

CREATE VIEW dw.vw_top_products AS
SELECT
    p.product_id,
    p.title AS product_name,
    p.category,
    p.price,
    COUNT(DISTINCT f.sale_key) AS orders,
    SUM(f.quantity) AS units_sold,
    SUM(f.total_amount) AS revenue,
    RANK() OVER (ORDER BY SUM(f.total_amount) DESC) AS revenue_rank
FROM dw.fact_sales f
INNER JOIN dw.dim_product p ON f.product_key = p.product_key
WHERE p.is_current = 1
GROUP BY p.product_id, p.title, p.category, p.price;
GO

-- -----------------------------------------------------------------------------
-- View: Customer Segments
-- Used for: Pie chart, segment analysis
-- -----------------------------------------------------------------------------
IF OBJECT_ID('dw.vw_customer_segments', 'V') IS NOT NULL
    DROP VIEW dw.vw_customer_segments;
GO

CREATE VIEW dw.vw_customer_segments AS
SELECT
    c.customer_segment,
    COUNT(DISTINCT c.customer_key) AS customer_count,
    COUNT(DISTINCT f.sale_key) AS total_orders,
    SUM(f.total_amount) AS total_revenue,
    AVG(f.total_amount) AS avg_order_value
FROM dw.dim_customer c
LEFT JOIN dw.fact_sales f ON c.customer_key = f.customer_key
WHERE c.is_current = 1
GROUP BY c.customer_segment;
GO

-- -----------------------------------------------------------------------------
-- View: Sales by Region
-- Used for: Geographic visualization
-- -----------------------------------------------------------------------------
IF OBJECT_ID('dw.vw_sales_by_region', 'V') IS NOT NULL
    DROP VIEW dw.vw_sales_by_region;
GO

CREATE VIEW dw.vw_sales_by_region AS
SELECT
    ISNULL(c.region, 'Unknown') AS region,
    ISNULL(c.country, 'Unknown') AS country,
    COUNT(DISTINCT c.customer_key) AS customers,
    COUNT(DISTINCT f.sale_key) AS orders,
    SUM(f.total_amount) AS revenue
FROM dw.dim_customer c
LEFT JOIN dw.fact_sales f ON c.customer_key = f.customer_key
WHERE c.is_current = 1
GROUP BY c.region, c.country;
GO

-- -----------------------------------------------------------------------------
-- View: Monthly Sales Comparison
-- Used for: Month-over-month comparison
-- -----------------------------------------------------------------------------
IF OBJECT_ID('dw.vw_monthly_sales', 'V') IS NOT NULL
    DROP VIEW dw.vw_monthly_sales;
GO

CREATE VIEW dw.vw_monthly_sales AS
SELECT
    d.year,
    d.month_num,
    d.month_name,
    COUNT(DISTINCT f.sale_key) AS orders,
    SUM(f.total_amount) AS revenue,
    SUM(f.total_amount) - ISNULL(SUM(f.cost_amount), 0) AS profit,
    LAG(SUM(f.total_amount)) OVER (ORDER BY d.year, d.month_num) AS prev_month_revenue
FROM dw.fact_sales f
INNER JOIN dw.dim_date d ON f.date_key = d.date_key
GROUP BY d.year, d.month_num, d.month_name;
GO

-- =============================================================================
-- Data Quality Dashboard Views
-- =============================================================================

-- -----------------------------------------------------------------------------
-- View: Quality Summary
-- Used for: Quality KPI cards
-- -----------------------------------------------------------------------------
IF OBJECT_ID('quality.vw_quality_summary', 'V') IS NOT NULL
    DROP VIEW quality.vw_quality_summary;
GO

CREATE VIEW quality.vw_quality_summary AS
SELECT
    COUNT(*) AS total_pipeline_runs,
    SUM(records_received) AS total_records_received,
    SUM(records_stored) AS total_records_stored,
    SUM(records_rejected) AS total_records_rejected,
    CAST(
        CASE
            WHEN SUM(records_received) = 0 THEN 100.0
            ELSE (CAST(SUM(records_stored) AS FLOAT) / SUM(records_received)) * 100
        END
    AS DECIMAL(5,2)) AS overall_quality_score,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS successful_runs,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_runs
FROM quality.ingestion_log;
GO

-- -----------------------------------------------------------------------------
-- View: Quality by Source
-- Used for: Source comparison chart
-- -----------------------------------------------------------------------------
IF OBJECT_ID('quality.vw_quality_by_source', 'V') IS NOT NULL
    DROP VIEW quality.vw_quality_by_source;
GO

CREATE VIEW quality.vw_quality_by_source AS
SELECT
    source_name,
    source_type,
    COUNT(*) AS run_count,
    SUM(records_received) AS total_received,
    SUM(records_stored) AS total_stored,
    SUM(records_rejected) AS total_rejected,
    AVG(quality_score) AS avg_quality_score,
    MAX(created_at) AS last_run
FROM quality.ingestion_log
GROUP BY source_name, source_type;
GO

-- -----------------------------------------------------------------------------
-- View: Quality Trend
-- Used for: Quality over time line chart
-- -----------------------------------------------------------------------------
IF OBJECT_ID('quality.vw_quality_trend', 'V') IS NOT NULL
    DROP VIEW quality.vw_quality_trend;
GO

CREATE VIEW quality.vw_quality_trend AS
SELECT
    CAST(created_at AS DATE) AS run_date,
    COUNT(*) AS pipeline_runs,
    SUM(records_received) AS records_received,
    SUM(records_stored) AS records_stored,
    SUM(records_rejected) AS records_rejected,
    AVG(quality_score) AS avg_quality_score
FROM quality.ingestion_log
GROUP BY CAST(created_at AS DATE);
GO

-- -----------------------------------------------------------------------------
-- View: Recent Pipeline Runs
-- Used for: Pipeline status table
-- -----------------------------------------------------------------------------
IF OBJECT_ID('quality.vw_recent_runs', 'V') IS NOT NULL
    DROP VIEW quality.vw_recent_runs;
GO

CREATE VIEW quality.vw_recent_runs AS
SELECT TOP 100
    batch_id,
    pipeline_name,
    source_name,
    source_type,
    records_received,
    records_stored,
    records_rejected,
    quality_score,
    status,
    duration_seconds,
    created_at
FROM quality.ingestion_log
ORDER BY created_at DESC;
GO

-- -----------------------------------------------------------------------------
-- View: Rejection Analysis
-- Used for: Error breakdown chart
-- -----------------------------------------------------------------------------
IF OBJECT_ID('quality.vw_rejection_analysis', 'V') IS NOT NULL
    DROP VIEW quality.vw_rejection_analysis;
GO

CREATE VIEW quality.vw_rejection_analysis AS
SELECT
    source_name,
    rejection_reason,
    SUM(rejection_count) AS total_rejections,
    COUNT(DISTINCT batch_id) AS affected_batches
FROM quality.rejection_details
GROUP BY source_name, rejection_reason;
GO

PRINT 'Dashboard views created successfully';
GO
