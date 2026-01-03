"""Quality metrics tracker for logging pipeline metrics."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from src.database import get_cursor

logger = logging.getLogger(__name__)


@dataclass
class IngestionMetrics:
    """Metrics for a single ingestion operation."""

    source_name: str
    source_type: str  # 'api', 'csv', 'database'
    records_received: int = 0
    records_stored: int = 0
    records_rejected: int = 0
    rejection_reasons: dict[str, int] = field(default_factory=dict)
    extraction_started_at: datetime | None = None
    extraction_completed_at: datetime | None = None
    load_started_at: datetime | None = None
    load_completed_at: datetime | None = None
    error_message: str | None = None

    @property
    def quality_score(self) -> float:
        """Calculate quality score as percentage of records stored."""
        if self.records_received == 0:
            return 100.0
        return (self.records_stored / self.records_received) * 100

    @property
    def status(self) -> str:
        """Determine status based on metrics."""
        if self.error_message:
            return "failed"
        if self.records_rejected > 0:
            return "partial"
        if self.records_stored == self.records_received:
            return "success"
        return "running"


class QualityTracker:
    """Tracker for logging data quality metrics."""

    def __init__(self, batch_id: UUID | None = None, pipeline_name: str = "ingestion"):
        self.batch_id = batch_id or uuid4()
        self.pipeline_name = pipeline_name
        self.metrics: dict[str, IngestionMetrics] = {}

    def start_extraction(self, source_name: str, source_type: str) -> None:
        """Mark the start of extraction for a source."""
        self.metrics[source_name] = IngestionMetrics(
            source_name=source_name,
            source_type=source_type,
            extraction_started_at=datetime.now(timezone.utc),
        )
        logger.info(f"Started extraction for {source_name}")

    def complete_extraction(self, source_name: str, records_received: int) -> None:
        """Mark extraction complete and record count."""
        if source_name in self.metrics:
            self.metrics[source_name].records_received = records_received
            self.metrics[source_name].extraction_completed_at = datetime.now(
                timezone.utc
            )
            logger.info(f"Extraction complete for {source_name}: {records_received} records")

    def start_load(self, source_name: str) -> None:
        """Mark the start of loading for a source."""
        if source_name in self.metrics:
            self.metrics[source_name].load_started_at = datetime.now(timezone.utc)

    def complete_load(
        self,
        source_name: str,
        records_stored: int,
        records_rejected: int = 0,
        rejection_reasons: dict[str, int] | None = None,
    ) -> None:
        """Mark load complete and record counts."""
        if source_name in self.metrics:
            m = self.metrics[source_name]
            m.records_stored = records_stored
            m.records_rejected = records_rejected
            m.rejection_reasons = rejection_reasons or {}
            m.load_completed_at = datetime.now(timezone.utc)
            logger.info(
                f"Load complete for {source_name}: "
                f"stored={records_stored}, rejected={records_rejected}, "
                f"quality={m.quality_score:.2f}%"
            )

    def record_error(self, source_name: str, error_message: str) -> None:
        """Record an error for a source."""
        if source_name in self.metrics:
            self.metrics[source_name].error_message = error_message
            logger.error(f"Error for {source_name}: {error_message}")

    def save_to_database(self) -> None:
        """Save all metrics to the quality.ingestion_log table."""
        with get_cursor() as cursor:
            for source_name, m in self.metrics.items():
                cursor.execute(
                    """
                    INSERT INTO quality.ingestion_log (
                        batch_id, pipeline_name, source_name, source_type,
                        records_received, records_stored, records_rejected,
                        extraction_started_at, extraction_completed_at,
                        load_started_at, load_completed_at,
                        status, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(self.batch_id),
                        self.pipeline_name,
                        source_name,
                        m.source_type,
                        m.records_received,
                        m.records_stored,
                        m.records_rejected,
                        m.extraction_started_at,
                        m.extraction_completed_at,
                        m.load_started_at,
                        m.load_completed_at,
                        m.status,
                        m.error_message,
                    ),
                )

                # Save rejection details if any
                if m.rejection_reasons:
                    for reason, count in m.rejection_reasons.items():
                        cursor.execute(
                            """
                            INSERT INTO quality.rejection_details (
                                batch_id, source_name, rejection_reason,
                                rejection_count
                            ) VALUES (?, ?, ?, ?)
                            """,
                            (
                                str(self.batch_id),
                                source_name,
                                reason,
                                count,
                            ),
                        )

        logger.info(f"Saved quality metrics for batch {self.batch_id}")

    def get_summary(self) -> dict[str, Any]:
        """Get summary of all metrics."""
        total_received = sum(m.records_received for m in self.metrics.values())
        total_stored = sum(m.records_stored for m in self.metrics.values())
        total_rejected = sum(m.records_rejected for m in self.metrics.values())

        return {
            "batch_id": str(self.batch_id),
            "pipeline_name": self.pipeline_name,
            "sources_count": len(self.metrics),
            "total_records_received": total_received,
            "total_records_stored": total_stored,
            "total_records_rejected": total_rejected,
            "overall_quality_score": (
                (total_stored / total_received * 100) if total_received > 0 else 100.0
            ),
            "sources": {
                name: {
                    "received": m.records_received,
                    "stored": m.records_stored,
                    "rejected": m.records_rejected,
                    "quality_score": m.quality_score,
                    "status": m.status,
                }
                for name, m in self.metrics.items()
            },
        }

    def print_summary(self) -> None:
        """Print a formatted summary of metrics."""
        summary = self.get_summary()
        print("\n" + "=" * 60)
        print(f"INGESTION QUALITY REPORT - Batch: {summary['batch_id'][:8]}...")
        print("=" * 60)
        print(f"Pipeline: {summary['pipeline_name']}")
        print(f"Sources processed: {summary['sources_count']}")
        print("-" * 60)
        print(f"{'Source':<20} {'Received':>10} {'Stored':>10} {'Quality':>10}")
        print("-" * 60)

        for name, data in summary["sources"].items():
            print(
                f"{name:<20} {data['received']:>10} {data['stored']:>10} "
                f"{data['quality_score']:>9.2f}%"
            )

        print("-" * 60)
        print(
            f"{'TOTAL':<20} {summary['total_records_received']:>10} "
            f"{summary['total_records_stored']:>10} "
            f"{summary['overall_quality_score']:>9.2f}%"
        )
        print("=" * 60 + "\n")
