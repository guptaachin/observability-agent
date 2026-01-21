# Agent Contract

**Feature**: Natural Language Metrics Querying  
**Version**: 1.0  
**Date**: January 21, 2026

---

## Purpose

This contract defines the interface for the LangGraph agent node that processes natural language queries and orchestrates the metrics query workflow.

---

## Node Interface

### Node Name
```
"metrics_agent"
```

### Input State

**Type**: `MetricsQueryState`

```python
class MetricsQueryState(TypedDict):
    user_query: str                    # User's natural language question
    parsed_query: Optional[MetricsQuery]  # Parsed query (None initially)
    result: Optional[MetricsQueryResult]  # Query result (None initially)
    error: Optional[QueryError]        # Error details (None if successful)
    processing_time_ms: float          # Execution timing
```

**Constraints**:
- `user_query` must be non-empty string
- Initial values: `parsed_query=None`, `result=None`, `error=None`
- `processing_time_ms` starts at 0

**Example Input**:
```python
{
    "user_query": "Show CPU usage for the last hour",
    "parsed_query": None,
    "result": None,
    "error": None,
    "processing_time_ms": 0.0
}
```

### Output State

**Type**: `MetricsQueryState` (same structure, updated fields)

After processing, the state must have exactly one of the following:
1. **Success**: `parsed_query` and `result` populated, `error=None`
2. **Failure**: `error` populated, `result=None`

**Example Success Output**:
```python
{
    "user_query": "Show CPU usage for the last hour",
    "parsed_query": MetricsQuery(...),
    "result": MetricsQueryResult(...),
    "error": None,
    "processing_time_ms": 245.3
}
```

**Example Error Output**:
```python
{
    "user_query": "Show anomalies in CPU usage",
    "parsed_query": None,
    "result": None,
    "error": QueryError(
        error_type="unsupported_operation",
        message="Anomaly detection is not supported",
        suggestion="Try asking for raw metric data instead"
    ),
    "processing_time_ms": 123.5
}
```

---

## Processing Steps

The node must execute the following steps in order:

### Step 1: Parse Natural Language Query

**Input**: `state["user_query"]`

**Action**: Use LLM to translate natural language to `MetricsQuery`

**Implementation**:
```python
llm = initialize_llm()
prompt = create_parsing_prompt(state["user_query"])
response = llm.invoke(prompt)
parsed_query = MetricsQuery(**json.loads(response))
```

**Success Criteria**:
- Response is valid JSON matching MetricsQuery schema
- All required fields populated
- Pydantic validation passes

**Failure Mode**: Set `error` with type `parsing_error`

### Step 2: Validate Query Parameters

**Input**: `parsed_query` from Step 1

**Action**: Verify metrics exist, time ranges valid, operations supported

**Implementation**:
```python
# Validate metric exists in Grafana
available_metrics = await grafana_client.get_available_metrics()
if parsed_query.metric_name not in available_metrics:
    raise MetricNotFoundError(...)

# Validate time range
if parsed_query.time_range.end_time <= parsed_query.time_range.start_time:
    raise InvalidTimeRangeError(...)

# Validate aggregation (caught by Pydantic)
# Validate no unsupported operations requested
```

**Success Criteria**:
- Metric exists in Grafana
- Time range is valid
- No unsupported operations in query

**Failure Mode**: Set `error` with appropriate error type

### Step 3: Execute Metrics Query

**Input**: `parsed_query` from Step 1

**Action**: Call Grafana metrics tool to retrieve data

**Implementation**:
```python
metrics_tool = create_grafana_metrics_tool()
raw_result = await metrics_tool.ainvoke({
    "metric_name": parsed_query.metric_name,
    "time_range": parsed_query.time_range,
    "aggregation": parsed_query.aggregation,
    "filters": parsed_query.filters
})
```

**Success Criteria**:
- Tool returns raw time-series data
- Data points are valid numbers with timestamps
- Data is non-empty OR explicitly marked as empty

**Failure Mode**: Set `error` with type `grafana_unavailable` or `invalid_query`

### Step 4: Format Result

**Input**: Raw data from Step 3

**Action**: Wrap in `MetricsQueryResult` with validation and statistics

**Implementation**:
```python
result = MetricsQueryResult(
    metric_name=parsed_query.metric_name,
    unit=get_metric_unit(parsed_query.metric_name),
    time_range=parsed_query.time_range,
    datapoints=[DataPoint(timestamp=ts, value=v) for ts, v in raw_data],
    datapoint_count=len(raw_data),
    statistics=calculate_stats(raw_data) if raw_data else None,
    is_empty=len(raw_data) == 0
)
```

**Success Criteria**:
- `MetricsQueryResult` passes Pydantic validation
- All fields populated correctly
- Statistics calculated if data non-empty

**Failure Mode**: Set `error` with type `invalid_query`

