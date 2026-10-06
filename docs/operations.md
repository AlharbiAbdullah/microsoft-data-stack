# Operations

Services, layers, queries and fixes for the running stack.

## Services

| Service | Address | Login |
|---------|---------|-------|
| Airflow | http://localhost:8080 | `AIRFLOW_ADMIN_USER` and `AIRFLOW_ADMIN_PASSWORD` in `.env` |
| Superset | http://localhost:8088 | the admin user created in `superset/superset_init.sh` (it does not read `.env`) |
| SQL Server | localhost:1433 | user `sa`, password `DB_PASSWORD` in `.env` |

Airflow keeps its metadata in a Postgres container (`mds_postgres`). Superset keeps its own in
SQLite inside the `mds_superset_data` volume.

## Data layers

| Layer | Schema | What it holds |
|-------|--------|---------------|
| Raw | `raw.*` | Records as received, with the source JSON or CSV line and a batch id |
| Staging | `staging.*` | Cleaned, validated, typed records from the latest raw batch |
| Warehouse | `dw.*` | Star schema: `dim_date`, `dim_product`, `dim_customer`, `fact_sales` |
| Marts | `mart.*` | Aggregate tables, truncated and rebuilt on every transformation run |
| Quality | `quality.*` | The ingestion run log and the quality views |

`dim_product` and `dim_customer` keep SCD Type 2 history (`effective_from`, `effective_to`,
`is_current`).

The SQL files drop and recreate every table and view each time `sqlserver-init` runs them.

## Pipelines

Run them from the Airflow UI: enable and trigger `data_ingestion`, then `data_transformation`.

Both DAGs are scheduled `@daily` and are not chained: the `ExternalTaskSensor` in
`transform_dag.py` is commented out. Each task retries twice, five minutes apart.

## Dashboard views

Created by `sql/07_dashboard_views.sql`:

```sql
-- Sales
SELECT * FROM dw.vw_sales_kpi_summary;
SELECT * FROM dw.vw_daily_sales_trend;
SELECT * FROM dw.vw_sales_by_category;
SELECT * FROM dw.vw_top_products;
SELECT * FROM dw.vw_customer_segments;
SELECT * FROM dw.vw_sales_by_region;
SELECT * FROM dw.vw_monthly_sales;

-- Quality
SELECT * FROM quality.vw_quality_summary;
SELECT * FROM quality.vw_quality_by_source;
SELECT * FROM quality.vw_quality_trend;
SELECT * FROM quality.vw_recent_runs;
SELECT * FROM quality.vw_rejection_analysis;
```

Superset starts with a connection named "Microsoft Data Stack" to the warehouse
(`superset/bootstrap_superset.py`). The two dashboards are built by hand:
[superset/dashboards/DASHBOARD_SETUP.md](../superset/dashboards/DASHBOARD_SETUP.md).

## Quality tracking

Each ingestion run writes one row per source to `quality.ingestion_log`:

- `records_received`: records extracted from the source.
- `records_stored`: records inserted into the raw table.
- `quality_score`: a computed column, `(stored / received) × 100`.

```sql
SELECT
    source_name,
    records_received,
    records_stored,
    quality_score,
    created_at
FROM quality.ingestion_log
ORDER BY created_at DESC;
```

## Commands

```bash
docker compose up -d                        # start all services
docker compose down                         # stop all services
docker compose logs -f <service-name>       # follow one service's logs
docker compose restart airflow-webserver    # restart one service
docker compose down -v                      # reset everything, volumes included

# SQL shell on the warehouse
docker exec -it mds_sqlserver /opt/mssql-tools18/bin/sqlcmd \
    -S localhost -U sa -P '<DB_PASSWORD from .env>' -C
```

## Troubleshooting

### SQL Server won't start

- Give Docker at least 2 GB of RAM for SQL Server. The original setup asked for 8 GB free
  for the whole stack.
- Check that `DB_PASSWORD` meets SQL Server's password complexity rules.

### Airflow tasks failing

```bash
# Scheduler logs
docker compose logs airflow-scheduler

# SQL Server connection from inside Airflow, through the pipeline's own module
docker exec mds_airflow_webserver python -c "
import sys; sys.path.insert(0, '/opt/airflow')
from src.database import test_connection
print(test_connection())
"
```

### Superset can't connect to SQL Server

- Check that SQL Server is healthy: `docker compose ps`.
- The connection must use `sqlserver` as the host, not `localhost`.
