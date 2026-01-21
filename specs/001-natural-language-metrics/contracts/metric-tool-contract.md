# Metrics Query Tool Contract

**Feature**: Natural Language Metrics Querying  
**Version**: 1.0  
**Date**: January 21, 2026

---

## Purpose

This contract defines the interface for the LangChain tool that executes metric queries against Grafana.

---

## Tool Definition

### Tool Name
```
"query_grafana_metrics"
```

### Tool Description

For LLM Function Calling:
```
"Query metrics from Grafana. Returns time-series metric data for a specified metric 
and time range. Supports optional aggregation."
```

---

## Input Parameters

### Parameter Schema (JSON Schema)

```json
{
  "type": "object",
  "properties": {
    "metric_name": {
      "type": "string",
      "description": "Name of the metric to query (e.g., 'cpu_usage', 'memory_utilization', 'request_latency')"
    },
    "start_time": {
      "type": "string",
      "format": "date-time",
      "description": "Query start time (ISO 8601 format, e.g., '2026-01-21T10:00:00Z')"
    },
    "end_time": {
      "type": "string",
      "format": "date-time",
      "description": "Query end time (ISO 8601 format, e.g., '2026-01-21T11:00:00Z')"
    },
    "aggregation": {
      "type": "string",
      "enum": ["avg", "max", "min", "sum"],
      "description": "Optional aggregation function to apply to the data"
    },
    "filters": {
      "type": "object",
      "description": "Optional key-value filters for the metric (e.g., {'instance': 'server-1'})",
      "additionalProperties": {"type": "string"}
    }
  },
  "required": ["metric_name", "start_time", "end_time"],
  "additionalProperties": false
}
```

### Python Signature

```python
@tool
def query_grafana_metrics(
    metric_name: str = Field(
        description="Name of the metric to query"
    ),
    start_time: str = Field(
        description="Query start time (ISO 8601)"
    ),
    end_time: str = Field(
        description="Query end time (ISO 8601)"
    ),
    aggregation: Optional[str] = Field(
        default=None,
        description="Optional aggregation (avg, max, min, sum)"
    ),
    filters: Optional[Dict[str, str]] = Field(
        default=None,
        description="Optional filters"
    )
) -> str:
    """Query metrics from Grafana."""
    pass
```

### Parameter Validation

| Parameter | Validation | Error Response |
|-----------|-----------|-----------------|
| `metric_name` | Non-empty string, exists in Grafana | `QueryError(error_type="metric_not_found")` |
| `start_time` | Valid ISO 8601 datetime | `QueryError(error_type="invalid_time_range")` |
| `end_time` | Valid ISO 8601, after start_time | `QueryError(error_type="invalid_time_range")` |
| `aggregation` | One of: avg, max, min, sum, or None | `QueryError(error_type="invalid_query")` |
| `filters` | Dict of string keys/values | `QueryError(error_type="invalid_query")` |

---

## Return Value

### Success Response

**Type**: String (formatted for human readability)

**Format**: Markdown-style text representation of metric data

```
cpu_usage (%)
Time: 2026-01-21 10:00:00 to 2026-01-21 11:00:00
Data Points: 60

Statistics:
  Min:    5.2%
  Max:    45.8%
  Mean:   22.1%
  Median: 18.9%
  Sum:    1,326%

Data (first 10 points):
  10:01:00 - 5.2%
  10:02:00 - 6.1%
  10:03:00 - 7.3%
  10:04:00 - 8.9%
  10:05:00 - 10.2%
  10:06:00 - 11.5%
  10:07:00 - 12.8%
  10:08:00 - 13.6%
  10:09:00 - 14.2%
  10:10:00 - 15.1%
```

### Error Response

**Type**: String with error message

**Format**:
```
ERROR: [error_type]
Message: [user-friendly description]
Suggestion: [how to fix or rephrase]
```

**Example**:
```
ERROR: metric_not_found
Message: Metric 'disk_io' not found in Grafana
Suggestion: Available metrics include: cpu_usage, memory_utilization, disk_usage, disk_read_rate, disk_write_rate
```

---

## Internal Implementation

## Internal Implementation

### MCP Server Integration

