# API Contracts: Grafana Agent

**Phase 1 Output** | **Status**: Complete | **Date**: 2026-01-23

## Overview

This document specifies the contracts (interfaces) between components of the Grafana Agent system. All contracts are implementation-agnostic; programming language and framework details are deferred to Phase 2.

---

## 1. LangGraph Node Contract

**Node Name**: `agent_node`  
**Type**: State processing node (no branching)  
**Responsibility**: Accept user query, invoke LLM, return formatted response

### Input State

```python
{
    "query": str,                    # User's raw natural language input
    "context": Optional[Dict],       # Reserved for future metadata
}
```

### Output State

```python
{
    "query": str,                    # (preserved from input)
    "intent": str,                   # Parsed intent: "list" | "filter" | "get_info" | "invalid" | "out_of_scope"
    "response": str,                 # Human-readable formatted response
    "status": str,                   # "success" | "error" | "out_of_scope"
    "error_code": Optional[str],     # Machine-readable error identifier
    "data": Optional[List[Dict]],    # Structured dashboard data if success
}
```

### Processing Logic

```
1. Receive query
2. Call LLM with system prompt (constrains scope, guides intent parsing)
3. LLM decides which Grafana tool to call (or error/out_of_scope)
4. If tool call:
   a. Call GrafanaTool.list_dashboards() or .search_dashboards()
   b. Format results into human-readable text
   c. Return status="success", response="formatted text", data=[...]
5. If error:
   a. Catch exception
   b. Return status="error", response="error message", error_code="..."
6. If out_of_scope:
   a. LLM identifies unsupported request
   b. Return status="out_of_scope", response="explanation"
```

### Error Handling

| Scenario | Status | Error Code | Response |
|----------|--------|-----------|----------|
| Grafana MCP unreachable | "error" | "grafana_connection_error" | "Unable to connect to Grafana. Please check your configuration." |
| Query is empty/invalid | "invalid" | "invalid_query" | "Please provide a query about dashboards." |
| Query asks for metrics analysis | "out_of_scope" | "unsupported_capability" | "I can only retrieve dashboard information, not analyze metrics." |
| MCP returns partial data | "error" | "partial_data_error" | "Grafana returned incomplete data. Please try again." |

---

## 2. Grafana Tool Contract

**Tool Class**: `GrafanaMCPTool`  
**Responsibility**: Communicate with Grafana exclusively via MCP server; return structured dashboard data

### Initialization

```python
class GrafanaMCPTool:
    def __init__(self, config: GrafanaConfig):
        """
        Args:
            config: Contains MCP server connection details
                - mcp_server_command: str (docker)
                - mcp_args: List[str] (docker run args)
                - grafana_url: str (http://localhost:3000)
                - grafana_username: str
                - grafana_password: str
                - grafana_org_id: int
        """
        self.mcp_client = MCPClient(config)
        self.mcp_client.start()
```

### Methods

#### list_dashboards()

```python
async def list_dashboards() -> List[DashboardMetadata]:
    """
    Retrieve all dashboards from Grafana via MCP server.
    
    Returns:
        List of dashboard objects with metadata:
        - id: str (UUID)
        - title: str
        - uid: str
        - updated: datetime (ISO 8601)
        - tags: List[str]
        - folderTitle: Optional[str]
        - orgId: int
    
    Raises:
        GrafanaConnectionError: MCP server unreachable
        GrafanaAuthError: Authentication failed
        GrafanaDataError: Malformed response from Grafana
    """
```

#### search_dashboards(query: str) -> List[DashboardMetadata]

```python
async def search_dashboards(query: str) -> List[DashboardMetadata]:
    """
    Search dashboards by name, tags, or metadata.
    
    Args:
        query: Search string (e.g., "prod", "monitoring", "api")
    
    Returns:
        Filtered list of dashboards matching query
    
    Raises:
        GrafanaConnectionError
        GrafanaDataError
    """
```

#### get_dashboard(uid: str) -> DashboardMetadata

```python
async def get_dashboard(uid: str) -> DashboardMetadata:
    """
    Retrieve single dashboard by UID.
    
    Args:
        uid: Dashboard unique identifier
    
    Returns:
        Dashboard object with full metadata
    
    Raises:
        GrafanaConnectionError
        GrafanaNotFoundError: Dashboard not found
        GrafanaDataError
    """
```

### Exception Hierarchy

```python
GrafanaError (base)
├── GrafanaConnectionError
│   └── MCPServerUnreachable
│   └── MCPServerTimeout
├── GrafanaAuthError
│   └── InvalidCredentials
│   └── UnauthorizedOrg
└── GrafanaDataError
    └── MalformedResponse
    └── PartialData
```

---

## 3. LLM System Prompt Contract

**Purpose**: Guide LLM behavior; constrain scope; define tool-calling patterns

