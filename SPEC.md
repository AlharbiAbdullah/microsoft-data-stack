# Microsoft Data Stack - Portfolio Project

## Overview

A containerized data engineering solution demonstrating end-to-end data pipeline capabilities: ingestion from multiple sources, multi-layer data warehouse architecture, and quality monitoring dashboards.

**Startup**: `docker compose up` → Full data platform running in ~2 minutes

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA SOURCES                                    │
├─────────────────┬───────────────────────────────────────────────────────────┤
│   REST API      │              CSV/JSON Files                               │
│ (Public Dataset)│           (Sample Data Files)                             │
└────────┬────────┴──────────────────────┬────────────────────────────────────┘
         │                               │
         ▼                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INGESTION LAYER (Python)                            │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │  API Connector  │    │  File Connector │    │  Quality Logger │         │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘         │
└───────────┼──────────────────────┼──────────────────────┼───────────────────┘
            │                      │                      │
            ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RAW LAYER (Landing Zone)                          │
│                    File System: /data/raw/{source}/{date}/                  │
│                    Database: raw.* tables (SQL Server)                      │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STAGING LAYER (Cleaned)                             │
│                    Database: staging.* tables                               │
│                    - Data type enforcement                                  │
│                    - Null handling                                          │
│                    - Deduplication                                          │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DATA WAREHOUSE (Star Schema)                           │
│                    Database: dw.* tables                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  dim_date    │  │ dim_product  │  │ dim_customer │  │ fact_sales   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA MARTS (Aggregated)                           │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐    │
│  │   mart_sales_daily │  │  mart_product_perf │  │  mart_quality_rpt  │    │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘    │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          BI / VISUALIZATION                                 │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     Apache Superset Dashboard                        │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐  │   │
│  │  │ Sales KPIs  │  │ Trends Chart│  │  Data Quality Report        │  │   │
│  │  │             │  │             │  │  ┌─────────┬─────────────┐  │  │   │
│  │  │ $1.2M       │  │    ╱╲       │  │  │Received │ 10,000 rows │  │  │   │
│  │  │ Total Sales │  │   ╱  ╲╱╲    │  │  │Stored   │  9,847 rows │  │  │   │
│  │  │             │  │  ╱      ╲   │  │  │Quality  │   98.47%    │  │  │   │
│  │  └─────────────┘  └─────────────┘  │  └─────────┴─────────────┘  │  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Orchestration** | Apache Airflow | DAG scheduling, monitoring, retries |
| **Ingestion** | Python (requests, pandas) | API calls, file parsing |
| **Storage - Files** | Docker Volume | Raw file landing zone |
| **Storage - Database** | SQL Server 2022 | Staging, DW, Data Marts |
| **Transformation** | Python + SQL | Data cleaning, star schema loading |
| **Visualization** | Apache Superset | Dashboards, quality reports |
| **Infrastructure** | Docker Compose | Single-command deployment |

---

## Data Flow

### 1. Ingestion Pipeline

```
┌────────────────────────────────────────────────────────────────┐
│                     Airflow DAG: data_ingestion                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  [extract_api] ──┬──► [load_raw_files] ──► [load_raw_db]      │
│                  │                              │              │
│  [extract_csv] ──┘                              │              │
│                                                 ▼              │
│                                     [log_quality_metrics]      │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 2. Transformation Pipeline

```
┌────────────────────────────────────────────────────────────────┐
│                   Airflow DAG: data_transformation             │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  [raw_to_staging] ──► [staging_to_dims] ──► [staging_to_facts]│
│                              │                    │            │
│                              └────────┬───────────┘            │
│                                       ▼                        │
│                              [build_data_marts]                │
│                                       │                        │
│                                       ▼                        │
│                           [update_quality_report]              │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Data Quality Report

The crown jewel of this project - a visual comparison of **received vs stored** data:

| Metric | Description |
|--------|-------------|
| `records_received` | Count of records extracted from source |
| `records_stored` | Count of records successfully loaded |
| `records_rejected` | Count of records that failed validation |
| `quality_score` | `(stored / received) * 100` |
| `rejection_reasons` | Breakdown by error type |

