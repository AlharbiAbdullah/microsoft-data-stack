-- =============================================================================
-- Microsoft Data Stack - Data Mart Layer
-- Pre-aggregated tables for specific analytical use cases
-- =============================================================================

USE datawarehouse;
GO

-- -----------------------------------------------------------------------------
-- Mart: Daily Sales Summary
-- -----------------------------------------------------------------------------
IF OBJECT_ID('mart.sales_daily', 'U') IS NOT NULL
    DROP TABLE mart.sales_daily;
GO

CREATE TABLE mart.sales_daily (
    sales_daily_id INT IDENTITY(1,1) PRIMARY KEY,
    date_key INT NOT NULL,
    full_date DATE NOT NULL,
    year INT NOT NULL,
    month_num TINYINT NOT NULL,
    month_name VARCHAR(10) NOT NULL,
    day_name VARCHAR(10) NOT NULL,
    is_weekend BIT NOT NULL,
    -- Measures
    total_orders INT NOT NULL,
    total_quantity INT NOT NULL,
    total_revenue DECIMAL(15, 2) NOT NULL,
    total_cost DECIMAL(15, 2),
    total_profit DECIMAL(15, 2),
    avg_order_value DECIMAL(10, 2) NOT NULL,
    unique_customers INT NOT NULL,
    unique_products INT NOT NULL,
    -- Audit
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);
GO

CREATE INDEX IX_mart_sales_daily_date ON mart.sales_daily(full_date);
CREATE INDEX IX_mart_sales_daily_year_month ON mart.sales_daily(year, month_num);
GO

-- -----------------------------------------------------------------------------
-- Mart: Product Performance
-- -----------------------------------------------------------------------------
IF OBJECT_ID('mart.product_performance', 'U') IS NOT NULL
    DROP TABLE mart.product_performance;
GO

CREATE TABLE mart.product_performance (
    product_performance_id INT IDENTITY(1,1) PRIMARY KEY,
    product_key INT NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    title NVARCHAR(500) NOT NULL,
    category NVARCHAR(255),
    price DECIMAL(10, 2) NOT NULL,
    -- Lifetime metrics
    total_orders INT NOT NULL,
    total_quantity_sold INT NOT NULL,
    total_revenue DECIMAL(15, 2) NOT NULL,
    total_profit DECIMAL(15, 2),
    avg_quantity_per_order DECIMAL(8, 2),
    -- Time-based metrics
    first_sale_date DATE,
    last_sale_date DATE,
    days_since_last_sale INT,
    -- Ranking
    revenue_rank INT,
    quantity_rank INT,
    -- Audit
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);
GO

CREATE INDEX IX_mart_product_perf_category ON mart.product_performance(category);
CREATE INDEX IX_mart_product_perf_revenue ON mart.product_performance(total_revenue DESC);
GO

-- -----------------------------------------------------------------------------
-- Mart: Customer Summary
-- -----------------------------------------------------------------------------
IF OBJECT_ID('mart.customer_summary', 'U') IS NOT NULL
    DROP TABLE mart.customer_summary;
GO

CREATE TABLE mart.customer_summary (
    customer_summary_id INT IDENTITY(1,1) PRIMARY KEY,
    customer_key INT NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    full_name NVARCHAR(200),
    email NVARCHAR(255),
    city NVARCHAR(100),
    country NVARCHAR(100),
    -- Lifetime metrics
    total_orders INT NOT NULL,
    total_quantity INT NOT NULL,
    total_spent DECIMAL(15, 2) NOT NULL,
    avg_order_value DECIMAL(10, 2),
    -- Time-based metrics
    first_purchase_date DATE,
    last_purchase_date DATE,
    days_since_last_purchase INT,
    customer_tenure_days INT,
    -- Segmentation
    customer_segment VARCHAR(50),
    rfm_score VARCHAR(10),
    -- Audit
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);
GO

CREATE INDEX IX_mart_customer_segment ON mart.customer_summary(customer_segment);
CREATE INDEX IX_mart_customer_spent ON mart.customer_summary(total_spent DESC);
GO

-- -----------------------------------------------------------------------------
-- Mart: Category Analysis
-- -----------------------------------------------------------------------------
IF OBJECT_ID('mart.category_analysis', 'U') IS NOT NULL
    DROP TABLE mart.category_analysis;
GO

CREATE TABLE mart.category_analysis (
    category_analysis_id INT IDENTITY(1,1) PRIMARY KEY,
    category NVARCHAR(255) NOT NULL,
    year INT NOT NULL,
    month_num TINYINT NOT NULL,
    -- Measures
    product_count INT NOT NULL,
    total_orders INT NOT NULL,
    total_quantity INT NOT NULL,
    total_revenue DECIMAL(15, 2) NOT NULL,
    total_profit DECIMAL(15, 2),
    avg_product_price DECIMAL(10, 2),
    unique_customers INT NOT NULL,
    -- Growth metrics
    revenue_mom_change DECIMAL(10, 2),
    revenue_yoy_change DECIMAL(10, 2),
    -- Audit
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);
GO

CREATE INDEX IX_mart_category_year_month ON mart.category_analysis(year, month_num);
CREATE INDEX IX_mart_category_revenue ON mart.category_analysis(total_revenue DESC);
GO

PRINT 'Data mart layer tables created successfully';
GO