```
You are an assistant that helps engineers retrieve information about Grafana dashboards.

YOUR CAPABILITIES:
- List all available dashboards in the organization
- Search/filter dashboards by name or tags
- Retrieve dashboard metadata (title, last updated, tags, folder)

YOUR CONSTRAINTS:
- You CANNOT analyze metrics, detect anomalies, or explain metric behavior
- You CANNOT make recommendations or provide predictions
- You CANNOT modify dashboards or create new ones
- You only retrieve and display data exactly as stored in Grafana
- You do not make inferences or add context beyond the data

USER QUERY:
{query}

TASK:
1. Understand what the user is asking
2. Determine if the request is within your capabilities
3. If YES: Call the appropriate Grafana tool (list_dashboards, search_dashboards, get_dashboard) and format results clearly
4. If NO: Explain what you can do instead

RESPONSE FORMAT:
- Use plain text (no JSON, no markdown code blocks)
- Use bullet points or numbered lists for dashboard lists
- Be concise and clear
- If results are empty, say "No dashboards found"
```

---

## 4. Configuration Contract

**Purpose**: Specify how agent is configured; environment variables and optional YAML

### Environment Variables

```bash
# Required
GRAFANA_URL=http://localhost:3000
GRAFANA_USERNAME=mopadmin
GRAFANA_PASSWORD=moppassword
GRAFANA_ORG_ID=1

# LLM Configuration
LLM_PROVIDER=ollama  # or "openai"
OPENAI_API_KEY=sk-...  # Required if LLM_PROVIDER=openai
OPENAI_MODEL=gpt-4-turbo  # Optional; default provided
OLLAMA_BASE_URL=http://localhost:11434  # Required if LLM_PROVIDER=ollama
OLLAMA_MODEL=llama2  # Optional; default provided

# Optional
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
AGENT_TIMEOUT=30  # Query timeout in seconds
```

### Config File Schema (YAML)

```yaml
grafana:
  url: http://localhost:3000
  username: mopadmin
  password: moppassword
  org_id: 1

llm:
  provider: ollama  # or openai
  openai:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4-turbo
  ollama:
    base_url: http://localhost:11434
    model: llama2

logging:
  level: INFO
  format: json  # or plain

agent:
  timeout: 30  # seconds
  max_results: 100  # max dashboards to return
```

### Configuration Priority (lowest to highest)

1. Hardcoded defaults in code
2. YAML config file (if exists)
3. Environment variables (override all)

---

## 5. Gradio Interface Contract

**Purpose**: Define user-facing chat interface

### Input

- **Type**: Text (single line)
- **Validation**: Non-empty string
- **Example**: "Show me all dashboards"

### Output

- **Type**: Text (multi-line)
- **Format**: Plain text with formatting (line breaks, bullet points)
- **Example**:
  ```
  I found 3 dashboards:

  1. Production API Metrics
     Last updated: 2026-01-23
     Tags: prod, api, monitoring

  2. Database Performance
     Last updated: 2026-01-21
     Tags: database, prod

  3. Service Health
     Last updated: 2026-01-22
     Tags: services, observability
  ```

### Interaction Flow

```
User Input → Agent Node → Gradio Display → User Reads Response
                            ↓
                    (message appended to chat history)
                    (user can submit next query)
```

### Chat History

- Previous messages displayed in chat window
- Each user query and agent response shown as separate messages
- No persistence between sessions (stateless)

---

## 6. Error Response Contract

**Purpose**: Specify consistent error messages for common failure scenarios

### Error Response Format

```python
{
    "status": "error" | "out_of_scope" | "invalid",
    "response": str,  # User-facing explanation
    "error_code": str,  # Machine-readable code
}
```

### Predefined Error Messages

| Error Code | User-Facing Message | Recovery Suggestion |
|------------|-------------------|-------------------|
| `grafana_connection_error` | "Unable to connect to Grafana. Please check your configuration." | Check Grafana Docker container is running; verify GRAFANA_URL in config |
| `grafana_auth_error` | "Authentication failed with Grafana. Check your username and password." | Verify GRAFANA_USERNAME, GRAFANA_PASSWORD in .env file |
| `invalid_query` | "Please provide a query about dashboards (e.g., 'Show me all dashboards')." | Rephrase query to be more specific |
| `unsupported_capability` | "I can only retrieve dashboard information. I cannot [requested capability]." | Request something within my capabilities |
| `partial_data_error` | "Grafana returned incomplete data. Please try again." | Retry the query; contact Grafana admin if persists |
| `llm_timeout` | "Query took too long to process. Please try again." | Retry; check LLM provider availability |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-23 | Initial contracts for MVP (single-node agent, Grafana MCP, Gradio UI) |

---

## Future Extensions

The following contracts are candidates for future phases (not in MVP):

- **Multi-node Agent Contract**: State flow between multiple nodes
- **Caching Contract**: Cache layer for frequently accessed dashboards
- **Logging/Metrics Contract**: Structured logging and observability
- **API Endpoint Contract**: RESTful HTTP API (if server deployment needed)
- **WebSocket Contract**: Real-time updates (if streaming responses needed)

All future contracts must maintain backward compatibility with current single-node interface.