### Quality Tracking Table

```sql
CREATE TABLE quality.ingestion_log (
    log_id INT IDENTITY(1,1) PRIMARY KEY,
    pipeline_run_id UNIQUEIDENTIFIER,
    source_name VARCHAR(100),
    extraction_timestamp DATETIME2,
    records_received INT,
    records_stored INT,
    records_rejected INT,
    quality_score DECIMAL(5,2),
    rejection_details NVARCHAR(MAX),  -- JSON
    created_at DATETIME2 DEFAULT GETDATE()
);
```

---

## Project Structure

```
microsoft_data_stack/
├── docker-compose.yml          # One-command deployment
├── .env.example                 # Environment template
├── SPEC.md                      # This file
├── README.md                    # Quick start guide
│
├── airflow/
│   ├── dags/
│   │   ├── ingestion_dag.py    # Extract from sources
│   │   └── transform_dag.py    # Load DW and marts
│   ├── plugins/
│   └── Dockerfile
│
├── src/
│   ├── __init__.py
│   ├── connectors/
│   │   ├── __init__.py
│   │   ├── api_connector.py    # REST API extraction
│   │   └── file_connector.py   # CSV/JSON parsing
│   │
│   ├── loaders/
│   │   ├── __init__.py
│   │   ├── raw_loader.py       # Load to raw layer
│   │   ├── staging_loader.py   # Load to staging
│   │   └── dw_loader.py        # Load dimensions/facts
│   │
│   ├── transformers/
│   │   ├── __init__.py
│   │   ├── cleaners.py         # Data cleaning logic
│   │   └── validators.py       # Data validation rules
│   │
│   ├── quality/
│   │   ├── __init__.py
│   │   └── tracker.py          # Quality metrics logging
│   │
│   └── tests/
│       ├── test_connectors.py
│       ├── test_loaders.py
│       └── test_quality.py
│
├── sql/
│   ├── 01_create_schemas.sql   # raw, staging, dw, mart, quality
│   ├── 02_raw_tables.sql
│   ├── 03_staging_tables.sql
│   ├── 04_dw_tables.sql        # Star schema
│   ├── 05_mart_tables.sql
│   └── 06_quality_tables.sql
│
├── data/
│   ├── sample/                  # Sample CSV files for demo
│   │   ├── products.csv
│   │   ├── customers.csv
│   │   └── sales.csv
│   └── raw/                     # Landing zone (git-ignored)
│
├── superset/
│   ├── dashboards/              # Exported dashboard configs
│   └── Dockerfile
│
└── scripts/
    ├── init_db.sh               # Database initialization
    └── seed_data.sh             # Load sample data
```

---

## Docker Services

```yaml
services:
  # SQL Server 2022 - Data Warehouse
  sqlserver:
    image: mcr.microsoft.com/mssql/server:2022-latest
    ports:
      - "1433:1433"
    environment:
      - ACCEPT_EULA=Y
      - MSSQL_SA_PASSWORD=${DB_PASSWORD}
    volumes:
      - sqlserver_data:/var/opt/mssql

  # Apache Airflow - Orchestration
  airflow:
    build: ./airflow
    ports:
      - "8080:8080"
    depends_on:
      - sqlserver
    volumes:
      - ./airflow/dags:/opt/airflow/dags
      - ./src:/opt/airflow/src
      - ./data:/opt/airflow/data

  # Apache Superset - Visualization
  superset:
    build: ./superset
    ports:
      - "8088:8088"
    depends_on:
      - sqlserver
```

---

## Sample Data Source

