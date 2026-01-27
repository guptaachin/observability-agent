# Data Model: Grafana Agent for Dashboard Discovery

**Phase 1 Output** | **Status**: Complete | **Date**: 2026-01-23

## Core Entities

### 1. Dashboard

**Description**: Represents a Grafana dashboard object. Retrieved from Grafana via MCP server.

**Attributes** (implementation-agnostic):

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string (UUID) | Yes | Unique identifier from Grafana |
| `title` | string | Yes | Dashboard display name |
| `uid` | string | Yes | URL-safe unique identifier |
| `folderTitle` | string | Optional | Folder containing dashboard (if organized in folders) |
| `tags` | List[string] | Optional | Labels/tags for categorization |
| `updated` | datetime (ISO 8601) | Yes | Last modification timestamp |
| `created` | datetime (ISO 8601) | Optional | Creation timestamp |
| `orgId` | integer | Yes | Organization ID (for multi-tenant Grafana) |
| `starred` | boolean | Optional | Whether dashboard is starred by current user |
| `isStarred` | boolean | Optional | Alternative field name (Grafana API variation) |

**Validation Rules**:
- `title` must not be empty or whitespace-only
- `uid` must be non-empty alphanumeric string
- `updated` must be valid ISO 8601 datetime
- `orgId` must be positive integer

