# Research: Grafana Dashboard Agent

**Phase**: 0 (Research & Clarification)  
**Date**: 2026-01-23  
**Status**: In Progress  
**Goal**: Resolve technology choices and validate best practices for single-node LangGraph agent, Gradio interface, and Grafana MCP integration.

---

## Research Questions & Findings

### 1. LangGraph Architecture for Single-Node, Future-Proof Design

**Question**: How to structure a single-node LangGraph graph that is minimal yet extensible for future multi-node expansion?

**Decision**: Single StateGraph with one node executing the core agent logic.

**Rationale**: 
- LangGraph's StateGraph pattern is the simplest, most flexible foundation. A single node named "agent" or "process_query" receives user input and produces formatted output.
- No ceremony—no routing logic, no conditional edges (yet). All complexity is inside the node function.
- Future expansion is straightforward: add new nodes for metrics queries, visualization, anomaly detection without refactoring the existing node.
- Easier for learners to understand: clear input → function → output pattern.

**Alternatives Considered**:
- Multi-node graph from the start (rejected: violates Minimalism principle; adds unnecessary complexity for MVP)
- Tool-calling agent with dynamic node creation (rejected: LangGraph's tool-calling pattern requires multi-step reasoning; simpler for single-query dashboard lookup to be deterministic)
- Direct LLM calls without LangGraph (rejected: loses observability; LangGraph + LangSmith integration is core learning objective)

**Implementation Pattern**:
```python
# Pseudocode
from langgraph.graph import StateGraph

class AgentState(BaseModel):
    query: str
    context: str  # "You are a Grafana agent..."
    response: str

graph = StateGraph(AgentState)
graph.add_node("agent", process_query_node)
graph.set_entry_point("agent")
graph.set_finish_point("agent")
```

---

### 2. Grafana MCP Tool Integration with LangChain

**Question**: Best practices for wrapping the Grafana MCP tool in LangChain-compatible format?

**Decision**: Create a wrapper class that implements LangChain's `Tool` interface, handling MCP stdio communication under the hood.

**Rationale**:
- Grafana MCP server is a subprocess communicating via stdio. LangChain's `Tool` abstraction is ideal for wrapping external systems.
- Wrapper hides MCP protocol details from the agent—agent just calls `tool.invoke({"query": "..."})`  and receives structured results.
- LangSmith automatically logs tool invocations when integrated, giving full observability.
- Clean separation: `tools.py` module is the single source of truth for Grafana integration.

**Alternatives Considered**:
- Direct MCP subprocess calls in agent (rejected: couples agent logic to protocol; harder to test and observe)
- LangChain's built-in `MCP` tool loader (rejected: unclear maturity; wrapping ourselves gives control and learning value)

**Implementation Pattern**:
```python
from langchain.tools import Tool
from pydantic import BaseModel

class DashboardQuery(BaseModel):
    action: str  # e.g., "list_dashboards"

class GrafanaMCPTool(Tool):
    name = "grafana"
    description = "Fetch dashboard metadata from Grafana"
    
    def _run(self, action: str) -> dict:
        # Spawn MCP subprocess, send request, receive response
        return self._invoke_mcp(action)
```

---

### 3. Configuration Management: Environment Variables + Defaults

**Question**: Recommended pattern for loading environment variables, config files, and defaults in Python?

**Decision**: Use `pydantic.Settings` for config schema validation + `python-dotenv` for loading `.env` files.

**Rationale**:
- `pydantic.Settings` provides type-safe, validated configuration with automatic environment variable parsing.
- `.env` file support (via `python-dotenv`) allows committed defaults without exposing secrets.
- Clear priority: env var > `.env` file > hardcoded default.
- Pydantic's validation catches misconfigurations early (e.g., invalid Grafana URL, missing API key).

**Alternatives Considered**:
- ConfigParser (rejected: no validation; verbose syntax)
- YAML config files (rejected: adds parsing dependency; environment variables sufficient per spec)
- Hardcoded defaults + env var override (rejected: no validation; less clear)

**Implementation Pattern**:
```python
from pydantic_settings import BaseSettings

class GrafanaConfig(BaseSettings):
    url: str = "http://localhost:3000"  # default
    username: str = "mopadmin"
    password: str  # required, from env
    org_id: int = 1
    
    class Config:
        env_file = ".env"
        env_prefix = "GRAFANA_"
```

---

### 4. LangSmith Integration for Observability

**Question**: How to automatically log agent interactions without code clutter?

**Decision**: Use `LangSmith` client as context manager; initialize in `main.py` before agent execution.

**Rationale**:
- LangSmith is LangGraph's native observability backend. Integration is as simple as setting an environment variable (`LANGSMITH_API_KEY`) and initializing the callback.
- All LLM calls, tool invocations, and agent state transitions are automatically logged to the LangSmith dashboard.
- Zero additional code in the agent—callbacks are registered globally.
- Perfect for learning: see exactly what the agent is doing at each step.

**Alternatives Considered**:
- Manual logging (rejected: verbose; doesn't capture LLM/tool details automatically)
- OpenTelemetry (rejected: overkill for MVP; LangSmith is simpler and integrated with LangGraph)

**Implementation Pattern**:
```python
import os
from langsmith import Client

# Automatic if LANGSMITH_API_KEY is set
client = Client()

# Then run agent—all interactions are logged
result = app.invoke({"query": "Show me all dashboards"})
```

---

### 5. Gradio Chat Interface Best Practices

**Question**: Best practices for building a chat interface that displays agent responses cleanly?

**Decision**: Use `gr.ChatInterface` component with custom formatting function.

**Rationale**:
- `gr.ChatInterface` is the simplest Gradio component for chat workflows. It handles message history, submit button, and layout automatically.
- Custom formatting function accepts user message and returns agent response—no boilerplate.
- Supports markdown in responses, allowing clean formatting of dashboard lists.
- LLM provider agnostic—passes through user text to agent, displays agent output as-is.

**Alternatives Considered**:
- `gr.Blocks` (rejected: verbose; excessive control for chat use case)
- `gr.Interface` with custom HTML (rejected: hard to maintain; loses chat semantics)

**Implementation Pattern**:
```python
import gradio as gr

def chat_fn(message, history):
    result = agent.invoke({"query": message})
    return result["response"]

demo = gr.ChatInterface(
    chat_fn,
    examples=["Show me all dashboards", "What dashboards exist?"],
    title="Grafana Dashboard Agent",
)
demo.launch()
```

---

### 6. Error Handling Patterns: Route Invalid Queries to Meaningful Responses

**Question**: How to route invalid queries to meaningful error responses via LLM?

**Decision**: Dual-layer approach:
1. **First layer (Structural)**: Validate configuration, MCP server connection on startup.
2. **Second layer (Semantic)**: Include instructions in system prompt to recognize out-of-scope queries (metrics, anomalies, recommendations) and return explicit error messages.

**Rationale**:
- Structural validation fails fast: if Grafana is unreachable, user knows immediately (before opening chat).
- Semantic validation via prompt is natural: the LLM is already interpreting text, so we can guide it to recognize limits.
- Clear error message format helps users understand what's supported: "I can list dashboards. For metrics queries, use Prometheus API directly."
- Per Principle IV (Accuracy & Clarity), errors must be explicit and actionable.

**Alternatives Considered**:
- Hard-coded keyword matching (rejected: brittle; misses variations like "predict anomaly")
- Attempt query execution and catch MCP errors (rejected: unreliable; doesn't prevent misunderstandings)

**Implementation Pattern**:
```python
SYSTEM_PROMPT = """
You are a Grafana dashboard assistant. You can only list dashboards.
If asked about:
- Metrics or time series data: "I can list dashboards, but metrics queries are not yet supported. Please use the Grafana UI or Prometheus API."
- Anomaly detection: "I cannot detect anomalies. Please use Grafana's alerting rules."
- Recommendations: "I can show you dashboards, but I don't make recommendations."

For dashboard queries, use the 'grafana' tool with action='list_dashboards'.
"""
```

---

## Summary of Decisions

| Area | Decision | Rationale |
|------|----------|-----------|
| **Graph Structure** | Single StateGraph, one "agent" node | Minimal, extensible, clear learning model |
| **MCP Integration** | LangChain Tool wrapper | Clean abstraction, automatic observability, testable |
| **Configuration** | pydantic.Settings + .env file | Type-safe, validated, environment-friendly |
| **Observability** | LangSmith client (automatic) | Native LangGraph integration, zero-code setup |
| **UI** | Gradio ChatInterface | Simplest chat component, markdown support |
| **Error Handling** | Structural validation + semantic prompt | Fast failure + natural language boundaries |

---

## Validation Against Constitution

✅ All research decisions align with six constitutional principles:
- **I. Purpose**: LangGraph + LangSmith teaches core agentic patterns
- **II. Minimalism**: All choices favor simplicity (single-node, no multi-step reasoning, basic config)
- **III. Extensibility**: Each component (graph, tools, config) is designed for future expansion
- **IV. Accuracy & Clarity**: MCP wrapper + error handling ensure real data and clear boundaries
- **V. Pragmatic Testing**: Choices emphasize learning (LangSmith observability) over test coverage
- **VI. Simplistic Structure**: Flat module design, no nested packages

---

## Next Phase

Phase 1 (Design & Contracts) will use these research findings to define:
- Data models (Dashboard, Query entities)
- API contracts (agent node input/output, MCP tool interface)
- Quickstart guide with concrete examples
- Configuration schema (JSON schema for validation)

**Phase 1 Deliverables**: data-model.md, contracts/, quickstart.md
