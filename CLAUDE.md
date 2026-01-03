# Microsoft Data Stack - Claude Instructions

## Project Overview

This is a **portfolio project** demonstrating end-to-end data engineering capabilities:
- Data ingestion from REST APIs and CSV files
- Multi-layer data warehouse (raw → staging → DW → marts)
- Data quality tracking (received vs stored metrics)
- Visualization dashboards with Apache Superset

## Tech Stack

| Component | Technology |
|-----------|------------|
| Database | SQL Server 2022 |
| Orchestration | Apache Airflow 2.8 |
| Visualization | Apache Superset 3.1 |
| Language | Python 3.11 |
| Infrastructure | Docker Compose |

## Project Structure

```
microsoft_data_stack/
├── airflow/dags/          # Airflow DAG definitions
├── superset/              # Superset config and dashboards
├── sql/                   # Database schema files (run in order)
├── src/                   # Python source code
│   ├── connectors/        # API and file extraction
│   ├── loaders/           # Data loading (raw, staging, dw, mart)
│   ├── transformers/      # Validation and cleaning
│   ├── quality/           # Quality metrics tracking
│   └── tests/             # Unit tests
└── data/sample/           # Sample CSV data files
```

## Development Commands

```bash
# Start the stack
docker compose up -d

# Run tests
uv run pytest src/tests/ -v

# Lint code
uv run ruff check src/

# Format code
uv run ruff format src/

# Type check
uv run mypy src/
```

## Database Layers

| Schema | Purpose |
|--------|---------|
| `raw.*` | Landing zone - data as-is from sources |
| `staging.*` | Cleaned, validated, typed data |
| `dw.*` | Star schema (dim_date, dim_product, dim_customer, fact_sales) |
| `mart.*` | Pre-aggregated analytics tables |
| `quality.*` | Pipeline metrics and audit logs |

## Key Files

- `airflow/dags/ingestion_dag.py` - Extracts from API + CSV → raw layer
- `airflow/dags/transform_dag.py` - Transforms raw → staging → dw → marts
- `src/quality/tracker.py` - Logs received vs stored metrics
- `sql/07_dashboard_views.sql` - Pre-built views for Superset

## Data Flow

```
API/CSV → Raw Layer → Staging Layer → Data Warehouse → Data Marts
                ↓                            ↓
         Quality Logs              Superset Dashboards
```

## Testing

Tests are colocated with source code in `src/tests/`:
- `test_connectors.py` - API and file connector tests
- `test_validators.py` - Data validation rule tests
- `test_cleaners.py` - Data cleaning function tests
- `test_quality.py` - Quality tracker tests

## Important Notes

- All database connections use environment variables from `.env`
- Airflow DAGs should be run in order: ingestion first, then transformation
- Dashboard views in `sql/07_dashboard_views.sql` must be created for Superset
- Quality metrics are logged to `quality.ingestion_log` table