**Relationships**:
- Dashboard may belong to a Folder (optional)
- Dashboard contains multiple Panels (not modeled here; agent doesn't modify panels)

**State Transitions**: N/A (agent is read-only)

**Example** (JSON from MCP/API):
```json
{
  "id": "1",
  "uid": "prod-api-dashboard",
  "title": "Production API Metrics",
  "folderTitle": "Production",
  "tags": ["prod", "api", "monitoring"],
  "updated": "2026-01-23T10:30:00Z",
  "created": "2025-11-15T14:22:00Z",
  "orgId": 1,
  "starred": true
}
```

---

### 2. User Query

**Description**: Represents the engineer's natural language question about dashboards.

**Attributes** (extracted from user input):

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `raw_input` | string | Yes | Exact text from user |
| `intent` | Enum | Yes | Parsed intent: `"list"`, `"filter"`, `"get_info"`, `"invalid"`, `"out_of_scope"` |
| `filters` | Dict[string, string] | Optional | Extracted key-value filters (e.g., `{"name": "prod", "tag": "monitoring"}`) |
| `target_dashboard` | string | Optional | If query asks about specific dashboard (extracted UID or title) |
| `timestamp` | datetime | Yes | When query was submitted |

**Validation Rules**:
- `raw_input` must not be empty
- `intent` must be one of the defined enum values
- If `intent == "out_of_scope"`, error message should be provided in response
- If `intent == "invalid"`, prompt user for valid query format

**Intent Mapping** (LLM interprets):

| Intent | Example Queries |
|--------|-----------------|
| `"list"` | "Show me all dashboards", "What dashboards do we have?", "List dashboards" |
| `"filter"` | "Show me dashboards with 'prod' in the name", "List dashboards tagged with 'monitoring'" |
| `"get_info"` | "When was [dashboard] last updated?", "Tell me about the API dashboard" |
| `"invalid"` | "", "(nonsense)", "asdf" |
| `"out_of_scope"` | "Analyze my metrics", "Detect anomalies", "Predict failures" |

**Example** (parsed from raw input "Show me dashboards with prod in the name"):
```json
{
  "raw_input": "Show me dashboards with prod in the name",
  "intent": "filter",
  "filters": {
    "name": "prod"
  },
  "target_dashboard": null,
  "timestamp": "2026-01-23T15:45:30Z"
}
```

---

### 3. Agent Response

**Description**: Formatted output returned to user after processing query.

**Attributes**:

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | Enum | Yes | Result status: `"success"`, `"error"`, `"out_of_scope"` |
| `formatted_output` | string | Yes | Human-readable text for user |
| `data` | Union[List[Dashboard], null] | Optional | Structured data if status == "success" |
| `error_code` | string | Optional | Machine-readable error (e.g., `"grafana_connection_error"`) |
| `llm_reasoning` | string | Optional | Raw LLM response for debugging |

**Status Definitions**:

| Status | Meaning | Example Output |
|--------|---------|-----------------|
| `"success"` | Query fulfilled; dashboards returned | "Found 3 dashboards: 1) Production API, 2) Database Metrics, 3) Service Health" |
| `"error"` | Query valid but system error | "Unable to connect to Grafana. Please check your configuration." |
| `"out_of_scope"` | Query requests unsupported capability | "I can only retrieve dashboard information. I cannot analyze metrics or detect anomalies." |

**Validation Rules**:
- `formatted_output` must not be empty
- If `status == "success"`, `data` should contain List[Dashboard]
- If `status == "error"`, `error_code` should be set
- Formatted output should be plain text (no JSON, no code blocks)

**Example** (for query "Show me all dashboards"):
```json
{
  "status": "success",
  "formatted_output": "I found 3 dashboards:\n1. Production API Metrics (last updated: 2026-01-23)\n2. Database Performance (last updated: 2026-01-21)\n3. Service Health Overview (last updated: 2026-01-22)",
  "data": [
    { "id": "1", "title": "Production API Metrics", "uid": "prod-api", "updated": "2026-01-23T10:30:00Z", "orgId": 1 },
    { "id": "2", "title": "Database Performance", "uid": "db-perf", "updated": "2026-01-21T14:22:00Z", "orgId": 1 },
    { "id": "3", "title": "Service Health Overview", "uid": "svc-health", "updated": "2026-01-22T09:15:00Z", "orgId": 1 }
  ],
  "error_code": null,
  "llm_reasoning": "[raw LLM output for debugging]"
}
```

---

## Agent State Schema

**LangGraph State Dictionary** (passed between nodes):

```python
state = {
    "query": str,                    # User's raw input query
    "intent": Optional[str],         # Parsed intent (from LLM or query parser)
    "filters": Optional[Dict],       # Extracted filters
    "grafana_response": Optional[List[Dashboard]],  # Raw data from MCP
    "response": str,                 # Formatted text for user display
    "status": str,                   # "success", "error", "out_of_scope"
    "error_code": Optional[str],     # Machine-readable error
}
```

---

## Data Flow Diagram

```
User Input (text)
    ↓
LangGraph Node
    ├─ Extract query intent (LLM system prompt guides)
    ├─ Call Grafana Tool (MCP client)
    │   └─ MCP Server
    │       └─ Grafana API
    ├─ Filter/format results
    └─ Return formatted response
    ↓
Gradio UI (display formatted_output)
```

---

## Constraints & Assumptions

**Data Constraints**:
- Maximum dashboards returned: No hard limit (but UX degrades if > 100 listed at once)
- Maximum query length: Reasonable (< 2000 characters; LLM window limits)
- Character encoding: UTF-8 for all strings

**Assumptions**:
- All dashboards are readable by authenticated user (no row-level permissions filtering)
- Dashboard metadata from Grafana is always consistent (no partial data)
- Timestamps are in UTC (ISO 8601 format)
- Dashboard UIDs are unique within organization

**Scalability Notes**:
- MVP: Tested with 0-10 dashboards (reasonable for demo)
- Small production: 10-100 dashboards (acceptable UX)
- Large production: 100+ dashboards (may need pagination or search refinement in future)

---

## Future Extensions (Not in MVP)

The following entities/attributes are candidates for future phases:

- **Dashboard Panels**: Individual visualizations within a dashboard (for future "metric correlation" feature)
- **Alerts**: Alert rules associated with dashboards (for future "alert status" feature)
- **Annotations**: Timeline events/notes (for future "context" feature)
- **Datasources**: Data sources used by dashboards (for future "dependency analysis" feature)
- **Versions**: Dashboard version history (for future "change tracking" feature)

These are deferred until multi-node agent capabilities are designed.

---

## JSON Schema (for API contracts)

See [contracts/](contracts/) for formal OpenAPI/GraphQL schemas.
