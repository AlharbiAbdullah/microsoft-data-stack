-- =============================================================================
-- Microsoft Data Stack - Data Warehouse Layer (Star Schema)
-- Dimensional model optimized for analytics
-- =============================================================================

USE datawarehouse;
GO

-- -----------------------------------------------------------------------------
-- Dimension: Date
-- -----------------------------------------------------------------------------
IF OBJECT_ID('dw.dim_date', 'U') IS NOT NULL
    DROP TABLE dw.dim_date;
GO

CREATE TABLE dw.dim_date (
    date_key INT PRIMARY KEY,  -- YYYYMMDD format
    full_date DATE NOT NULL,
    day_of_week TINYINT NOT NULL,
    day_name VARCHAR(10) NOT NULL,
    day_of_month TINYINT NOT NULL,
    day_of_year SMALLINT NOT NULL,
    week_of_year TINYINT NOT NULL,
    month_num TINYINT NOT NULL,
    month_name VARCHAR(10) NOT NULL,
    month_short VARCHAR(3) NOT NULL,
    quarter TINYINT NOT NULL,
    quarter_name VARCHAR(2) NOT NULL,
    year INT NOT NULL,
    is_weekend BIT NOT NULL,
    is_holiday BIT DEFAULT 0,
    fiscal_year INT,
    fiscal_quarter TINYINT
);
GO

-- Populate date dimension (2020-2030)
;WITH DateRange AS (
    SELECT CAST('2020-01-01' AS DATE) AS dt
    UNION ALL
    SELECT DATEADD(DAY, 1, dt)
    FROM DateRange
    WHERE dt < '2030-12-31'
)
INSERT INTO dw.dim_date (
    date_key, full_date, day_of_week, day_name, day_of_month, day_of_year,
    week_of_year, month_num, month_name, month_short, quarter, quarter_name,
    year, is_weekend, fiscal_year, fiscal_quarter
)
SELECT
    CAST(FORMAT(dt, 'yyyyMMdd') AS INT) AS date_key,
    dt AS full_date,
    DATEPART(WEEKDAY, dt) AS day_of_week,
    DATENAME(WEEKDAY, dt) AS day_name,
    DAY(dt) AS day_of_month,
    DATEPART(DAYOFYEAR, dt) AS day_of_year,
    DATEPART(WEEK, dt) AS week_of_year,
    MONTH(dt) AS month_num,
    DATENAME(MONTH, dt) AS month_name,
    LEFT(DATENAME(MONTH, dt), 3) AS month_short,
    DATEPART(QUARTER, dt) AS quarter,
    'Q' + CAST(DATEPART(QUARTER, dt) AS VARCHAR) AS quarter_name,
    YEAR(dt) AS year,
    CASE WHEN DATEPART(WEEKDAY, dt) IN (1, 7) THEN 1 ELSE 0 END AS is_weekend,
    CASE WHEN MONTH(dt) >= 7 THEN YEAR(dt) + 1 ELSE YEAR(dt) END AS fiscal_year,
    CASE
        WHEN MONTH(dt) IN (7, 8, 9) THEN 1
        WHEN MONTH(dt) IN (10, 11, 12) THEN 2
        WHEN MONTH(dt) IN (1, 2, 3) THEN 3
        ELSE 4
    END AS fiscal_quarter
FROM DateRange
OPTION (MAXRECURSION 5000);
GO

-- -----------------------------------------------------------------------------
-- Dimension: Product
-- -----------------------------------------------------------------------------
IF OBJECT_ID('dw.dim_product', 'U') IS NOT NULL
    DROP TABLE dw.dim_product;
GO

CREATE TABLE dw.dim_product (
    product_key INT IDENTITY(1,1) PRIMARY KEY,
    product_id VARCHAR(50) NOT NULL,
    title NVARCHAR(500) NOT NULL,
    category NVARCHAR(255),
    price DECIMAL(10, 2) NOT NULL,
    cost DECIMAL(10, 2),
    profit_margin AS (CASE WHEN cost > 0 THEN (price - cost) / price * 100 ELSE NULL END),
    description NVARCHAR(MAX),
    image_url NVARCHAR(1000),
    rating_rate DECIMAL(3, 2),
    rating_count INT,
    stock_quantity INT,
    supplier NVARCHAR(255),
    -- SCD Type 2 fields
    effective_from DATE NOT NULL DEFAULT CAST(GETDATE() AS DATE),
    effective_to DATE DEFAULT '9999-12-31',
    is_current BIT DEFAULT 1,
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);
GO

CREATE INDEX IX_dim_product_id ON dw.dim_product(product_id);
CREATE INDEX IX_dim_product_current ON dw.dim_product(is_current);
GO

-- -----------------------------------------------------------------------------
-- Dimension: Customer
-- -----------------------------------------------------------------------------
IF OBJECT_ID('dw.dim_customer', 'U') IS NOT NULL
    DROP TABLE dw.dim_customer;
GO

CREATE TABLE dw.dim_customer (
    customer_key INT IDENTITY(1,1) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    email NVARCHAR(255),
    first_name NVARCHAR(100),
    last_name NVARCHAR(100),
    full_name NVARCHAR(200),
    phone NVARCHAR(50),
    city NVARCHAR(100),
    state NVARCHAR(100),
    country NVARCHAR(100),
    region NVARCHAR(100),
    registration_date DATE,
    customer_segment VARCHAR(50),
    -- SCD Type 2 fields
    effective_from DATE NOT NULL DEFAULT CAST(GETDATE() AS DATE),
    effective_to DATE DEFAULT '9999-12-31',
    is_current BIT DEFAULT 1,
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);
GO

CREATE INDEX IX_dim_customer_id ON dw.dim_customer(customer_id);
CREATE INDEX IX_dim_customer_current ON dw.dim_customer(is_current);
GO

-- -----------------------------------------------------------------------------
-- Fact: Sales
-- -----------------------------------------------------------------------------
IF OBJECT_ID('dw.fact_sales', 'U') IS NOT NULL
    DROP TABLE dw.fact_sales;
GO

CREATE TABLE dw.fact_sales (
    sale_key BIGINT IDENTITY(1,1) PRIMARY KEY,
    -- Dimension keys
    date_key INT NOT NULL,
    product_key INT NOT NULL,
    customer_key INT NOT NULL,
    -- Degenerate dimensions
    sale_id VARCHAR(50) NOT NULL,
    payment_method NVARCHAR(50),
    -- Measures
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_amount DECIMAL(12, 2) NOT NULL,
    cost_amount DECIMAL(12, 2),
    profit_amount AS (total_amount - ISNULL(cost_amount, 0)),
    -- Audit
    created_at DATETIME2 DEFAULT GETDATE(),
    batch_id UNIQUEIDENTIFIER,
    -- Foreign keys
    CONSTRAINT FK_fact_sales_date FOREIGN KEY (date_key) REFERENCES dw.dim_date(date_key),
    CONSTRAINT FK_fact_sales_product FOREIGN KEY (product_key) REFERENCES dw.dim_product(product_key),
    CONSTRAINT FK_fact_sales_customer FOREIGN KEY (customer_key) REFERENCES dw.dim_customer(customer_key)
);
GO

-- Create indexes for common query patterns
CREATE INDEX IX_fact_sales_date ON dw.fact_sales(date_key);
CREATE INDEX IX_fact_sales_product ON dw.fact_sales(product_key);
CREATE INDEX IX_fact_sales_customer ON dw.fact_sales(customer_key);
CREATE INDEX IX_fact_sales_date_product ON dw.fact_sales(date_key, product_key);
GO

PRINT 'Data warehouse layer tables created successfully';
GO
