# Feature Specification: Grafana Agent for Dashboard Discovery

**Feature Branch**: `001-grafana-agent`  
**Created**: 2026-01-23  
**Status**: Implemented  
**Input**: User description: "Enable engineers to successfully interact with grafana mcp via a single node agent for basic questions like give me list of all dashboards"

## Architecture Overview

The agent consists of four main components:

1. **config.py** (~40 lines) - Configuration via environment variables and LLM setup
2. **tools.py** (~100 lines) - MCP client using SSE transport to Grafana MCP server
3. **agent.py** (~150 lines) - Single-node LangGraph agent with LLM-based intent extraction
4. **main.py** (~35 lines) - Gradio chat UI

### Key Design Decisions

- **SSE Transport**: Connects to Grafana MCP server running in Docker at `http://localhost:8001`
- **LLM-Based Intent Extraction**: Uses structured prompts to extract search keywords from natural language
- **Multi-Keyword Search**: Supports semantic matching via multiple pipe-separated keywords (e.g., "node|system|health")
- **Minimal Dependencies**: Uses dataclasses instead of Pydantic, simple dict-based state

## User Scenarios & Testing *(mandatory)*

### User Story 1 - List All Dashboards (Priority: P1)

An engineer with access to the local Grafana instance can ask the agent "Show me all dashboards" and receive a clear, readable list of all dashboards available in their organization. This is the primary use case and the foundation for all agent interactions.

**Why this priority**: This is the core MVP feature. Without the ability to list dashboards, the agent cannot fulfill its basic purpose. This story establishes the end-to-end flow: user query → LLM intent extraction → MCP → Grafana → response.

**Independent Test**: Can be fully tested by starting the agent with `python -m src.main`, submitting the query "Show me all dashboards", and verifying that the response contains a formatted list of dashboards with titles.

**Acceptance Scenarios**:

1. **Given** the Grafana instance has 3+ dashboards, **When** the user asks "Show me all dashboards", **Then** the agent returns all dashboards with their titles in a numbered list format
2. **Given** the Grafana instance has no dashboards, **When** the user asks "Show me all dashboards", **Then** the agent returns "No dashboards found."
3. **Given** the agent is running, **When** the user asks "What dashboards are available?", **Then** the LLM interprets this as a list-all query (SEARCH:) and returns all dashboards

---

### User Story 2 - Search Dashboards by Topic (Priority: P2)

An engineer can search for dashboards using natural language queries like "Show me dashboards for system health" or "Find API monitoring dashboards". The LLM extracts relevant keywords and performs semantic matching.

**Why this priority**: This extends usability beyond exact name matching. The LLM translates user intent into multiple search keywords (e.g., "system health" → node|system|health|exporter|cpu|memory).

**Independent Test**: Can be tested by querying "Do we have dashboards to check system health?" and verifying that dashboards with names like "Node Exporter" are returned due to semantic keyword matching.

**Acceptance Scenarios**:

1. **Given** a dashboard named "Node Exporter Full" exists, **When** the user asks "Show me system health dashboards", **Then** the agent searches with keywords like node|system|health and returns matching dashboards
2. **Given** dashboards exist with differing names, **When** the user asks "Find dashboards with prod in the name", **Then** the agent returns only dashboards matching "prod"
3. **Given** no dashboards match the search, **When** the user searches, **Then** the agent returns "No dashboards found."

---

### User Story 3 - Graceful Error Handling (Priority: P2)

When the user submits an unsupported query or the Grafana instance is unavailable, the agent returns a clear error message explaining what went wrong.

**Why this priority**: Error paths are critical for usability. Clear error messages prevent user frustration.

**Independent Test**: Can be tested by submitting out-of-scope queries (e.g., "Analyze my metrics") and verifying the agent returns an appropriate message, or by stopping the MCP server and verifying connection error handling.

**Acceptance Scenarios**:

1. **Given** the user asks an out-of-scope question like "Analyze my metrics for anomalies", **When** the LLM processes it, **Then** it responds with OUT_OF_SCOPE and the agent returns "I can only list or search dashboards."
2. **Given** the MCP server is unreachable, **When** the user submits a query, **Then** the agent returns "Error connecting to Grafana: ..."
3. **Given** the user submits an empty query, **When** the agent processes it, **Then** it returns "Please provide a query about dashboards."

---

### Edge Cases

