-- =============================================================================
-- Microsoft Data Stack - Staging Layer Tables
-- Cleaned, validated, and type-enforced data
-- =============================================================================

USE datawarehouse;
GO

-- -----------------------------------------------------------------------------
-- Staging Products (merged from API + CSV)
-- -----------------------------------------------------------------------------
IF OBJECT_ID('staging.products', 'U') IS NOT NULL
    DROP TABLE staging.products;
GO

CREATE TABLE staging.products (
    staging_product_id INT IDENTITY(1,1) PRIMARY KEY,
    source_product_id VARCHAR(50) NOT NULL,
    source_system VARCHAR(50) NOT NULL,  -- 'api' or 'csv'
    title NVARCHAR(500) NOT NULL,
    category NVARCHAR(255),
    price DECIMAL(10, 2) NOT NULL,
    cost DECIMAL(10, 2),
    description NVARCHAR(MAX),
    image_url NVARCHAR(1000),
    rating_rate DECIMAL(3, 2),
    rating_count INT,
    stock_quantity INT,
    supplier NVARCHAR(255),
    is_valid BIT DEFAULT 1,
    validation_errors NVARCHAR(MAX),
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE(),
    batch_id UNIQUEIDENTIFIER,
    CONSTRAINT UQ_staging_products_source UNIQUE (source_product_id, source_system)
);
GO

-- -----------------------------------------------------------------------------
-- Staging Customers (merged from API + CSV)
-- -----------------------------------------------------------------------------
IF OBJECT_ID('staging.customers', 'U') IS NOT NULL
    DROP TABLE staging.customers;
GO

CREATE TABLE staging.customers (
    staging_customer_id INT IDENTITY(1,1) PRIMARY KEY,
    source_customer_id VARCHAR(50) NOT NULL,
    source_system VARCHAR(50) NOT NULL,
    email NVARCHAR(255),
    first_name NVARCHAR(100),
    last_name NVARCHAR(100),
    full_name NVARCHAR(200),
    phone NVARCHAR(50),
    city NVARCHAR(100),
    state NVARCHAR(100),
    country NVARCHAR(100),
    registration_date DATE,
    is_valid BIT DEFAULT 1,
    validation_errors NVARCHAR(MAX),
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE(),
    batch_id UNIQUEIDENTIFIER,
    CONSTRAINT UQ_staging_customers_source UNIQUE (source_customer_id, source_system)
);
GO

-- -----------------------------------------------------------------------------
-- Staging Sales (merged from API carts + CSV sales)
-- -----------------------------------------------------------------------------
IF OBJECT_ID('staging.sales', 'U') IS NOT NULL
    DROP TABLE staging.sales;
GO

CREATE TABLE staging.sales (
    staging_sale_id INT IDENTITY(1,1) PRIMARY KEY,
    source_sale_id VARCHAR(50) NOT NULL,
    source_system VARCHAR(50) NOT NULL,
    source_customer_id VARCHAR(50),
    source_product_id VARCHAR(50),
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_amount DECIMAL(12, 2) NOT NULL,
    sale_date DATE NOT NULL,
    payment_method NVARCHAR(50),
    is_valid BIT DEFAULT 1,
    validation_errors NVARCHAR(MAX),
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE(),
    batch_id UNIQUEIDENTIFIER,
    CONSTRAINT UQ_staging_sales_source UNIQUE (source_sale_id, source_system)
);
GO

-- Create indexes for transformation queries
CREATE INDEX IX_staging_products_source ON staging.products(source_product_id, source_system);
CREATE INDEX IX_staging_products_valid ON staging.products(is_valid);
CREATE INDEX IX_staging_customers_source ON staging.customers(source_customer_id, source_system);
CREATE INDEX IX_staging_customers_valid ON staging.customers(is_valid);
CREATE INDEX IX_staging_sales_source ON staging.sales(source_customer_id, source_product_id);
CREATE INDEX IX_staging_sales_date ON staging.sales(sale_date);
CREATE INDEX IX_staging_sales_valid ON staging.sales(is_valid);
GO

PRINT 'Staging layer tables created successfully';
GO