The tool uses the **Grafana MCP server** as the backend. The MCP server is configured to run in Docker and provides methods for querying Grafana metrics.

```python
from mcp.client import MCPClient
from pydantic import BaseModel

class GrafanaMCPClient:
    """Client for Grafana MCP server."""
    
    def __init__(self, mcp_config: dict):
        self.client = MCPClient(mcp_config)
    
    async def query_metrics(
        self,
        metric_name: str,
        start_time: str,
        end_time: str,
        aggregation: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query Grafana via MCP server.
        
        The MCP server handles:
        - Authentication with Grafana
        - API request formation
        - Response parsing
        
        Returns:
            List of data points with timestamp and value
        """
        result = await self.client.call_tool(
            "query_metrics",
            {
                "metric_name": metric_name,
                "start_time": start_time,
                "end_time": end_time,
                "aggregation": aggregation
            }
        )
        return result

@tool
async def query_grafana_metrics(
    metric_name: str,
    start_time: str,
    end_time: str,
    aggregation: Optional[str] = None,
    filters: Optional[Dict[str, str]] = None
) -> str:
    """Query metrics from Grafana via MCP server."""
    try:
        # Get MCP client
        mcp_client = get_grafana_mcp_client()
        
        # Query via MCP server
        data_points = await mcp_client.query_metrics(
            metric_name, start_time, end_time, aggregation
        )
        
        # Format result
        return format_result(data_points)
        
    except Exception as e:
        return format_error(...)
```

### MCP Server Configuration

The Grafana MCP server is configured in Docker:

```json
{
  "mcpServers": {
    "grafana": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--network",
        "host",
        "-e", "GRAFANA_URL",
        "-e", "GRAFANA_USERNAME",
        "-e", "GRAFANA_PASSWORD",
        "-e", "GRAFANA_ORG_ID",
        "mcp/grafana:latest",
        "-t", "stdio"
      ],
      "env": {
        "GRAFANA_URL": "http://localhost:3000",
        "GRAFANA_USERNAME": "mopadmin",
        "GRAFANA_PASSWORD": "moppassword",
        "GRAFANA_ORG_ID": "1"
      }
    }
  }
}
```

### Query Execution Steps

1. **Receive parameters** (metric_name, time range, etc.)
2. **Validate parameters** (above)
3. **Call MCP server** (via MCPClient)
4. **MCP server** calls Grafana HTTP API (internal to MCP server)
5. **Parse response** from MCP server
6. **Calculate statistics** (min, max, mean, etc.)
7. **Format for output** (human-readable string)

### Error Handling

```python
async def query_grafana_metrics(...) -> str:
    try:
        # Validate parameters
        validate_parameters(...)
        
        # Query Grafana
        data_points = await grafana_client.query_metrics(...)
        
        # Format result
        return format_result(...)
        
    except MetricNotFoundError as e:
        return format_error("metric_not_found", str(e), suggest_available_metrics())
    except InvalidTimeRangeError as e:
        return format_error("invalid_time_range", str(e), suggest_valid_format())
    except GrafanaUnavailableError as e:
        return format_error("grafana_unavailable", str(e), "Check Grafana is running")
    except Exception as e:
        return format_error("invalid_query", str(e), "Contact administrator")
```

---

## Behavior Specification

### Standard Query

**Given**: 
```python
metric_name="cpu_usage"
start_time="2026-01-21T10:00:00Z"
end_time="2026-01-21T11:00:00Z"
```

**When**: Tool is called

**Then**: Returns time-series data for CPU usage in the specified hour

### Query with Aggregation

**Given**:
```python
metric_name="request_latency"
start_time="2026-01-20T00:00:00Z"
end_time="2026-01-21T00:00:00Z"
aggregation="avg"
```

**When**: Tool is called

**Then**: Returns hourly average of request latency over 24 hours

### Query with Filters

**Given**:
```python
metric_name="cpu_usage"
start_time="2026-01-21T10:00:00Z"
end_time="2026-01-21T11:00:00Z"
filters={"instance": "prod-server-1"}
```

**When**: Tool is called

**Then**: Returns CPU usage for only the prod-server-1 instance

### Query with No Data

**Given**: Metric in valid time range with no data points

**When**: Tool is called

