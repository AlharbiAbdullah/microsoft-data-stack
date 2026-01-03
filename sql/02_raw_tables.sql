-- =============================================================================
-- Microsoft Data Stack - Raw Layer Tables
-- Landing zone for source data (preserved as-is from sources)
-- =============================================================================

USE datawarehouse;
GO

-- -----------------------------------------------------------------------------
-- Raw Products (from API)
-- -----------------------------------------------------------------------------
IF OBJECT_ID('raw.api_products', 'U') IS NOT NULL
    DROP TABLE raw.api_products;
GO

CREATE TABLE raw.api_products (
    raw_product_id INT IDENTITY(1,1) PRIMARY KEY,
    source_id INT,
    title NVARCHAR(500),
    price NVARCHAR(50),
    description NVARCHAR(MAX),
    category NVARCHAR(255),
    image_url NVARCHAR(1000),
    rating_rate NVARCHAR(50),
    rating_count NVARCHAR(50),
    raw_json NVARCHAR(MAX),
    ingested_at DATETIME2 DEFAULT GETDATE(),
    source_name VARCHAR(100) DEFAULT 'fakestoreapi',
    batch_id UNIQUEIDENTIFIER
);
GO

-- -----------------------------------------------------------------------------
-- Raw Users/Customers (from API)
-- -----------------------------------------------------------------------------
IF OBJECT_ID('raw.api_users', 'U') IS NOT NULL
    DROP TABLE raw.api_users;
GO

CREATE TABLE raw.api_users (
    raw_user_id INT IDENTITY(1,1) PRIMARY KEY,
    source_id INT,
    email NVARCHAR(255),
    username NVARCHAR(100),
    password_hash NVARCHAR(255),
    firstname NVARCHAR(100),
    lastname NVARCHAR(100),
    city NVARCHAR(100),
    street NVARCHAR(255),
    zipcode NVARCHAR(20),
    phone NVARCHAR(50),
    raw_json NVARCHAR(MAX),
    ingested_at DATETIME2 DEFAULT GETDATE(),
    source_name VARCHAR(100) DEFAULT 'fakestoreapi',
    batch_id UNIQUEIDENTIFIER
);
GO

-- -----------------------------------------------------------------------------
-- Raw Carts/Sales (from API)
-- -----------------------------------------------------------------------------
IF OBJECT_ID('raw.api_carts', 'U') IS NOT NULL
    DROP TABLE raw.api_carts;
GO

CREATE TABLE raw.api_carts (
    raw_cart_id INT IDENTITY(1,1) PRIMARY KEY,
    source_id INT,
    user_id INT,
    cart_date NVARCHAR(50),
    products_json NVARCHAR(MAX),
    raw_json NVARCHAR(MAX),
    ingested_at DATETIME2 DEFAULT GETDATE(),
    source_name VARCHAR(100) DEFAULT 'fakestoreapi',
    batch_id UNIQUEIDENTIFIER
);
GO

-- -----------------------------------------------------------------------------
-- Raw Products (from CSV files)
-- -----------------------------------------------------------------------------
IF OBJECT_ID('raw.csv_products', 'U') IS NOT NULL
    DROP TABLE raw.csv_products;
GO

CREATE TABLE raw.csv_products (
    raw_csv_product_id INT IDENTITY(1,1) PRIMARY KEY,
    product_id NVARCHAR(50),
    product_name NVARCHAR(500),
    category NVARCHAR(255),
    price NVARCHAR(50),
    cost NVARCHAR(50),
    stock_quantity NVARCHAR(50),
    supplier NVARCHAR(255),
    raw_line NVARCHAR(MAX),
    file_name VARCHAR(255),
    line_number INT,
    ingested_at DATETIME2 DEFAULT GETDATE(),
    batch_id UNIQUEIDENTIFIER
);
GO

-- -----------------------------------------------------------------------------
-- Raw Customers (from CSV files)
-- -----------------------------------------------------------------------------
IF OBJECT_ID('raw.csv_customers', 'U') IS NOT NULL
    DROP TABLE raw.csv_customers;
GO

CREATE TABLE raw.csv_customers (
    raw_csv_customer_id INT IDENTITY(1,1) PRIMARY KEY,
    customer_id NVARCHAR(50),
    first_name NVARCHAR(100),
    last_name NVARCHAR(100),
    email NVARCHAR(255),
    phone NVARCHAR(50),
    city NVARCHAR(100),
    state NVARCHAR(100),
    country NVARCHAR(100),
    registration_date NVARCHAR(50),
    raw_line NVARCHAR(MAX),
    file_name VARCHAR(255),
    line_number INT,
    ingested_at DATETIME2 DEFAULT GETDATE(),
    batch_id UNIQUEIDENTIFIER
);
GO

-- -----------------------------------------------------------------------------
-- Raw Sales (from CSV files)
-- -----------------------------------------------------------------------------
IF OBJECT_ID('raw.csv_sales', 'U') IS NOT NULL
    DROP TABLE raw.csv_sales;
GO

CREATE TABLE raw.csv_sales (
    raw_csv_sale_id INT IDENTITY(1,1) PRIMARY KEY,
    sale_id NVARCHAR(50),
    customer_id NVARCHAR(50),
    product_id NVARCHAR(50),
    quantity NVARCHAR(50),
    unit_price NVARCHAR(50),
    total_amount NVARCHAR(50),
    sale_date NVARCHAR(50),
    payment_method NVARCHAR(50),
    raw_line NVARCHAR(MAX),
    file_name VARCHAR(255),
    line_number INT,
    ingested_at DATETIME2 DEFAULT GETDATE(),
    batch_id UNIQUEIDENTIFIER
);
GO

-- Create indexes for common queries
CREATE INDEX IX_raw_api_products_batch ON raw.api_products(batch_id);
CREATE INDEX IX_raw_api_users_batch ON raw.api_users(batch_id);
CREATE INDEX IX_raw_api_carts_batch ON raw.api_carts(batch_id);
CREATE INDEX IX_raw_csv_products_batch ON raw.csv_products(batch_id);
CREATE INDEX IX_raw_csv_customers_batch ON raw.csv_customers(batch_id);
CREATE INDEX IX_raw_csv_sales_batch ON raw.csv_sales(batch_id);
GO

PRINT 'Raw layer tables created successfully';
GO
