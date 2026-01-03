"""
Airflow DAG for data transformation pipeline.

This DAG transforms data through the following layers:
- Raw → Staging (cleaning, validation)
- Staging → Data Warehouse (dimensions, facts)
- Data Warehouse → Data Marts (aggregations)
"""

import sys
from datetime import datetime, timedelta
from uuid import uuid4

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor

# Add src to path for imports
sys.path.insert(0, "/opt/airflow")

from src.loaders.dw_loader import DimensionLoader, FactLoader
from src.loaders.mart_builder import MartBuilder
from src.loaders.staging_loader import StagingLoader
from src.quality.tracker import QualityTracker

# DAG default arguments
default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def load_staging_products(**context) -> dict:
    """Load products from raw to staging layer."""
    batch_id = uuid4()
    context["ti"].xcom_push(key="batch_id", value=str(batch_id))

    loader = StagingLoader(batch_id)
    stats = loader.load_products()

    print(f"Staging products complete: {stats}")
    return stats


def load_staging_customers(**context) -> dict:
    """Load customers from raw to staging layer."""
    batch_id = uuid4()
    loader = StagingLoader(batch_id)
    stats = loader.load_customers()

    print(f"Staging customers complete: {stats}")
    return stats


def load_staging_sales(**context) -> dict:
    """Load sales from raw to staging layer."""
    batch_id = uuid4()
    loader = StagingLoader(batch_id)
    stats = loader.load_sales()

    print(f"Staging sales complete: {stats}")
    return stats


def load_dim_product(**context) -> dict:
    """Load product dimension from staging."""
    batch_id = uuid4()
    loader = DimensionLoader(batch_id)
    stats = loader.load_dim_product()

    print(f"dim_product load complete: {stats}")
    return stats


def load_dim_customer(**context) -> dict:
    """Load customer dimension from staging."""
    batch_id = uuid4()
    loader = DimensionLoader(batch_id)
    stats = loader.load_dim_customer()

    print(f"dim_customer load complete: {stats}")
    return stats


def load_fact_sales(**context) -> dict:
    """Load sales facts from staging."""
    batch_id = uuid4()
    loader = FactLoader(batch_id)
    stats = loader.load_fact_sales()

    # Update customer segments based on new data
    segments_updated = loader.update_customer_segments()
    stats["segments_updated"] = segments_updated

    print(f"fact_sales load complete: {stats}")
    return stats


def build_data_marts(**context) -> dict:
    """Build all data marts."""
    batch_id = uuid4()
    builder = MartBuilder(batch_id)
    results = builder.build_all()

    print(f"Data marts built: {results}")
    return results


def log_transformation_summary(**context) -> None:
    """Log final transformation summary."""
    ti = context["ti"]

    staging_products = ti.xcom_pull(task_ids="staging_products")
    staging_customers = ti.xcom_pull(task_ids="staging_customers")
    staging_sales = ti.xcom_pull(task_ids="staging_sales")
    dim_product = ti.xcom_pull(task_ids="load_dim_product")
    dim_customer = ti.xcom_pull(task_ids="load_dim_customer")
    fact_sales = ti.xcom_pull(task_ids="load_fact_sales")
    marts = ti.xcom_pull(task_ids="build_data_marts")

    print("\n" + "=" * 70)
    print("TRANSFORMATION PIPELINE SUMMARY")
    print("=" * 70)
    print("\nSTAGING LAYER:")
    print(f"  Products:  {staging_products}")
    print(f"  Customers: {staging_customers}")
    print(f"  Sales:     {staging_sales}")
    print("\nDATA WAREHOUSE:")
    print(f"  dim_product:  {dim_product}")
    print(f"  dim_customer: {dim_customer}")
    print(f"  fact_sales:   {fact_sales}")
    print("\nDATA MARTS:")
    for mart, count in (marts or {}).items():
        print(f"  {mart}: {count} rows")
    print("=" * 70 + "\n")


# Define the DAG
with DAG(
    dag_id="data_transformation",
    default_args=default_args,
    description="Transform data: raw → staging → DW → marts",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["transformation", "staging", "dw", "mart"],
) as dag:

    # Wait for ingestion to complete (optional - for scheduled runs)
    # wait_for_ingestion = ExternalTaskSensor(
    #     task_id="wait_for_ingestion",
    #     external_dag_id="data_ingestion",
    #     external_task_id="log_quality_summary",
    #     timeout=600,
    #     mode="poke",
    # )

    # Staging layer tasks (can run in parallel)
    staging_products = PythonOperator(
        task_id="staging_products",
        python_callable=load_staging_products,
        provide_context=True,
    )

    staging_customers = PythonOperator(
        task_id="staging_customers",
        python_callable=load_staging_customers,
        provide_context=True,
    )

    staging_sales = PythonOperator(
        task_id="staging_sales",
        python_callable=load_staging_sales,
        provide_context=True,
    )

    # Dimension loads (depend on staging, can run in parallel)
    dim_product = PythonOperator(
        task_id="load_dim_product",
        python_callable=load_dim_product,
        provide_context=True,
    )

    dim_customer = PythonOperator(
        task_id="load_dim_customer",
        python_callable=load_dim_customer,
        provide_context=True,
    )

    # Fact load (depends on dimensions)
    fact_sales = PythonOperator(
        task_id="load_fact_sales",
        python_callable=load_fact_sales,
        provide_context=True,
    )

    # Build data marts (depends on facts)
    marts = PythonOperator(
        task_id="build_data_marts",
        python_callable=build_data_marts,
        provide_context=True,
    )

    # Summary
    summary = PythonOperator(
        task_id="log_summary",
        python_callable=log_transformation_summary,
        provide_context=True,
    )

    # Task dependencies
    # Staging layer (parallel)
    [staging_products, staging_customers, staging_sales]

    # Dimensions depend on staging
    staging_products >> dim_product
    staging_customers >> dim_customer

    # Facts depend on dimensions and staging sales
    [dim_product, dim_customer, staging_sales] >> fact_sales

    # Marts depend on facts
    fact_sales >> marts >> summary