### Step 5: Return Updated State

**Output**: Updated `MetricsQueryState`

```python
return {
    **state,
    "parsed_query": parsed_query,
    "result": result,
    "error": error if steps failed else None,
    "processing_time_ms": elapsed_time
}
```

---

## Error Handling

### Error Processing Rules

1. **Parsing Errors** (Step 1 fails):
   ```
   error_type = "parsing_error"
   message = "Could not understand your query"
   suggestion = "[Show example query formats]"
   ```

2. **Validation Errors** (Step 2 fails):
   ```
   error_type = [specific: metric_not_found, invalid_time_range, unsupported_operation]
   message = "[Specific reason]"
   suggestion = "[How to fix]"
   ```

3. **Execution Errors** (Step 3 fails):
   ```
   error_type = "grafana_unavailable" or "invalid_query"
   message = "[Specific error from Grafana]"
   suggestion = "[Recovery steps]"
   ```

4. **Formatting Errors** (Step 4 fails):
   ```
   error_type = "invalid_query"
   message = "Could not format results"
   suggestion = "Contact administrator"
   ```

### Error Propagation

- **Do not suppress errors** - Always populate `error` field if any step fails
- **Do not retry automatically** - Return error to user for manual retry
- **Preserve details** - Include `details` field for logging (not shown to user)

---

## Node Dependencies

### External Tools

```python
llm: BaseLanguageModel
    - Used in Step 1 to parse natural language
    - Methods: invoke()
    - Must support function calling with JSON responses

grafana_metrics_tool: Tool
    - Used in Step 3 to query metrics
    - Method: ainvoke(parameters)
    - Returns: raw time-series data

grafana_client: GrafanaMetricsClient
    - Used in Step 2 to validate metric existence
    - Methods: get_available_metrics(), get_metric_unit()
    - Returns: List[str] or str
```

### Data Models

- `MetricsQueryState` - State type
- `MetricsQuery` - Parsed query
- `MetricsQueryResult` - Query result
- `QueryError` - Error representation
- `TimeRange`, `DataPoint`, `AggregationStats` - Supporting models

---

## State Guarantees

### Invariants

After node execution, exactly ONE of these must be true:

1. **Success Path**:
   - `parsed_query is not None`
   - `result is not None`
   - `error is None`

2. **Error Path**:
   - `error is not None`
   - `result is None`
   - `parsed_query` may or may not be populated

### Non-Invariants (Allowed to Vary)

- `parsing_time_ms` depends on network latency to LLM
- Exact statistics values depend on Grafana data
- Error messages can vary based on failure mode

---

## Extensibility Points

### Adding New Nodes (Future)

This node is designed to be extended without modification:

**Option 1: Visualization Node**
```
metrics_agent -> visualization_node -> END
```
Visualization node receives MetricsQueryResult and creates charts.

**Option 2: Anomaly Detection Node**
```
metrics_agent -> anomaly_detection_node -> END
```
Anomaly node analyzes result patterns.

**Option 3: Multi-Step Workflow**
```
metrics_agent -> enrichment_node -> explanation_node -> END
```
Additional context and interpretation without modifying metrics_agent.

### Key Design Pattern

- **Upstream nodes** (this node) produce standardized outputs (MetricsQueryState)
- **Downstream nodes** consume those outputs without modification
- **No state modification in downstream** - Add new fields if needed, don't change existing ones

---

## Testing Contract

### Unit Test Requirements

Node must be tested with:

1. **Valid Queries**:
   - Single metric queries
   - Queries with aggregation
   - Queries with filters
   - Various time ranges

2. **Invalid Queries**:
   - Non-existent metrics
   - Invalid time ranges
   - Unsupported operations
   - Malformed natural language

3. **Edge Cases**:
   - Very large time ranges
   - Very small time ranges
   - Empty result sets
   - Grafana unavailable
   - LLM parsing failures

### Integration Test Requirements

Node must be tested with:

1. **Real Grafana Connection**:
   - Actual metrics data
   - Real time ranges
   - Actual available metrics

2. **Real LLM**:
   - OpenAI or Ollama instance
   - Actual LLM response parsing

3. **End-to-End Workflow**:
   - User input → agent → Gradio display
   - Error handling end-to-end

---

## Performance Characteristics

### Target Performance

- **Step 1 (Parsing)**: < 2 seconds (LLM latency)
- **Step 2 (Validation)**: < 500ms (Grafana API call)
- **Step 3 (Execution)**: < 3 seconds (Grafana query execution)
- **Step 4 (Formatting)**: < 500ms (local processing)
- **Total**: < 6 seconds for typical query

### Performance Constraints

- **Memory**: No unbounded state growth
- **Connections**: Reuse HTTP client across invocations
- **Caching**: Cache available_metrics list (TTL: 5 minutes)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-21 | Initial contract |
