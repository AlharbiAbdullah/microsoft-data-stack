# microsoft-data-stack

Airflow loads API and CSV sales data into a SQL Server star schema that Superset reads, in Docker Compose.

Status: working · portfolio project · 2026-01

![The Fake Store API and sample CSVs are extracted by Airflow into raw tables in SQL Server. A second Airflow DAG cleans them into staging, loads a star schema and rebuilds the marts. Superset queries the dashboard views. An init container creates the tables and views at startup, and Ruff, mypy and pytest check the code.](docs/diagrams/architecture.excalidraw.svg)

## What it does

Turns e-commerce sales records into answers on revenue, profit, top products, categories,
regions and customer segments. Every ingestion run logs, per source, the records it received
and the records it stored.

## How it works

1. **Source.** The Fake Store API (`/products`, `/users`, `/carts`, no key) and three
   sample CSVs in `data/sample/`: products, customers and sales.
2. **Schema.** At startup the `sqlserver-init` container creates the `datawarehouse`
   database and runs `sql/01` to `sql/07` in order with sqlcmd: schemas, tables, views.
3. **Ingest.** The `data_ingestion` DAG extracts the API and the CSVs in parallel, flattens
   nested records into `raw.*` tables and logs received and stored counts per source.
4. **Warehouse.** SQL Server 2022 holds five schemas: `raw`, `staging`, `dw` (the star
   schema), `mart` and `quality` (the run log). Views in `dw` and `quality` feed the dashboards.
5. **Transform.** The `data_transformation` DAG cleans and validates the latest raw batch,
   loads the star schema with SCD Type 2 dimensions, then rebuilds the four marts.
6. **Consume.** Apache Superset starts connected to the warehouse. The sales and quality
   dashboards are built from the views; SQL Lab queries any layer.
7. **Checks.** Ruff lints and formats, mypy checks types, pytest runs the unit tests with
   the API mocked.

## Tech stack

![Tech stack: Docker Compose; Fake Store API, sample CSVs; Apache Airflow; SQL Server; Apache Superset; sqlcmd; Apache Airflow; uv, Ruff, pytest](docs/diagrams/tech-stack.excalidraw.svg)

## Decisions

- **Raw kept as received over cleaning on the way in:** for audit. Each raw row keeps the
  source JSON or CSV line and a batch id. Cost: raw tables grow on every run, and staging
  reads only the latest batch.
- **Airflow over hand-run scripts:** scheduling, monitoring and retries (two per task).
  Cost: a webserver, a scheduler, an init container and a Postgres metadata database.
- **Docker Compose over a manual install:** the whole platform starts with one command.
  Cost: seven containers on one machine, two of them one-shot init jobs.

## Run it

Needs Docker with Compose, and internet access for the Fake Store API.

```sh
cp .env.example .env                    # set your own passwords here
docker compose up -d
docker compose logs -f sqlserver-init   # wait for "Database initialization complete!"
```

Then, in Airflow at http://localhost:8080, enable and trigger `data_ingestion`, then
`data_transformation`. Superset is at http://localhost:8088. Logins: [docs/operations.md](docs/operations.md).

## Checks

```sh
uv sync --extra dev
uv run ruff check src/            # lint rules in pyproject.toml
uv run ruff format --check src/   # one code format
uv run mypy src/                  # every function typed
uv run pytest src/tests/ -v       # cleaners, validators, connectors, quality tracker
```

No CI: nothing runs these on push.

## Layout

```
airflow/    Airflow image and the two DAGs
src/        connectors, loaders, transformers, quality tracker, tests
sql/        warehouse tables and dashboard views, run in order at startup
superset/   Superset image, config, connection bootstrap, dashboard guide
data/       sample CSVs
docs/       operations reference, diagrams
```

## Docs

- [docs/operations.md](docs/operations.md): services and logins, data layers, views,
  quality log, commands, troubleshooting.
- [superset/dashboards/DASHBOARD_SETUP.md](superset/dashboards/DASHBOARD_SETUP.md): the two
  dashboards, chart by chart.
- [SPEC.md](SPEC.md): the original design spec. Where it differs from the code, the code wins.
- [docs/diagrams/diagrams.py](docs/diagrams/diagrams.py): the scene script behind both diagrams.
