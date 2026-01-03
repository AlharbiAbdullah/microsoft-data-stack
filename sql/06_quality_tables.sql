-- =============================================================================
-- Microsoft Data Stack - Quality Layer
-- Data quality tracking, metrics, and audit logging
-- =============================================================================

USE datawarehouse;
GO

-- -----------------------------------------------------------------------------
-- Quality: Ingestion Log
-- Tracks received vs stored metrics for each pipeline run
-- -----------------------------------------------------------------------------
IF OBJECT_ID('quality.ingestion_log', 'U') IS NOT NULL
    DROP TABLE quality.ingestion_log;
GO

CREATE TABLE quality.ingestion_log (
    ingestion_log_id INT IDENTITY(1,1) PRIMARY KEY,
    batch_id UNIQUEIDENTIFIER NOT NULL,
    pipeline_name VARCHAR(100) NOT NULL,
    source_name VARCHAR(100) NOT NULL,
    source_type VARCHAR(50) NOT NULL,  -- 'api', 'csv', 'database'
    -- What we received
    records_received INT NOT NULL,
    bytes_received BIGINT,
    -- What we stored
    records_stored INT NOT NULL,
    records_rejected INT NOT NULL DEFAULT 0,
    -- Quality metrics
    quality_score AS (
        CAST(
            CASE
                WHEN records_received = 0 THEN 100.00
                ELSE (CAST(records_stored AS DECIMAL(12,2)) / records_received) * 100
            END
        AS DECIMAL(5,2))
    ),
    -- Timing
    extraction_started_at DATETIME2 NOT NULL,
    extraction_completed_at DATETIME2,
    load_started_at DATETIME2,
    load_completed_at DATETIME2,
    duration_seconds AS DATEDIFF(SECOND, extraction_started_at, load_completed_at),
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'running',  -- running, success, failed, partial
    error_message NVARCHAR(MAX),
    -- Audit
    created_at DATETIME2 DEFAULT GETDATE()
);
GO

CREATE INDEX IX_quality_ingestion_batch ON quality.ingestion_log(batch_id);
CREATE INDEX IX_quality_ingestion_pipeline ON quality.ingestion_log(pipeline_name);
CREATE INDEX IX_quality_ingestion_source ON quality.ingestion_log(source_name);
CREATE INDEX IX_quality_ingestion_date ON quality.ingestion_log(created_at);
GO

-- -----------------------------------------------------------------------------
-- Quality: Rejection Details
-- Detailed breakdown of rejected records
-- -----------------------------------------------------------------------------
IF OBJECT_ID('quality.rejection_details', 'U') IS NOT NULL
    DROP TABLE quality.rejection_details;
GO

CREATE TABLE quality.rejection_details (
    rejection_detail_id INT IDENTITY(1,1) PRIMARY KEY,
    batch_id UNIQUEIDENTIFIER NOT NULL,
    source_name VARCHAR(100) NOT NULL,
    rejection_reason VARCHAR(100) NOT NULL,
    rejection_count INT NOT NULL,
    sample_values NVARCHAR(MAX),  -- JSON array of sample rejected values
    created_at DATETIME2 DEFAULT GETDATE()
);
GO

CREATE INDEX IX_quality_rejection_batch ON quality.rejection_details(batch_id);
GO

-- -----------------------------------------------------------------------------
-- Quality: Transformation Log
-- Tracks transformation pipeline metrics
-- -----------------------------------------------------------------------------
IF OBJECT_ID('quality.transformation_log', 'U') IS NOT NULL
    DROP TABLE quality.transformation_log;
GO

CREATE TABLE quality.transformation_log (
    transformation_log_id INT IDENTITY(1,1) PRIMARY KEY,
    batch_id UNIQUEIDENTIFIER NOT NULL,
    pipeline_name VARCHAR(100) NOT NULL,
    step_name VARCHAR(100) NOT NULL,
    source_layer VARCHAR(50) NOT NULL,  -- 'raw', 'staging'
    target_layer VARCHAR(50) NOT NULL,  -- 'staging', 'dw', 'mart'
    target_table VARCHAR(100) NOT NULL,
    -- Metrics
    records_input INT NOT NULL,
    records_output INT NOT NULL,
    records_inserted INT NOT NULL DEFAULT 0,
    records_updated INT NOT NULL DEFAULT 0,
    records_deleted INT NOT NULL DEFAULT 0,
    records_rejected INT NOT NULL DEFAULT 0,
    -- Timing
    started_at DATETIME2 NOT NULL,
    completed_at DATETIME2,
    duration_seconds AS DATEDIFF(SECOND, started_at, completed_at),
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'running',
    error_message NVARCHAR(MAX),
    -- Audit
    created_at DATETIME2 DEFAULT GETDATE()
);
GO

CREATE INDEX IX_quality_transform_batch ON quality.transformation_log(batch_id);
CREATE INDEX IX_quality_transform_pipeline ON quality.transformation_log(pipeline_name);
GO

