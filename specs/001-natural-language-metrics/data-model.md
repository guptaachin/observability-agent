# Data Model: Natural Language Metric Queries

**Feature**: 001-natural-language-metrics  
**Date**: 2026-01-20

## Overview

This feature operates on a stateless, request-response model. No persistent data storage is required. The data model focuses on the transient data structures that flow through the system during a single query cycle.

## Entities

### NaturalLanguageQuery

Represents the user's input question in natural language.

**Attributes**:
- `query_text` (string, required): The raw natural language question from the user
- `timestamp` (datetime, optional): When the query was received (for logging/debugging)

**Validation Rules**:
- Must not be empty
- Maximum length: 1000 characters (reasonable limit for chat interface)

**Example**:
```python
{
    "query_text": "Show CPU usage for the last hour",
    "timestamp": "2026-01-20T10:30:00Z"
}
```

### ParsedMetricQuery

Represents the structured query parameters extracted from natural language.

**Attributes**:
- `metric_name` (string, required): Name of the metric to query (e.g., "cpu_usage", "memory_usage")
- `time_range` (TimeRange, required): Start and end times for the query
- `filters` (dict, optional): Additional filters (e.g., host, service, environment)
- `aggregation` (string, optional): Aggregation type if specified (e.g., "average", "sum", "max")

**Validation Rules**:
- `metric_name` must not be empty
- `time_range.start` must be before `time_range.end`
- `time_range` duration must be reasonable (not more than 1 year, not negative)

**Example**:
```python
{
    "metric_name": "cpu_usage",
    "time_range": {
        "start": "2026-01-20T09:30:00Z",
        "end": "2026-01-20T10:30:00Z"
    },
    "filters": {},
    "aggregation": None
}
```

### TimeRange

Represents a time period for metric queries.

**Attributes**:
- `start` (datetime, required): Start time (inclusive)
- `end` (datetime, required): End time (inclusive)

**Validation Rules**:
- `start` must be before `end`
- Duration must be positive
- Maximum duration: 1 year (configurable limit)
- Minimum duration: 1 second

**Example**:
```python
{
    "start": "2026-01-20T09:30:00Z",
    "end": "2026-01-20T10:30:00Z"
}
```

### MetricData

Represents the raw metric data retrieved from the observability system.

**Attributes**:
- `metric_name` (string, required): Name of the metric
- `data_points` (list[DataPoint], required): Time-series data points
- `metadata` (dict, optional): Additional metadata (unit, description, etc.)

**Validation Rules**:
- `data_points` must not be empty (if query succeeded)
- Each data point must have valid timestamp and value

**Example**:
```python
{
    "metric_name": "cpu_usage",
    "data_points": [
        {"timestamp": "2026-01-20T09:30:00Z", "value": 45.2},
        {"timestamp": "2026-01-20T09:31:00Z", "value": 47.8},
        # ... more points
    ],
    "metadata": {
        "unit": "percent",
        "description": "CPU usage percentage"
    }
}
```

### DataPoint

Represents a single metric value at a specific time.

**Attributes**:
- `timestamp` (datetime, required): When this value was recorded
- `value` (float, required): The metric value

**Validation Rules**:
- `timestamp` must be valid datetime
- `value` must be numeric (float or int)

**Example**:
```python
{
    "timestamp": "2026-01-20T09:30:00Z",
    "value": 45.2
}
```

### AgentResponse

Represents the formatted response returned to the user.

**Attributes**:
- `response_text` (string, required): Human-readable response text
- `has_data` (boolean, required): Whether response contains metric data
- `error` (string, optional): Error message if query failed

**Validation Rules**:
- If `has_data` is true, `response_text` must contain metric information
- If `error` is present, `has_data` must be false

**Example** (success):
```python
{
    "response_text": "CPU usage for the last hour:\n09:30 - 45.2%\n09:31 - 47.8%\n...",
    "has_data": True,
    "error": None
}
```

**Example** (error):
```python
{
    "response_text": "I couldn't find a metric matching your query. Please check the metric name and try again.",
    "has_data": False,
    "error": "Metric 'xyz' not found"
}
```

## State Transitions

### Query Processing Flow

1. **NaturalLanguageQuery** → (LLM interpretation) → **ParsedMetricQuery**
2. **ParsedMetricQuery** → (MCP tool execution) → **MetricData**
3. **MetricData** → (formatting) → **AgentResponse**

### Error States

- **Interpretation Error**: NaturalLanguageQuery → ErrorResponse (invalid query format)
- **Metric Not Found**: ParsedMetricQuery → ErrorResponse (metric doesn't exist)
- **MCP Error**: ParsedMetricQuery → ErrorResponse (connection/query failure)
- **Validation Error**: Any stage → ErrorResponse (invalid parameters)

## Relationships

- **NaturalLanguageQuery** → (1:1) → **ParsedMetricQuery** (interpretation)
- **ParsedMetricQuery** → (1:1) → **MetricData** (execution)
- **MetricData** → (1:1) → **AgentResponse** (formatting)

All relationships are transient (exist only during single request-response cycle).

## Notes

- No persistent storage: All entities are in-memory only
- No relationships across requests: Each query is independent (stateless)
- Validation happens at each stage to fail fast
- Error responses follow same structure as success responses for consistency