- **MCP Connection Timeouts**: SSE connection may timeout if MCP server is slow; errors are caught and reported
- **Special Characters**: Dashboard names with special characters are handled by the MCP server
- **Large Response**: No pagination implemented; all matching dashboards are returned
- **Partial Data**: Missing dashboard fields default to empty strings/lists

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Agent MUST accept natural language queries via Gradio chat interface and return responses in plain text
- **FR-002**: Agent MUST retrieve dashboards from Grafana via MCP server using SSE transport
- **FR-003**: Agent MUST format dashboard responses as a numbered list showing title, folder, and tags
- **FR-004**: Agent MUST use LLM to extract search keywords from natural language queries
- **FR-005**: Agent MUST support multi-keyword search (pipe-separated) for semantic matching
- **FR-006**: Agent MUST return clear error messages when queries are out of scope (via LLM OUT_OF_SCOPE response)
- **FR-007**: Agent MUST handle MCP connection errors gracefully with user-friendly messages
- **FR-008**: Agent MUST use only the Grafana MCP server for all Grafana interactions; no direct API calls
- **FR-009**: Agent MUST be configurable via environment variables (MCP_SERVER_URL, OPENAI_API_KEY, OPENAI_MODEL)
- **FR-010**: Agent MUST use OpenAI LLM (gpt-4-turbo by default) for intent extraction
- **FR-011**: Agent MUST implement a single-node LangGraph graph with dict-based state

### Key Entities

- **Dashboard**: Dataclass with uid, title, folder (optional), tags (optional), url (optional). Retrieved from Grafana via MCP.
- **Config**: Dataclass with mcp_server_url, openai_api_key, openai_model. Loaded from environment variables.
- **GrafanaMCP**: Client class using SSE transport to call MCP tools (search_dashboards, list_tools).
- **Agent State**: Simple dict with "query" and "response" keys.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An engineer can submit a natural language query about dashboards and receive a response within 5 seconds
- **SC-002**: Queries for listing or searching dashboards return accurate information from Grafana (no fabrication)
- **SC-003**: Out-of-scope queries (metric analysis, predictions, modifications) are rejected via LLM OUT_OF_SCOPE detection
- **SC-004**: Agent can be started by running `python -m src.main` after setting OPENAI_API_KEY and having MCP server running
- **SC-005**: Connection failures and errors are caught and reported as user-friendly messages
- **SC-006**: Semantic search queries (e.g., "system health") match relevant dashboards via multi-keyword expansion

## Implementation Details

### Files

```
src/
├── config.py    # Config dataclass, load_config(), create_llm()
├── tools.py     # GrafanaMCP class with SSE transport
├── agent.py     # LangGraph agent with SYSTEM_PROMPT
└── main.py      # Gradio chat UI launcher
```

### Configuration

Environment variables (can be set in `.env` file):
- `MCP_SERVER_URL` - MCP server endpoint (default: http://localhost:8001)
- `OPENAI_API_KEY` - Required for LLM
- `OPENAI_MODEL` - Model name (default: gpt-4-turbo)

### MCP Connection

Uses `mcp.client.sse.sse_client` to connect to `{MCP_SERVER_URL}/sse`. The MCP server runs in Docker:
```bash
docker run -e GRAFANA_URL=... -e GRAFANA_API_KEY=... -p 8001:8001 mcp/grafana:latest
```

### LLM Intent Extraction

The agent uses a structured SYSTEM_PROMPT that instructs the LLM to output one of:
- `SEARCH: keyword1|keyword2|keyword3` - For searching with multiple semantic keywords
- `SEARCH:` - For listing all dashboards
- `OUT_OF_SCOPE: explanation` - For unsupported requests

### Response Format

```
Found N dashboard(s):

1. Dashboard Title
   Folder: folder_name
   Tags: tag1, tag2
```

## Assumptions

- Grafana MCP server is running at the configured endpoint (default localhost:8001)
- MCP server has proper Grafana credentials configured
- User queries are in English
- OpenAI API key is valid and has sufficient quota
- All dashboards are readable by the MCP server's configured user

## Non-Goals

Explicitly out of scope:

- Metrics querying or visualization
- Anomaly detection or statistical analysis
- Dashboard modification or creation
- Ollama or other LLM providers (OpenAI only)
- Multi-turn conversation memory
- Multi-node agent orchestration
- Authentication beyond MCP server configuration
- Session persistence