Using the **Fake Store API** (https://fakestoreapi.com) for realistic e-commerce data:

| Endpoint | Data | Records |
|----------|------|---------|
| `/products` | Product catalog | ~20 |
| `/carts` | Shopping carts (sales) | ~7 |
| `/users` | Customer data | ~10 |

Combined with generated CSV files to simulate:
- Historical sales data (1000+ records)
- Product inventory updates
- Customer interactions

---

## Star Schema Design

```
                    ┌─────────────────┐
                    │    dim_date     │
                    ├─────────────────┤
                    │ date_key (PK)   │
                    │ full_date       │
                    │ day_of_week     │
                    │ month           │
                    │ quarter         │
                    │ year            │
                    └────────┬────────┘
                             │
┌─────────────────┐          │          ┌─────────────────┐
│  dim_product    │          │          │  dim_customer   │
├─────────────────┤          │          ├─────────────────┤
│ product_key(PK) │          │          │ customer_key(PK)│
│ product_id      │          │          │ customer_id     │
│ title           │          │          │ name            │
│ category        │    ┌─────┴─────┐    │ email           │
│ price           │◄───┤fact_sales ├───►│ city            │
│ description     │    ├───────────┤    │ created_date    │
└─────────────────┘    │ sale_key  │    └─────────────────┘
                       │ date_key  │
                       │product_key│
                       │customer_key│
                       │ quantity  │
                       │ unit_price│
                       │ total_amt │
                       │ created_at│
                       └───────────┘
```

---

## Demo Walkthrough (Interview Ready)

### 1. Start the Stack (2 min)
```bash
git clone <repo>
cd microsoft_data_stack
cp .env.example .env
docker compose up -d
```

### 2. Show Airflow DAGs (1 min)
- Open http://localhost:8080
- Trigger `ingestion_dag`
- Show task dependencies and logs

### 3. Query Data Layers (2 min)
```sql
-- Raw layer (as-is from source)
SELECT TOP 5 * FROM raw.api_products;

-- Staging layer (cleaned)
SELECT TOP 5 * FROM staging.products;

-- Data Warehouse (star schema)
SELECT
    d.full_date,
    p.title,
    SUM(f.total_amt) as revenue
FROM dw.fact_sales f
JOIN dw.dim_date d ON f.date_key = d.date_key
JOIN dw.dim_product p ON f.product_key = p.product_key
GROUP BY d.full_date, p.title;
```

### 4. Quality Report Dashboard (1 min)
- Open http://localhost:8088 (Superset)
- Show "Data Quality Report" dashboard
- Highlight received vs stored metrics

### 5. Key Talking Points
- **Scalability**: "Airflow handles retries and backfills automatically"
- **Data Quality**: "Every pipeline run logs received vs stored counts"
- **Modularity**: "Each layer is independent - easy to swap technologies"
- **Best Practices**: "Star schema for analytics, raw preservation for audit"

---

## Implementation Phases

### Phase 1: Foundation ✓
- [x] Docker Compose setup with SQL Server
- [x] Database schema creation (all layers)
- [x] Basic project structure

### Phase 2: Ingestion ✓
- [x] API connector (Fake Store API)
- [x] File connector (CSV parsing)
- [x] Raw layer loading
- [x] Quality metrics logging

### Phase 3: Transformation ✓
- [x] Staging layer (cleaning, validation)
- [x] Dimension table loading
- [x] Fact table loading
- [x] Data mart aggregations

### Phase 4: Orchestration ✓
- [x] Airflow DAG for ingestion
- [x] Airflow DAG for transformation
- [x] Error handling and retries

### Phase 5: Visualization ✓
- [x] Superset connection to SQL Server
- [x] Sales KPI dashboard
- [x] Data Quality Report dashboard

### Phase 6: Polish ✓
- [x] README with quick start
- [x] Sample data seeding
- [ ] Screenshot documentation (optional)

---

## Success Criteria

| Requirement | Metric |
|-------------|--------|
| One-command startup | `docker compose up` works in < 3 min |
| Data ingestion | API + CSV sources loading successfully |
| Multi-layer architecture | raw → staging → dw → mart flow complete |
| Quality tracking | Received vs stored visible in dashboard |
| Interview demo | Full walkthrough in < 10 minutes |

---

## Future Enhancements (Out of Scope)

- Real-time streaming with Kafka
- dbt for transformation layer
- Great Expectations for data validation
- CI/CD pipeline for automated testing
- Kubernetes deployment
