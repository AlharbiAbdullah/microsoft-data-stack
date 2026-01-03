"""Tests for quality tracker."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from src.quality.tracker import IngestionMetrics, QualityTracker


class TestIngestionMetrics:
    """Tests for IngestionMetrics dataclass."""

    def test_quality_score_calculation(self):
        """Test quality score is calculated correctly."""
        metrics = IngestionMetrics(
            source_name="test",
            source_type="api",
            records_received=100,
            records_stored=95,
            records_rejected=5,
        )
        assert metrics.quality_score == 95.0

    def test_quality_score_zero_received(self):
        """Test quality score when no records received."""
        metrics = IngestionMetrics(
            source_name="test",
            source_type="api",
            records_received=0,
            records_stored=0,
        )
        assert metrics.quality_score == 100.0

    def test_status_success(self):
        """Test status is success when all records stored."""
        metrics = IngestionMetrics(
            source_name="test",
            source_type="api",
            records_received=100,
            records_stored=100,
            records_rejected=0,
        )
        assert metrics.status == "success"

    def test_status_partial(self):
        """Test status is partial when some records rejected."""
        metrics = IngestionMetrics(
            source_name="test",
            source_type="api",
            records_received=100,
            records_stored=95,
            records_rejected=5,
        )
        assert metrics.status == "partial"

    def test_status_failed(self):
        """Test status is failed when error occurs."""
        metrics = IngestionMetrics(
            source_name="test",
            source_type="api",
            error_message="Connection failed",
        )
        assert metrics.status == "failed"


class TestQualityTracker:
    """Tests for QualityTracker class."""

    def test_tracker_initialization(self):
        """Test tracker initializes with correct defaults."""
        tracker = QualityTracker(pipeline_name="test_pipeline")

        assert tracker.pipeline_name == "test_pipeline"
        assert tracker.batch_id is not None
        assert len(tracker.metrics) == 0

    def test_start_extraction(self):
        """Test starting extraction creates metrics entry."""
        tracker = QualityTracker()
        tracker.start_extraction("api_products", "api")

        assert "api_products" in tracker.metrics
        assert tracker.metrics["api_products"].source_type == "api"
        assert tracker.metrics["api_products"].extraction_started_at is not None

    def test_complete_extraction(self):
        """Test completing extraction records count."""
        tracker = QualityTracker()
        tracker.start_extraction("api_products", "api")
        tracker.complete_extraction("api_products", 100)

        assert tracker.metrics["api_products"].records_received == 100
        assert tracker.metrics["api_products"].extraction_completed_at is not None

    def test_complete_load(self):
        """Test completing load records counts and rejections."""
        tracker = QualityTracker()
        tracker.start_extraction("api_products", "api")
        tracker.complete_extraction("api_products", 100)
        tracker.start_load("api_products")
        tracker.complete_load(
            "api_products",
            records_stored=95,
            records_rejected=5,
            rejection_reasons={"invalid_price": 3, "null_title": 2},
        )

        metrics = tracker.metrics["api_products"]
        assert metrics.records_stored == 95
        assert metrics.records_rejected == 5
        assert metrics.rejection_reasons["invalid_price"] == 3

    def test_get_summary(self):
        """Test summary aggregation."""
        tracker = QualityTracker()

        # Add first source
        tracker.start_extraction("source1", "api")
        tracker.complete_extraction("source1", 100)
        tracker.complete_load("source1", 95)

        # Add second source
        tracker.start_extraction("source2", "csv")
        tracker.complete_extraction("source2", 50)
        tracker.complete_load("source2", 50)

        summary = tracker.get_summary()

        assert summary["sources_count"] == 2
        assert summary["total_records_received"] == 150
        assert summary["total_records_stored"] == 145
        assert summary["overall_quality_score"] == pytest.approx(96.67, rel=0.01)

    def test_record_error(self):
        """Test error recording."""
        tracker = QualityTracker()
        tracker.start_extraction("api_products", "api")
        tracker.record_error("api_products", "Connection timeout")

        assert tracker.metrics["api_products"].error_message == "Connection timeout"
        assert tracker.metrics["api_products"].status == "failed"
