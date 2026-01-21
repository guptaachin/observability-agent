# Contract: Agent Node

**Feature**: 001-natural-language-metrics  
**Date**: 2026-01-20  
**Type**: LangGraph Node Interface

## Overview

The Agent Node is a single-node LangGraph node that processes natural language queries. This contract defines the node's input/output interface and behavior.

## Node Interface

### Node Name
`process_query`

### Node Description
Processes a natural language query: interprets the query, executes metric retrieval, and formats the response.

### Input State Schema

```python
{
    "query": str,  # Natural language query from user
    "response": str | None  # Initially None, populated by node
}
```

### Output State Schema

```python
{
    "query": str,  # Original query (unchanged)
    "response": str  # Formatted response text
}
```

## Behavior Specification

### Processing Steps

1. **Receive Query**: Extract `query` from graph state
2. **Interpret Query**: Use LLM to parse natural language into structured query parameters
3. **Execute Query**: Invoke metrics query tool with structured parameters
4. **Format Response**: Convert metric data to human-readable text
5. **Update State**: Set `response` in graph state
6. **Return**: Return updated state

### Error Handling

- **Interpretation Error**: If LLM cannot parse query, return error message in `response`
- **Tool Error**: If metrics query tool fails, return error message in `response`
- **Formatting Error**: If data formatting fails, return error message in `response`

All errors are captured in the `response` field with clear, user-friendly messages.

### Response Format

**Success Response**:
```
CPU usage for the last hour (2026-01-20 09:30 - 10:30):

Time                Value
09:30:00           45.2%
09:31:00           47.8%
09:32:00           46.5%
...

Average: 46.5%
```

**Error Response**:
```
I couldn't process your query: [specific error message]

Please try rephrasing your question or check that the metric name is correct.
```

## State Management

- Node is stateless (no memory between invocations)
- Each query is processed independently
- State is transient (exists only during graph execution)

## Extensibility

This single-node structure allows future extensions:
- Add pre-processing node (query validation, normalization)
- Add post-processing node (response enhancement, formatting options)
- Add routing node (multi-capability agent)

The node interface remains stable; new nodes can be added to the graph without modifying this node.

## Usage Example

```python
from langgraph.graph import StateGraph, END

# Define state
class AgentState(TypedDict):
    query: str
    response: str | None

# Create node
def process_query_node(state: AgentState) -> AgentState:
    query = state["query"]
    # ... processing logic ...
    return {"response": formatted_response}

# Build graph
graph = StateGraph(AgentState)
graph.add_node("process_query", process_query_node)
graph.set_entry_point("process_query")
graph.add_edge("process_query", END)
```

## Performance Expectations

- Typical processing: < 10 seconds (includes LLM call + metric query)
- Maximum processing: 30 seconds (configurable timeout)
- Single request-response cycle (no multi-step reasoning)

## Notes

- Node does not maintain conversation history
- Node does not perform multi-step reasoning
- Node focuses on single query → single response pattern
- All processing happens synchronously within node execution
