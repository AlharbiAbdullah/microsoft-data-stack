# Superset Dashboard Setup Guide

This guide walks you through creating the two main dashboards for the Microsoft Data Stack project.

## Prerequisites

1. Stack is running: `docker compose up -d`
2. Data has been ingested and transformed (run both Airflow DAGs)
3. Access Superset at http://localhost:8088 (admin/admin)

## Database Connection Setup

The database connection should be auto-configured. If not:

1. Go to **Settings** → **Database Connections**
2. Click **+ Database**
3. Select **Microsoft SQL Server**
4. Enter connection details:
   - Host: `sqlserver`
   - Port: `1433`
   - Database: `datawarehouse`
   - Username: `sa`
   - Password: (from your .env file)
5. Test connection and save

---

## Dashboard 1: Sales Analytics

### Chart 1: Revenue KPIs (Big Number)

**Dataset**: `dw.vw_sales_kpi_summary`

| Setting | Value |
|---------|-------|
| Chart Type | Big Number |
| Metric | `total_revenue` |
| Subheader | "Total Revenue" |

Repeat for: `total_orders`, `unique_customers`, `avg_order_value`

### Chart 2: Daily Sales Trend (Line Chart)

**Dataset**: `dw.vw_daily_sales_trend`

| Setting | Value |
|---------|-------|
| Chart Type | Time-series Line Chart |
| Time Column | `full_date` |
| Metrics | `revenue`, `profit` |
| Time Grain | Day |

### Chart 3: Sales by Category (Pie Chart)

**Dataset**: `dw.vw_sales_by_category`

| Setting | Value |
|---------|-------|
| Chart Type | Pie Chart |
| Dimension | `category` |
| Metric | `revenue` |
| Show Labels | Yes |

### Chart 4: Top 10 Products (Bar Chart)

**Dataset**: `dw.vw_top_products`

| Setting | Value |
|---------|-------|
| Chart Type | Bar Chart |
| Dimension | `product_name` |
| Metric | `revenue` |
| Row Limit | 10 |
| Sort | Descending |

### Chart 5: Customer Segments (Donut Chart)

**Dataset**: `dw.vw_customer_segments`

| Setting | Value |
|---------|-------|
| Chart Type | Pie Chart (Donut) |
| Dimension | `customer_segment` |
| Metric | `customer_count` |
| Donut | Yes |

### Chart 6: Monthly Comparison (Bar Chart)

**Dataset**: `dw.vw_monthly_sales`

| Setting | Value |
|---------|-------|
| Chart Type | Bar Chart |
| X-Axis | `month_name` |
| Metrics | `revenue`, `profit` |
| Group By | `year` |

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│  [Revenue]    [Orders]    [Customers]    [Avg Order]        │
│   $X,XXX        XXX          XXX           $XX.XX           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│           Daily Sales Trend (Line Chart)                    │
│                                                             │
├─────────────────────────────┬───────────────────────────────┤
│                             │                               │
│   Sales by Category (Pie)   │   Customer Segments (Donut)   │
│                             │                               │
├─────────────────────────────┴───────────────────────────────┤
│                                                             │
│              Top 10 Products by Revenue (Bar)               │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│              Monthly Sales Comparison (Bar)                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Dashboard 2: Data Quality Report

### Chart 1: Quality Score KPI (Big Number)

**Dataset**: `quality.vw_quality_summary`

| Setting | Value |
|---------|-------|
| Chart Type | Big Number |
| Metric | `overall_quality_score` |
| Subheader | "Overall Quality %" |

Repeat for: `total_records_received`, `total_records_stored`, `total_records_rejected`

### Chart 2: Quality Trend (Line Chart)

**Dataset**: `quality.vw_quality_trend`

| Setting | Value |
|---------|-------|
| Chart Type | Time-series Line Chart |
| Time Column | `run_date` |
| Metric | `avg_quality_score` |
| Time Grain | Day |

### Chart 3: Quality by Source (Bar Chart)

**Dataset**: `quality.vw_quality_by_source`

| Setting | Value |
|---------|-------|
| Chart Type | Bar Chart |
| X-Axis | `source_name` |
| Metrics | `total_received`, `total_stored` |
| Show Values | Yes |

### Chart 4: Received vs Stored (Grouped Bar)

**Dataset**: `quality.vw_quality_by_source`

| Setting | Value |
|---------|-------|
| Chart Type | Bar Chart |
| X-Axis | `source_name` |
| Metrics | `total_received`, `total_stored`, `total_rejected` |
| Bar Mode | Group |

### Chart 5: Recent Pipeline Runs (Table)

**Dataset**: `quality.vw_recent_runs`

| Setting | Value |
|---------|-------|
| Chart Type | Table |
| Columns | `pipeline_name`, `source_name`, `records_received`, `records_stored`, `quality_score`, `status`, `created_at` |
| Row Limit | 20 |

### Chart 6: Pipeline Status (Pie Chart)

**Dataset**: `quality.vw_quality_summary`

Create a custom query:
```sql
SELECT 'Success' as status, successful_runs as count FROM quality.vw_quality_summary
UNION ALL
SELECT 'Failed' as status, failed_runs as count FROM quality.vw_quality_summary
```

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│  [Quality %]  [Received]   [Stored]    [Rejected]           │
│    98.5%       10,000       9,850         150               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│           Quality Score Trend (Line Chart)                  │
│                                                             │
├─────────────────────────────┬───────────────────────────────┤
│                             │                               │
│  Quality by Source (Bar)    │   Pipeline Status (Pie)       │
│                             │                               │
├─────────────────────────────┴───────────────────────────────┤
│                                                             │
│        Received vs Stored by Source (Grouped Bar)           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│              Recent Pipeline Runs (Table)                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick SQL Queries for SQL Lab

### Sales Summary
```sql
SELECT * FROM dw.vw_sales_kpi_summary;
```

### Quality Check
```sql
SELECT
    source_name,
    records_received,
    records_stored,
    quality_score,
    status
FROM quality.vw_recent_runs
ORDER BY created_at DESC;
```

### Product Performance
```sql
SELECT TOP 10
    product_name,
    category,
    units_sold,
    revenue,
    revenue_rank
FROM dw.vw_top_products
ORDER BY revenue DESC;
```

---

## Export/Import Dashboards

### Export
1. Open dashboard
2. Click **...** menu → **Export**
3. Save JSON file

### Import
1. Go to **Dashboards**
2. Click **Import Dashboard**
3. Select JSON file

---

## Troubleshooting

### Connection Issues
- Verify SQL Server is running: `docker compose ps`
- Check host is `sqlserver` (not `localhost`)
- Ensure password matches .env file

### No Data in Charts
- Run ingestion DAG first
- Run transformation DAG second
- Check Airflow logs for errors

### Views Not Found
- Run SQL script: `sql/07_dashboard_views.sql`
- Refresh database in Superset