-- -----------------------------------------------------------------------------
-- Quality: Data Quality Rules
-- Defines validation rules and their results
-- -----------------------------------------------------------------------------
IF OBJECT_ID('quality.data_quality_rules', 'U') IS NOT NULL
    DROP TABLE quality.data_quality_rules;
GO

CREATE TABLE quality.data_quality_rules (
    rule_id INT IDENTITY(1,1) PRIMARY KEY,
    rule_name VARCHAR(100) NOT NULL,
    rule_description NVARCHAR(500),
    target_table VARCHAR(100) NOT NULL,
    target_column VARCHAR(100),
    rule_type VARCHAR(50) NOT NULL,  -- 'not_null', 'unique', 'range', 'format', 'referential'
    rule_expression NVARCHAR(MAX),
    severity VARCHAR(20) NOT NULL DEFAULT 'warning',  -- 'error', 'warning', 'info'
    is_active BIT DEFAULT 1,
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE()
);
GO

-- -----------------------------------------------------------------------------
-- Quality: Rule Execution Results
-- Stores results of quality rule checks
-- -----------------------------------------------------------------------------
IF OBJECT_ID('quality.rule_execution_results', 'U') IS NOT NULL
    DROP TABLE quality.rule_execution_results;
GO

CREATE TABLE quality.rule_execution_results (
    result_id INT IDENTITY(1,1) PRIMARY KEY,
    batch_id UNIQUEIDENTIFIER NOT NULL,
    rule_id INT NOT NULL,
    records_checked INT NOT NULL,
    records_passed INT NOT NULL,
    records_failed INT NOT NULL,
    pass_rate AS (
        CAST(
            CASE
                WHEN records_checked = 0 THEN 100.00
                ELSE (CAST(records_passed AS DECIMAL(12,2)) / records_checked) * 100
            END
        AS DECIMAL(5,2))
    ),
    sample_failures NVARCHAR(MAX),  -- JSON array of sample failures
    executed_at DATETIME2 DEFAULT GETDATE(),
    CONSTRAINT FK_rule_results_rule FOREIGN KEY (rule_id) REFERENCES quality.data_quality_rules(rule_id)
);
GO

CREATE INDEX IX_quality_results_batch ON quality.rule_execution_results(batch_id);
CREATE INDEX IX_quality_results_rule ON quality.rule_execution_results(rule_id);
GO

-- -----------------------------------------------------------------------------
-- Quality: Daily Summary
-- Aggregated daily quality metrics for dashboards
-- -----------------------------------------------------------------------------
IF OBJECT_ID('quality.daily_summary', 'U') IS NOT NULL
    DROP TABLE quality.daily_summary;
GO

CREATE TABLE quality.daily_summary (
    daily_summary_id INT IDENTITY(1,1) PRIMARY KEY,
    summary_date DATE NOT NULL,
    -- Ingestion metrics
    total_pipelines_run INT NOT NULL DEFAULT 0,
    successful_pipelines INT NOT NULL DEFAULT 0,
    failed_pipelines INT NOT NULL DEFAULT 0,
    total_records_received INT NOT NULL DEFAULT 0,
    total_records_stored INT NOT NULL DEFAULT 0,
    total_records_rejected INT NOT NULL DEFAULT 0,
    overall_quality_score DECIMAL(5, 2),
    -- Transformation metrics
    total_transforms_run INT NOT NULL DEFAULT 0,
    successful_transforms INT NOT NULL DEFAULT 0,
    -- Quality rule metrics
    total_rules_executed INT NOT NULL DEFAULT 0,
    rules_passed INT NOT NULL DEFAULT 0,
    rules_failed INT NOT NULL DEFAULT 0,
    -- Audit
    created_at DATETIME2 DEFAULT GETDATE(),
    updated_at DATETIME2 DEFAULT GETDATE(),
    CONSTRAINT UQ_quality_daily_date UNIQUE (summary_date)
);
GO

CREATE INDEX IX_quality_daily_date ON quality.daily_summary(summary_date);
GO

-- -----------------------------------------------------------------------------
-- Insert default quality rules
-- -----------------------------------------------------------------------------
INSERT INTO quality.data_quality_rules (rule_name, rule_description, target_table, target_column, rule_type, severity)
VALUES
    ('product_price_positive', 'Product price must be greater than 0', 'staging.products', 'price', 'range', 'error'),
    ('product_title_not_null', 'Product title cannot be null', 'staging.products', 'title', 'not_null', 'error'),
    ('customer_email_format', 'Customer email must be valid format', 'staging.customers', 'email', 'format', 'warning'),
    ('sale_quantity_positive', 'Sale quantity must be greater than 0', 'staging.sales', 'quantity', 'range', 'error'),
    ('sale_date_not_future', 'Sale date cannot be in the future', 'staging.sales', 'sale_date', 'range', 'error'),
    ('sale_total_matches', 'Total amount should equal quantity * unit_price', 'staging.sales', 'total_amount', 'expression', 'warning');
GO

PRINT 'Quality layer tables created successfully';
GO
