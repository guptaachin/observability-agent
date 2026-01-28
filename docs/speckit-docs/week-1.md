# Week 1: Observability Agent - Constitution & Specification

## Constitution

**Command**: `/speckit.constitution`

Design the constitution around the following principles:

- **Purpose**: Learn how to build agentic applications and explore their use in observability
- **Minimalism**: Implement only core functionality; no insights or autonomous actions
- **Extensibility**: Establish a safe foundation for future expansion
- **Accuracy & Clarity**: Outputs must reflect real data and be easy to understand
- **For Education & Learning**: Tests can be skipped, focus on learning core features
- **Simplistic Directory Structure**: Create nested code directories only when absolutely necessary
- **Minimal code**: Create minimal code to complete the project.

---

## Specification

**Command**: `/speckit.specify`

### Goal

Enable engineers to successfully interact with grafana mcp via a single node agent for basic questions like give me list of all dashboards.

### Example Questions

- "Show me all dashboards"

### Non-Goals

- No metrics querying now.
- No anomaly detection
- No explanations or interpretations of metric behavior
- No recommendations or corrective actions
- No autonomous behavior
- No historical memory or context across interactions

### Constraints

- The capability must operate on top of the existing observability stack running in docker.
- The capability must not require changes to metric ingestion or storage
- The experience should be simple enough for someone cloning the repository to try without prior context

---

## Implementation Plan

**Command**: `/speckit.plan`

### High-Level Flow

1. User submits a natural language query via a chat-style interface
2. The query is routed through a simple agent workflow
3. Results are returned to the user in a readable format

### User Interface
- Use Gradio to provide a lightweight, local chat interface
- Support user text input and text-based responses from the agent
- The interface is for demo and exploration purposes only

### Agent Architecture

- Use LangGraph to define the agent workflow
- Limit to create one node agent in langgraph
- Implement the agent as a single-node graph
- The single node is responsible for:
  - Receiving the user query
  - Calling the language model to interpret the query
  - Formatting and returning the response
- Talking to grafana can only be done via Grafana MCP server. Do not use APIs

### Configuration

Grafana MCP server connection details must be configurable. Grafana MCP server runs in Docker and is configured in Cursor using this structure:

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
        "-e",
        "GRAFANA_URL",
        "-e",
        "GRAFANA_USERNAME",
        "-e",
        "GRAFANA_PASSWORD",
        "-e",
        "GRAFANA_ORG_ID",
        "mcp/grafana:latest",
        "-t",
        "stdio"
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

Configuration should be provided via environment variables or a config file. No credentials or endpoints should be hardcoded. Reasonable defaults may be provided for local development.

### LLM Support

We add support for both OpenAI and Ollama.

### Error Handling

- Handle invalid or unsupported queries gracefully
- Return clear error messages to the user when a query cannot be fulfilled
- Do not attempt automatic correction or inference beyond the user request

### Scope Control

- No anomaly detection or analysis
- No explanations or interpretations of metric behavior
- No recommendations or actions
- No persistence of state or memory between interactions
- No multi-node agent graphs
- No complicated agent runs

### Extensibility Considerations

- The single-node LangGraph structure should allow additional nodes to be added in future iterations without refactoring the core flow
- The metrics query tool interface should remain stable to support future capabilities such as visualization or anomaly detection

### Deliverables

- Gradio-based chat interface for user interaction
- Single-node LangGraph agent implementation
- LangChain-based metrics query tool
- Configurable integration with Grafana MCP
- End-to-end demo runnable locally

---

## Tasks

**Command**: `/speckit.tasks`

---

## Implementation

**Command**: `/speckit.implement`