**Then**: 
```
cpu_usage (%)
Time: 2026-01-21 10:00:00 to 2026-01-21 11:00:00
Data Points: 0

No data available for this metric in the specified time range.
```

### Invalid Metric

**Given**:
```python
metric_name="nonexistent_metric"
```

**When**: Tool is called

**Then**:
```
ERROR: metric_not_found
Message: Metric 'nonexistent_metric' not found in Grafana
Suggestion: Available metrics include: cpu_usage, memory_utilization, disk_usage, ...
```

### Invalid Time Range

**Given**:
```python
start_time="2026-01-21T11:00:00Z"
end_time="2026-01-21T10:00:00Z"  # End before start
```

**When**: Tool is called

**Then**:
```
ERROR: invalid_time_range
Message: end_time (2026-01-21T10:00:00Z) must be after start_time (2026-01-21T11:00:00Z)
Suggestion: Use format: start_time < end_time, both in ISO 8601 format
```

### Grafana Unavailable

**Given**: Grafana server is down

**When**: Tool is called

**Then**:
```
ERROR: grafana_unavailable
Message: Cannot connect to Grafana at http://localhost:3000
Suggestion: Verify Grafana is running: docker ps | grep grafana
```

---

## Performance Requirements

| Aspect | Target | Constraint |
|--------|--------|-----------|
| Query Execution | < 2 seconds | Excludes network latency |
| Data Point Limit | 10,000 points | Larger queries rejected |
| Time Range Limit | 90 days max | Longer ranges rejected |
| Concurrent Queries | 5 | Connection pool limit |

### Caching Strategy

```python
# Cache available metrics
@cached(ttl=300)  # 5 minutes
async def get_available_metrics() -> List[str]:
    pass

# Cache metric metadata (units, descriptions)
@cached(ttl=3600)  # 1 hour
async def get_metric_metadata(metric_name: str) -> Dict:
    pass
```

---

## Integration with Agent

### Called From

This tool is called by the agent's `metrics_agent` node during Step 3 (Query Execution).

### Input From Agent

The agent passes a `MetricsQuery` object (already validated):

```python
query = MetricsQuery(
    metric_name="cpu_usage",
    time_range=TimeRange(start_time=..., end_time=...),
    aggregation="avg",
    filters={"instance": "server-1"}
)

# Tool is called with unpacked parameters
result_str = await query_grafana_metrics(
    metric_name=query.metric_name,
    start_time=query.time_range.start_time.isoformat(),
    end_time=query.time_range.end_time.isoformat(),
    aggregation=query.aggregation,
    filters=query.filters
)
```

### Output to Agent

Tool returns string that agent processes:
- If success: Parse into `MetricsQueryResult`
- If error: Parse error details into `QueryError`

---

## Testing Contract

### Unit Tests

Tool must be tested with:

1. **Valid Queries**:
   - Standard metric queries
   - Queries with aggregation
   - Queries with filters
   - Various time ranges

2. **Invalid Queries**:
   - Non-existent metrics
   - Invalid time ranges
   - Invalid aggregations
   - Non-existent filter values

3. **Edge Cases**:
   - Very large time ranges
   - Very small time ranges (single second)
   - Empty result sets
   - Metrics with special characters in name

### Integration Tests

Tool must be tested against:

1. **Real Grafana**:
   - Actual available metrics
   - Actual metric data
   - Actual time ranges

2. **Mock Grafana**:
   - Consistent error scenarios
   - Network failures
   - Slow responses

---

## Future Extensions

### Planned Additions

1. **Percentile queries** (e.g., p50, p95, p99)
2. **Derivative queries** (rate of change)
3. **Multiple metrics** (query multiple metrics in one call)
4. **Label-based queries** (query by labels instead of metric name)

### Extension Pattern

New parameters can be added to the tool signature:

```python
@tool
def query_grafana_metrics(
    metric_name: str,
    start_time: str,
    end_time: str,
    aggregation: Optional[str] = None,
    filters: Optional[Dict[str, str]] = None,
    percentile: Optional[str] = None,  # NEW
    derivative: Optional[bool] = None,  # NEW
) -> str:
    """..."""
```

No changes needed to agent or tool registration - just parameter handling.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-21 | Initial tool contract |
