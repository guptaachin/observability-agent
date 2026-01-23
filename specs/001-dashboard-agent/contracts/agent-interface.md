# Agent Node Interface Contract

**Purpose**: Define the input/output contract for the single-node LangGraph agent.

**Phase**: 1 (Design & Contracts)  
**Location**: `src/agent.py`

---

## Node Name

`"agent"` — The sole processing node in the single-node graph.

---

## Input Contract

**Type**: `AgentState` (pydantic BaseModel)

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | str | ✅ | User's natural language input (e.g., "Show me all dashboards") |
| `context` | str | ✅ | System context (role, instructions, scope boundaries) |

**Example**:
```python
state = AgentState(
    query="Show me all dashboards",
    context="You are a Grafana dashboard assistant..."
)
```

**Validation**:
- `query` must be non-empty and ≤500 characters
- `context` must contain scope boundaries (metrics, anomalies, recommendations)

---

## Processing Steps

1. **Parse User Intent**: Call LLM with (query, context) → extract intent and scope
2. **Validate Scope**: Is intent within supported capabilities (list dashboards)?
3. **Execute Tool or Return Error**:
   - If valid: Call `grafana_mcp_tool.invoke()` → Dashboard list
   - If invalid: Return error message based on scope violation
4. **Format Response**: Markdown list for valid, error text for invalid
5. **Populate Metadata**: Record LLM model, response time, MCP connectivity

---

## Output Contract

**Type**: `AgentState` with populated `response` field

**Fields** (updated from input):
| Field | Type | Description |
|-------|------|-------------|
| `response` | str | Formatted response (Markdown for dashboards, plain text for errors) |
| `metadata` | dict | Processing info: `llm_model`, `response_time_ms`, `mcp_server_reachable` |

**Example (Success)**:
```python
output = AgentState(
    query="Show me all dashboards",
    context="...",
    response="""
# Available Dashboards

1. **System Metrics** (ID: 1)
   - Tags: prod, infrastructure
   - Last updated: 2026-01-23

2. **Application Logs** (ID: 2)
   - Tags: prod, app
   - Last updated: 2026-01-23
""",
    metadata={
        "llm_model": "gpt-4",
        "response_time_ms": 1240,
        "mcp_server_reachable": True
    }
)
```

**Example (Error)**:
```python
output = AgentState(
    query="What's the CPU trend?",
    context="...",
    response="I can list dashboards, but metrics queries are not yet supported. Please use the Grafana UI or Prometheus API directly.",
    metadata={
        "llm_model": "gpt-4",
        "response_time_ms": 840,
        "mcp_server_reachable": True
    }
)
```

---

## Error Handling

**Errors Caught by Node**:

| Scenario | Handling |
|----------|----------|
| MCP server unreachable | Return error: "Cannot connect to Grafana. Ensure MCP server is running." |
| LLM API unreachable | Return error: "LLM service is unavailable. Please try again." |
| Empty dashboard list | Return: "No dashboards found." (valid response, not an error) |
| Query timeout (>10s) | Return error: "Query took too long. Please try again." |
| Unsupported query (metrics, anomalies) | Return error from scope detection in step 2 |

**Observability**: All errors are logged via LangSmith callback.

---

## Performance Constraints

- **Response Time**: <5 seconds for typical dashboard query (SC-002)
- **Timeout**: Hard timeout at 10 seconds; return error if exceeded
- **Memory**: No state accumulation between invocations (stateless)

---

## Extension Points (Future)

For future multi-node expansion:
- **New Node**: `"metrics"` for time-series queries (add conditional edge: `if scope == "metrics" then route to "metrics" node`)
- **New Node**: `"anomaly_detection"` for anomaly queries
- **Tool Interface**: Remains stable—new tools added as needed, same invocation pattern

**No refactoring of this node required** when adding new functionality.

---

## Implementation Checklist

- [ ] Define `AgentState` pydantic model with query, context, response, metadata fields
- [ ] Create `process_query_node` function matching signature: `(AgentState) -> AgentState`
- [ ] Initialize LLM with system prompt (includes scope boundaries)
- [ ] Wrap Grafana MCP tool as LangChain Tool (see `grafana-mcp.md` contract)
- [ ] Add error handling for MCP server, LLM timeouts
- [ ] Log all state changes to LangSmith
- [ ] Test node in isolation with hardcoded test cases
- [ ] Measure response time for typical queries
