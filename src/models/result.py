"""
Data models for metric query results.

Defines DataPoint, AggregationStats, and MetricsQueryResult used to
represent time-series data returned from the Grafana MCP server. Includes
validation and convenience methods for summary and statistics.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from src.models.query import TimeRange


class DataPoint(BaseModel):
    """Single metric data point."""

    timestamp: datetime = Field(description="Timestamp of the data point")
    value: float = Field(description="Numeric value of the data point")

    @field_validator("value")
    @classmethod
    def value_is_finite(cls, v: float) -> float:
        """Ensure value is finite (not NaN or Inf)."""
        if not (-float("inf") < v < float("inf")):
            raise ValueError(f"Data point value must be finite, got {v}")
        return v


class AggregationStats(BaseModel):
    """Optional aggregation statistics."""

    min: float
    max: float
    mean: float
    median: float
    sum: float
    count: int


class MetricsQueryResult(BaseModel):
    """
    Represents time-series metric data from Grafana.

    Fields:
        metric_name: Name of the queried metric
        unit: Unit of measurement (e.g., '%', 'ms')
        time_range: TimeRange for returned data
        datapoints: List of DataPoint objects
        aggregation_applied: Optional aggregation applied
        statistics: Optional precomputed AggregationStats
        datapoint_count: Number of datapoints (kept in sync with datapoints)
        is_empty: True when no datapoints returned
    """

    metric_name: str = Field(description="Name of the queried metric")
    unit: str = Field(description="Unit of measurement (e.g., '%', 'ms', 'bytes')")
    time_range: TimeRange = Field(description="Actual time range of returned data")

    datapoints: List[DataPoint] = Field(description="List of (timestamp, value) pairs")

    aggregation_applied: Optional[str] = Field(
        default=None, description="Which aggregation was applied (if any)"
    )

    statistics: Optional[AggregationStats] = Field(
        default=None, description="Calculated statistics over the data points"
    )

    datapoint_count: int = Field(description="Number of data points returned")

    is_empty: bool = Field(default=False, description="True if no data available for this query")

    @field_validator("datapoints")
    @classmethod
    def sort_datapoints(cls, v: List[DataPoint]) -> List[DataPoint]:
        """Ensure datapoints are sorted by timestamp ascending."""
        return sorted(v, key=lambda dp: dp.timestamp)

    @model_validator(mode="after")
    def sync_counts(self) -> "MetricsQueryResult":
        """Sync datapoint_count and is_empty after model initialization."""
        # Ensure datapoints sorted already by field validator
        self.datapoint_count = len(self.datapoints)
        self.is_empty = self.datapoint_count == 0
        if self.statistics is None and not self.is_empty:
            # compute minimal statistics lazily
            try:
                self.statistics = self._calculate_stats()
            except Exception:
                # leave statistics as None if calculation fails
                self.statistics = None
        return self

    def _median(self, values: List[float]) -> float:
        """Compute median of a list of numeric values."""
        n = len(values)
        if n == 0:
            raise ValueError("Cannot compute median of empty list")
        values_sorted = sorted(values)
        mid = n // 2
        if n % 2 == 1:
            return values_sorted[mid]
        return (values_sorted[mid - 1] + values_sorted[mid]) / 2.0

    def _calculate_stats(self) -> AggregationStats:
        """Calculate statistics from datapoints."""
        if not self.datapoints:
            raise ValueError("Cannot calculate stats for empty data")
        values = [dp.value for dp in self.datapoints]
        return AggregationStats(
            min=min(values),
            max=max(values),
            mean=sum(values) / len(values),
            median=self._median(values),
            sum=sum(values),
            count=len(values),
        )

    @property
    def summary(self) -> str:
        """Generate human-readable summary of results."""
        if self.is_empty:
            return f"No data available for {self.metric_name} in the specified time range."

        stats = self.statistics or self._calculate_stats()
        return (
            f"{self.metric_name} - {self.datapoint_count} data points\n"
            f"  Range: {stats.min:.2f} to {stats.max:.2f} {self.unit}\n"
            f"  Average: {stats.mean:.2f} {self.unit}\n"
            f"  Time: {self.time_range.start_time} to {self.time_range.end_time}"
        )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "metric_name": "cpu_usage",
                    "unit": "%",
                    "time_range": {
                        "start_time": "2026-01-21T10:00:00",
                        "end_time": "2026-01-21T11:00:00",
                    },
                    "datapoints": [
                        {"timestamp": "2026-01-21T10:00:00", "value": 10.2},
                        {"timestamp": "2026-01-21T10:01:00", "value": 12.5},
                    ],
                }
            ]
        }
    }


class QueryError(BaseModel):
    """
    Represents an error encountered while parsing or executing a metrics query.

    This model is intended for use by the agent to convey actionable error
    information back to the user-facing layers.
    """

    error_type: Literal[
        "parsing_error",
        "metric_not_found",
        "invalid_time_range",
        "grafana_unavailable",
        "unsupported_operation",
        "invalid_query",
    ] = Field(description="Category of error")

    message: str = Field(description="Human-readable error message")

    suggestion: Optional[str] = Field(
        default=None, description="Suggestion for how to fix or rephrase the query"
    )

    details: Optional[str] = Field(
        default=None, description="Detailed error information for logging"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "error_type": "metric_not_found",
                    "message": "Metric 'disk_io' not found in Grafana",
                    "suggestion": "Try 'disk_write_rate', 'disk_read_rate', or 'disk_usage'",
                },
                {
                    "error_type": "parsing_error",
                    "message": "Could not understand your query",
                    "suggestion": "Try: 'Show [metric_name] for the [time_period]'",
                },
            ]
        }
    }
