# Contract: Metrics Query Tool

**Feature**: 001-natural-language-metrics  
**Date**: 2026-01-20  
**Type**: LangChain Tool Interface

## Overview

The Metrics Query Tool is a LangChain tool that provides a stable interface for querying metrics from the Grafana MCP server. This contract defines the tool's input/output interface to ensure extensibility and stability.

## Tool Interface

### Tool Name
`query_metrics`

### Tool Description
Queries metric data from the observability system. Accepts structured query parameters and returns time-series metric data.

### Input Schema

```python
{
    "type": "object",
    "properties": {
        "metric_name": {
            "type": "string",
            "description": "Name of the metric to query (e.g., 'cpu_usage', 'memory_usage')"
        },
        "time_range": {
            "type": "object",
            "properties": {
                "start": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Start time for the query (ISO 8601 format)"
                },
                "end": {
                    "type": "string",
                    "format": "date-time",
                    "description": "End time for the query (ISO 8601 format)"
                }
            },
            "required": ["start", "end"]
        },
        "filters": {
            "type": "object",
            "description": "Additional filters (e.g., host, service, environment)",
            "additionalProperties": True,
            "default": {}
        },
        "aggregation": {
            "type": "string",
            "enum": ["average", "sum", "min", "max", "count"],
            "description": "Aggregation type if specified",
            "default": None
        }
    },
    "required": ["metric_name", "time_range"]
}
```

### Output Schema

**Success Response**:
```python
{
    "metric_name": "cpu_usage",
    "data_points": [
        {
            "timestamp": "2026-01-20T09:30:00Z",
            "value": 45.2
        },
        # ... more data points
    ],
    "metadata": {
        "unit": "percent",
        "description": "CPU usage percentage"
    }
}
```

**Error Response**:
```python
{
    "error": "Metric 'xyz' not found",
    "error_type": "metric_not_found"  # or "connection_error", "invalid_query", etc.
}
```

## Behavior Specification

### Valid Inputs

- `metric_name`: Must be a valid metric name that exists in the observability system
- `time_range.start`: Must be a valid ISO 8601 datetime string
- `time_range.end`: Must be a valid ISO 8601 datetime string, after `start`
- `filters`: Optional dict with filter key-value pairs
- `aggregation`: Optional string from enum values

### Error Conditions

1. **Metric Not Found**: `metric_name` does not exist in observability system
   - Error type: `metric_not_found`
   - Response: `{"error": "Metric '{metric_name}' not found", "error_type": "metric_not_found"}`

2. **Invalid Time Range**: `start` is after `end` or range is invalid
   - Error type: `invalid_query`
   - Response: `{"error": "Invalid time range: start must be before end", "error_type": "invalid_query"}`

3. **Connection Error**: Cannot connect to Grafana MCP server
   - Error type: `connection_error`
   - Response: `{"error": "Cannot connect to observability system", "error_type": "connection_error"}`

4. **Query Timeout**: Query takes too long to execute
   - Error type: `timeout_error`
   - Response: `{"error": "Query timed out", "error_type": "timeout_error"}`

### Performance Expectations

- Typical query: < 5 seconds
- Maximum query duration: 30 seconds (configurable timeout)
- Time range limit: Maximum 1 year (configurable)

## Stability Guarantees

This contract is stable and will not change in ways that break existing implementations. Future extensions may:
- Add optional fields to input schema (backward compatible)
- Add optional fields to output schema (backward compatible)
- Add new error types (consumers should handle unknown error types gracefully)

Breaking changes (removing fields, changing required fields) will require a new version of this contract.

## Usage Example

```python
from langchain.tools import Tool

tool = query_metrics_tool()

# Tool invocation
result = tool.invoke({
    "metric_name": "cpu_usage",
    "time_range": {
        "start": "2026-01-20T09:30:00Z",
        "end": "2026-01-20T10:30:00Z"
    }
})

# Result handling
if "error" in result:
    # Handle error
    print(f"Error: {result['error']}")
else:
    # Process data points
    for point in result["data_points"]:
        print(f"{point['timestamp']}: {point['value']}")
```

## Future Extensions

This interface is designed to support future capabilities:
- Multi-metric queries (extend `metric_name` to accept list)
- Advanced aggregations (extend `aggregation` enum)
- Metric metadata queries (add new tool method)
- Visualization hints (add optional `format` parameter)

All extensions will maintain backward compatibility with this contract.
