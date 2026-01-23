# Grafana MCP Tool Interface Contract

**Purpose**: Define the interface for wrapping Grafana MCP server as a callable LangChain tool.

**Phase**: 1 (Design & Contracts)  
**Location**: `src/tools.py`

---

## Tool Name & Description

**Name**: `grafana`

**Description**: `"Fetch dashboard metadata from Grafana MCP server. Use to list available dashboards or retrieve dashboard details."`

---

## Input Contract

**Type**: JSON-serializable dict

**Parameters**:
| Parameter | Type | Required | Valid Values | Description |
|-----------|------|----------|--------------|-------------|
| `action` | str | ✅ | `"list_dashboards"` | Action to perform on Grafana API |
| `filters` | dict | ❌ | See examples below | Optional filters (reserved for future; currently ignored) |

**Examples**:

```python
# List all dashboards
tool.invoke({
    "action": "list_dashboards"
})

# Future: Search dashboards by tag (not implemented in MVP)
tool.invoke({
    "action": "list_dashboards",
    "filters": {"tag": "prod"}
})
```

---

## Output Contract

**Type**: `dict` with structure:

```python
{
    "success": bool,
    "data": list[dict] | None,  # List of Dashboard objects or null if error
    "error": str | None,         # Error message or null if success
    "metadata": {
        "mcp_server_reachable": bool,
        "response_time_ms": int,
        "org_id": int             # Grafana org that was queried
    }
}
```

**Example (Success)**:
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "uid": "abc123def456",
            "title": "System Metrics",
            "description": "CPU, memory, disk usage",
            "tags": ["prod", "infrastructure"],
            "url": "/d/abc123def456/system-metrics",
            "updated": "2026-01-23T14:30:00Z",
            "folder_id": 5
        },
        {
            "id": 2,
            "uid": "xyz789uvw012",
            "title": "Application Logs",
            "description": null,
            "tags": ["prod", "app"],
            "url": "/d/xyz789uvw012/app-logs",
            "updated": "2026-01-23T12:00:00Z",
            "folder_id": null
        }
    ],
    "error": null,
    "metadata": {
        "mcp_server_reachable": true,
        "response_time_ms": 350,
        "org_id": 1
    }
}
```

**Example (Empty List)**:
```json
{
    "success": true,
    "data": [],
    "error": null,
    "metadata": {
        "mcp_server_reachable": true,
        "response_time_ms": 280,
        "org_id": 1
    }
}
```

**Example (Error)**:
```json
{
    "success": false,
    "data": null,
    "error": "Cannot connect to Grafana MCP server. Is it running on localhost:3000?",
    "metadata": {
        "mcp_server_reachable": false,
        "response_time_ms": 5000,  # Timeout
        "org_id": 1
    }
}
```

---

## Implementation Details

### Subprocess Management (MCP Communication)

**Pattern**:
1. Spawn Grafana MCP subprocess (configured in `.env` or environment variables)
2. Send JSON request to subprocess stdin: `{"action": "list_dashboards"}`
3. Read JSON response from subprocess stdout
4. Parse response, format as tool output contract
5. Log to LangSmith callback
6. Return to caller (LLM in agent node)

**Process Lifecycle**:
- **Spawn on first tool invocation** or reuse persistent process (TBD in implementation)
- **Timeout**: 8 seconds for MCP subprocess communication (leaves 2s buffer before agent timeout)
- **Error Handling**: Catch subprocess errors, JSON parse errors, timeouts; return structured error response

### Configuration Integration

Tool initialization reads from:
1. Environment variables (highest priority): `GRAFANA_URL`, `GRAFANA_USERNAME`, `GRAFANA_PASSWORD`, `GRAFANA_ORG_ID`
2. `.env` file (via `python-dotenv`)
3. Hardcoded defaults for local development

**Example**:
```python
import os
from src.config import GrafanaConfig

config = GrafanaConfig()  # Loads from env vars, .env, defaults
tool = GrafanaToolMCP(
    grafana_url=config.url,
    grafana_username=config.username,
    grafana_password=config.password,
    grafana_org_id=config.org_id
)
```

---

## Error Codes & Messages

| Error Scenario | Message | Handling |
|---|---|---|
| MCP server not reachable | "Cannot connect to Grafana. Ensure MCP server is running on {url}." | Return error; agent shows to user |
| MCP timeout (>8s) | "Grafana request timed out. Please try again." | Return error; agent shows to user |
| Authentication failed | "Authentication failed. Check GRAFANA_USERNAME and GRAFANA_PASSWORD." | Return error; check logs |
| Invalid action | "Unknown action: {action}. Supported: list_dashboards" | Return error; agent should not call invalid actions |
| Malformed Grafana response | "Unexpected response from Grafana. Please check MCP server logs." | Return error; check MCP server logs |

---

## Observability / LangSmith Logging

Tool must be registered with LangSmith callbacks:
- **Input logged**: `action`, `filters` (no credentials)
- **Output logged**: `success`, `data` (dashboards list), `error`, `metadata`
- **Timing**: `response_time_ms` captured
- **Errors**: Full error messages logged for debugging

Example LangSmith trace:
```
Agent Node
  ├─ LLM Call (gpt-4): "Show me all dashboards"
  └─ Tool Call: grafana
      ├─ Input: {"action": "list_dashboards"}
      ├─ Output: {"success": true, "data": [...], "metadata": {...}}
      └─ Duration: 350ms
```

---

## Testing Strategy

**Unit Tests** (focus per Principle V):
- Test subprocess spawning and JSON communication
- Test error handling (timeout, malformed response, auth failure)
- Test empty dashboard list
- Mock MCP server for fast test execution

**Integration Tests**:
- Test with real Grafana MCP server (if available in test environment)
- Verify response format matches contract

---

## Future Extensions

**Reserved for Phase 2**:
- `action: "get_dashboard"` — Retrieve single dashboard details
- `action: "search_dashboards"` — Filter by tag, folder, or name
- Pagination support for large dashboard lists
- Metrics querying (different action, different response schema)

**Design Consideration**: Tool interface is stable; new actions can be added without refactoring existing calls.

---

## Implementation Checklist

- [ ] Define tool class inheriting from LangChain's `Tool` or `BaseTool`
- [ ] Implement `_run()` method matching input/output contracts
- [ ] Spawn MCP subprocess with configuration from `GrafanaConfig`
- [ ] Implement JSON communication (send request, read response, parse)
- [ ] Add error handling for timeout, subprocess errors, JSON parse errors
- [ ] Log all tool invocations to LangSmith callback
- [ ] Write unit tests for normal case and error cases
- [ ] Document expected Grafana MCP server response format
- [ ] Add docstring with examples
