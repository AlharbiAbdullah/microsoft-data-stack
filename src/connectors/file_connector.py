"""File connector for extracting data from CSV and JSON files."""

import csv
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FileExtractionResult:
    """Result of a file extraction operation."""

    source_name: str
    file_path: str
    file_name: str
    records: list[dict[str, Any]]
    records_count: int
    extracted_at: datetime
    success: bool
    error_message: str | None = None


class FileConnector:
    """Connector for extracting data from local files."""

    def __init__(self, base_path: str | Path):
        self.base_path = Path(base_path)

    def extract_csv(
        self,
        file_name: str,
        source_name: str,
        delimiter: str = ",",
        encoding: str = "utf-8",
    ) -> FileExtractionResult:
        """
        Extract data from a CSV file.

        Args:
            file_name: Name of the CSV file
            source_name: Name to identify this data source
            delimiter: CSV delimiter character
            encoding: File encoding

        Returns:
            FileExtractionResult with extracted records and metadata
        """
        file_path = self.base_path / file_name
        extracted_at = datetime.now(timezone.utc)

        logger.info(f"Extracting from {file_path}")

        try:
            records = []
            with open(file_path, "r", encoding=encoding, newline="") as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                for line_num, row in enumerate(reader, start=2):
                    record = dict(row)
                    record["_file_name"] = file_name
                    record["_line_number"] = line_num
                    record["_raw_line"] = delimiter.join(row.values())
                    records.append(record)

            logger.info(f"Extracted {len(records)} records from {file_name}")

            return FileExtractionResult(
                source_name=source_name,
                file_path=str(file_path),
                file_name=file_name,
                records=records,
                records_count=len(records),
                extracted_at=extracted_at,
                success=True,
            )

        except FileNotFoundError:
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            return FileExtractionResult(
                source_name=source_name,
                file_path=str(file_path),
                file_name=file_name,
                records=[],
                records_count=0,
                extracted_at=extracted_at,
                success=False,
                error_message=error_msg,
            )
        except Exception as e:
            error_msg = f"Error reading {file_path}: {e}"
            logger.error(error_msg)
            return FileExtractionResult(
                source_name=source_name,
                file_path=str(file_path),
                file_name=file_name,
                records=[],
                records_count=0,
                extracted_at=extracted_at,
                success=False,
                error_message=error_msg,
            )

    def extract_json(
        self,
        file_name: str,
        source_name: str,
        encoding: str = "utf-8",
    ) -> FileExtractionResult:
        """
        Extract data from a JSON file.

        Args:
            file_name: Name of the JSON file
            source_name: Name to identify this data source
            encoding: File encoding

        Returns:
            FileExtractionResult with extracted records and metadata
        """
        file_path = self.base_path / file_name
        extracted_at = datetime.now(timezone.utc)

        logger.info(f"Extracting from {file_path}")

        try:
            with open(file_path, "r", encoding=encoding) as f:
                data = json.load(f)

            records = data if isinstance(data, list) else [data]
            for i, record in enumerate(records):
                record["_file_name"] = file_name
                record["_line_number"] = i + 1

            logger.info(f"Extracted {len(records)} records from {file_name}")

            return FileExtractionResult(
                source_name=source_name,
                file_path=str(file_path),
                file_name=file_name,
                records=records,
                records_count=len(records),
                extracted_at=extracted_at,
                success=True,
            )

        except FileNotFoundError:
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            return FileExtractionResult(
                source_name=source_name,
                file_path=str(file_path),
                file_name=file_name,
                records=[],
                records_count=0,
                extracted_at=extracted_at,
                success=False,
                error_message=error_msg,
            )
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in {file_path}: {e}"
            logger.error(error_msg)
            return FileExtractionResult(
                source_name=source_name,
                file_path=str(file_path),
                file_name=file_name,
                records=[],
                records_count=0,
                extracted_at=extracted_at,
                success=False,
                error_message=error_msg,
            )


class SampleDataConnector(FileConnector):
    """Connector for the sample data files."""

    def __init__(self, data_path: str | Path = "/opt/airflow/data/sample"):
        super().__init__(data_path)

    def extract_products(self) -> FileExtractionResult:
        """Extract products from CSV."""
        return self.extract_csv("products.csv", "csv_products")

    def extract_customers(self) -> FileExtractionResult:
        """Extract customers from CSV."""
        return self.extract_csv("customers.csv", "csv_customers")

    def extract_sales(self) -> FileExtractionResult:
        """Extract sales from CSV."""
        return self.extract_csv("sales.csv", "csv_sales")

    def extract_all(self) -> dict[str, FileExtractionResult]:
        """Extract all sample data files."""
        return {
            "products": self.extract_products(),
            "customers": self.extract_customers(),
            "sales": self.extract_sales(),
        }


def transform_csv_product(record: dict[str, Any]) -> dict[str, Any]:
    """Transform CSV product record for raw layer."""
    return {
        "product_id": record.get("product_id"),
        "product_name": record.get("product_name"),
        "category": record.get("category"),
        "price": record.get("price"),
        "cost": record.get("cost"),
        "stock_quantity": record.get("stock_quantity"),
        "supplier": record.get("supplier"),
        "raw_line": record.get("_raw_line"),
        "file_name": record.get("_file_name"),
        "line_number": record.get("_line_number"),
    }


def transform_csv_customer(record: dict[str, Any]) -> dict[str, Any]:
    """Transform CSV customer record for raw layer."""
    return {
        "customer_id": record.get("customer_id"),
        "first_name": record.get("first_name"),
        "last_name": record.get("last_name"),
        "email": record.get("email"),
        "phone": record.get("phone"),
        "city": record.get("city"),
        "state": record.get("state"),
        "country": record.get("country"),
        "registration_date": record.get("registration_date"),
        "raw_line": record.get("_raw_line"),
        "file_name": record.get("_file_name"),
        "line_number": record.get("_line_number"),
    }


def transform_csv_sale(record: dict[str, Any]) -> dict[str, Any]:
    """Transform CSV sale record for raw layer."""
    return {
        "sale_id": record.get("sale_id"),
        "customer_id": record.get("customer_id"),
        "product_id": record.get("product_id"),
        "quantity": record.get("quantity"),
        "unit_price": record.get("unit_price"),
        "total_amount": record.get("total_amount"),
        "sale_date": record.get("sale_date"),
        "payment_method": record.get("payment_method"),
        "raw_line": record.get("_raw_line"),
        "file_name": record.get("_file_name"),
        "line_number": record.get("_line_number"),
    }
