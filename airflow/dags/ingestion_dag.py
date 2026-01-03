"""
Airflow DAG for data ingestion pipeline.

This DAG extracts data from:
- Fake Store API (products, users, carts)
- Sample CSV files (products, customers, sales)

And loads them into the raw layer of the data warehouse.
"""

import sys
from datetime import datetime, timedelta
from uuid import uuid4

from airflow import DAG
from airflow.operators.python import PythonOperator

# Add src to path for imports
sys.path.insert(0, "/opt/airflow")

from src.connectors.api_connector import FakeStoreAPIConnector
from src.connectors.file_connector import SampleDataConnector
from src.loaders.raw_loader import RawLoader
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


def extract_and_load_api_data(**context) -> dict:
    """Extract data from Fake Store API and load to raw layer."""
    batch_id = uuid4()
    tracker = QualityTracker(batch_id=batch_id, pipeline_name="api_ingestion")
    loader = RawLoader(batch_id=batch_id)
    connector = FakeStoreAPIConnector()

    results = {}

    # Extract and load products
    tracker.start_extraction("api_products", "api")
    products_result = connector.extract_products()
    tracker.complete_extraction("api_products", products_result.records_count)

    tracker.start_load("api_products")
    products_loaded = loader.load_api_products(products_result)
    tracker.complete_load("api_products", products_loaded)
    results["products"] = {"received": products_result.records_count, "loaded": products_loaded}

    # Extract and load users
    tracker.start_extraction("api_users", "api")
    users_result = connector.extract_users()
    tracker.complete_extraction("api_users", users_result.records_count)

    tracker.start_load("api_users")
    users_loaded = loader.load_api_users(users_result)
    tracker.complete_load("api_users", users_loaded)
    results["users"] = {"received": users_result.records_count, "loaded": users_loaded}

    # Extract and load carts
    tracker.start_extraction("api_carts", "api")
    carts_result = connector.extract_carts()
    tracker.complete_extraction("api_carts", carts_result.records_count)

    tracker.start_load("api_carts")
    carts_loaded = loader.load_api_carts(carts_result)
    tracker.complete_load("api_carts", carts_loaded)
    results["carts"] = {"received": carts_result.records_count, "loaded": carts_loaded}

    # Save quality metrics
    tracker.save_to_database()
    tracker.print_summary()

    # Push batch_id to XCom for downstream tasks
    context["ti"].xcom_push(key="api_batch_id", value=str(batch_id))

    return results


def extract_and_load_csv_data(**context) -> dict:
    """Extract data from CSV files and load to raw layer."""
    batch_id = uuid4()
    tracker = QualityTracker(batch_id=batch_id, pipeline_name="csv_ingestion")
    loader = RawLoader(batch_id=batch_id)
    connector = SampleDataConnector()

    results = {}

    # Extract and load products
    tracker.start_extraction("csv_products", "csv")
    products_result = connector.extract_products()
    tracker.complete_extraction("csv_products", products_result.records_count)

    tracker.start_load("csv_products")
    products_loaded = loader.load_csv_products(products_result)
    tracker.complete_load("csv_products", products_loaded)
    results["products"] = {"received": products_result.records_count, "loaded": products_loaded}

    # Extract and load customers
    tracker.start_extraction("csv_customers", "csv")
    customers_result = connector.extract_customers()
    tracker.complete_extraction("csv_customers", customers_result.records_count)

    tracker.start_load("csv_customers")
    customers_loaded = loader.load_csv_customers(customers_result)
    tracker.complete_load("csv_customers", customers_loaded)
    results["customers"] = {"received": customers_result.records_count, "loaded": customers_loaded}

    # Extract and load sales
    tracker.start_extraction("csv_sales", "csv")
    sales_result = connector.extract_sales()
    tracker.complete_extraction("csv_sales", sales_result.records_count)

    tracker.start_load("csv_sales")
    sales_loaded = loader.load_csv_sales(sales_result)
    tracker.complete_load("csv_sales", sales_loaded)
    results["sales"] = {"received": sales_result.records_count, "loaded": sales_loaded}

    # Save quality metrics
    tracker.save_to_database()
    tracker.print_summary()

    # Push batch_id to XCom
    context["ti"].xcom_push(key="csv_batch_id", value=str(batch_id))

    return results


def log_quality_summary(**context) -> None:
    """Log final quality summary for both ingestion sources."""
    api_batch = context["ti"].xcom_pull(key="api_batch_id", task_ids="extract_api_data")
    csv_batch = context["ti"].xcom_pull(key="csv_batch_id", task_ids="extract_csv_data")

    print("\n" + "=" * 70)
    print("INGESTION PIPELINE COMPLETE")
    print("=" * 70)
    print(f"API Batch ID: {api_batch}")
    print(f"CSV Batch ID: {csv_batch}")
    print("=" * 70 + "\n")


# Define the DAG
with DAG(
    dag_id="data_ingestion",
    default_args=default_args,
    description="Extract data from API and CSV sources into raw layer",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ingestion", "raw"],
) as dag:

    extract_api = PythonOperator(
        task_id="extract_api_data",
        python_callable=extract_and_load_api_data,
        provide_context=True,
    )

    extract_csv = PythonOperator(
        task_id="extract_csv_data",
        python_callable=extract_and_load_csv_data,
        provide_context=True,
    )

    quality_summary = PythonOperator(
        task_id="log_quality_summary",
        python_callable=log_quality_summary,
        provide_context=True,
    )

    # API and CSV extraction run in parallel, then quality summary
    [extract_api, extract_csv] >> quality_summary
