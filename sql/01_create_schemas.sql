-- =============================================================================
-- Microsoft Data Stack - Schema Creation
-- Creates the layered data architecture schemas
-- =============================================================================

USE datawarehouse;
GO

-- Raw Layer: Landing zone for source data (as-is)
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'raw')
BEGIN
    EXEC('CREATE SCHEMA raw');
END
GO

-- Staging Layer: Cleaned and validated data
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'staging')
BEGIN
    EXEC('CREATE SCHEMA staging');
END
GO

-- Data Warehouse Layer: Star schema for analytics
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'dw')
BEGIN
    EXEC('CREATE SCHEMA dw');
END
GO

-- Data Mart Layer: Aggregated views for specific use cases
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'mart')
BEGIN
    EXEC('CREATE SCHEMA mart');
END
GO

-- Quality Layer: Data quality tracking and metrics
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'quality')
BEGIN
    EXEC('CREATE SCHEMA quality');
END
GO

PRINT 'All schemas created successfully';
GO
