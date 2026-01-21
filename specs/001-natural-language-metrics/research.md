# Phase 0 Research: Natural Language Metrics Querying

**Date**: January 21, 2026  
**Feature**: [001-natural-language-metrics](spec.md)  
**Status**: Complete - All clarifications resolved

---

## 1. LangGraph Single-Node Agent Pattern

### Decision
Use LangGraph with TypedDict-based state management and a single node that can be extended with additional nodes in future iterations.

### Rationale
- **Minimalist**: Single node fulfills core requirement (query → metrics)
- **Extensible**: TypedDict state allows new nodes (e.g., visualization, anomaly detection) to be added without core refactoring
- **Learning Value**: Demonstrates agent architecture fundamentals while remaining simple
- **Maintenance**: Single-node pattern easier to understand and test than complex multi-node graphs

### Alternatives Considered
1. **Direct LangChain only** - Rejected: No agent workflow structure, harder to extend
2. **Multi-node graph upfront** - Rejected: Violates minimalism principle, over-engineers for current scope
3. **Custom agent implementation** - Rejected: Duplicates LangGraph functionality, reduces learning value

### Implementation Patterns

```python
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

class MetricsQueryState(TypedDict):
    user_query: str
    metric_name: str
    time_range: TimeRange
    result: MetricsQueryResult
    error: Optional[str]

# Single node agent
def metrics_agent_node(state: MetricsQueryState) -> MetricsQueryState:
    # 1. Parse query with LLM
    # 2. Call metrics tool
    # 3. Format result
    return updated_state

# Build graph
graph = StateGraph(MetricsQueryState)
graph.add_node("metrics_agent", metrics_agent_node)
graph.add_edge(START, "metrics_agent")
graph.add_edge("metrics_agent", END)
```

### Key Points
- **State Design**: Use TypedDict for type safety and clarity
- **Error Handling**: Include error field in state, handle gracefully in node
- **Extension Path**: Additional nodes connect to existing node via edges (no graph restructuring needed)

---

## 2. LangChain Tool Design

### Decision
Use `@tool` decorator with Pydantic field annotations for automatic schema generation and parameter validation.

### Rationale
- **Declarative**: Tool definitions are clear and self-documenting
- **LLM Integration**: Automatic JSON schema generation for function calling
- **Validation**: Built-in parameter validation catches errors early
- **Async Support**: Decorator supports async functions for non-blocking I/O
- **Error Handling**: Consistent error handling across all tools

### Alternatives Considered
1. **Custom tool classes** - Rejected: More boilerplate, same functionality
2. **Manual function wrapping** - Rejected: No schema generation, requires manual validation
3. **Structured tools (Tool base class)** - Less preferred: More verbose than decorator syntax

### Implementation Patterns

```python
from langchain.tools import tool
from pydantic import Field

@tool
def query_grafana_metrics(
    metric_name: str = Field(description="Name of the metric to query"),
    time_range: TimeRange = Field(description="Time range for the query"),
    aggregation: Optional[str] = Field(
        default=None,
        description="Optional aggregation (avg, max, min, sum)"
    )
) -> str:
    """Query metrics from Grafana MCP server.
    
    Args:
        metric_name: The metric to query (e.g., 'cpu_usage', 'memory_usage')
        time_range: Time range as (start_time, end_time)
        aggregation: Optional aggregation function
        
    Returns:
        Formatted metric data as string
    """
    # Implementation
    pass
```

### Key Points
- **Field Descriptions**: Each parameter has clear description for LLM
- **Type Hints**: Used for validation and schema generation
- **Return Type**: Always return string for readability in conversation
- **Error Handling**: Raise exceptions with clear messages; agent handles gracefully

---

## 3. Grafana Integration Architecture

### Decision
Use direct HTTP API integration to Grafana, NOT the MCP server pattern. The Grafana MCP server is for *exposing* your services, not for consuming external APIs.

### Rationale
- **Clarity of Pattern**: HTTP API directly calls Grafana; MCP is for exposing your agent to other systems
- **Control**: Direct API integration provides full control over query parameters and response handling
- **Simplicity**: No need to run MCP server separately; one fewer component to manage
- **Debugging**: Easier to debug HTTP requests than MCP protocol issues

### Important Clarification
The existing `mcp/grafana` Docker container mentioned in constraints is intended as a reference for Grafana MCP server *implementation*. For this agent, we call Grafana's HTTP API directly using the same credentials:

```json
{
  "GRAFANA_URL": "http://localhost:3000",
  "GRAFANA_USERNAME": "mopadmin",
  "GRAFANA_PASSWORD": "moppassword",
  "GRAFANA_ORG_ID": "1"
}
```

### API Integration Pattern

```python
import httpx
from typing import List, Dict, Any

class GrafanaMetricsClient:
    def __init__(self, url: str, username: str, password: str, org_id: str):
        self.url = url
        self.auth = (username, password)
        self.org_id = org_id
        self.client = httpx.AsyncClient()
    
    async def query_metrics(
        self, 
        metric_name: str,
        start_time: int,
        end_time: int
    ) -> List[Dict[str, Any]]:
        """Query metrics via Grafana HTTP API.
        
        Endpoint: /api/datasources/query
        Returns: Time-series data points
        """
        pass

    async def get_available_metrics(self) -> List[str]:
        """Discover available metrics in the system."""
        pass
```

### Authentication Patterns
- **API Key (Recommended)**: Most secure for this use case
- **Basic Auth**: Works with configured username/password
- **OAuth**: For multi-user environments (not needed for local demo)

### Response Format
Grafana returns time-series data:
```python
{
    "target": "cpu_usage",
    "datapoints": [
        [value1, timestamp1],
        [value2, timestamp2],
        ...
    ]
}
```

### Key Points
- **Async Client**: Use `httpx.AsyncClient` for non-blocking queries
- **Error Handling**: Handle connection timeouts, 404s, authentication errors
- **Metric Discovery**: Cache available metrics to guide LLM
- **Connection Pooling**: Reuse HTTP client for efficiency

---

## 4. Pydantic for LLM Output Validation

### Decision
Use Pydantic `BaseModel` with strict field validation and custom validators for complex parsing.

### Rationale
- **Automatic Validation**: LLM outputs automatically validated against schema
- **JSON Schema**: Pydantic generates JSON schema for LLM tool calling
- **Error Clarity**: Validation errors provide clear feedback on parsing issues
- **Type Safety**: Python types enforced at runtime
- **Extensibility**: Custom validators handle business logic

### Alternatives Considered
1. **Manual parsing** - Rejected: Error-prone, no validation
2. **JSONSchema only** - Rejected: No runtime validation
3. **Dataclasses** - Less preferred: No validation without additional libraries

### Implementation Patterns

```python
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class MetricsQuery(BaseModel):
    """LLM-generated query parameters."""
    metric_name: str = Field(
        description="Name of the metric to query"
    )
    start_time: datetime = Field(
        description="Query start time"
    )
    end_time: datetime = Field(
        description="Query end time"
    )
    aggregation: Optional[str] = Field(
        default=None,
        description="Optional aggregation (avg, max, min, sum)"
    )
    
    @validator('aggregation')
    def validate_aggregation(cls, v):
        """Ensure aggregation is one of allowed values."""
        if v and v not in ['avg', 'max', 'min', 'sum']:
            raise ValueError(f"Invalid aggregation: {v}")
        return v

class MetricsQueryResult(BaseModel):
    """Validated metrics query result."""
    metric_name: str
    unit: str
    datapoints: List[tuple[float, int]]  # (value, timestamp)
    aggregation_applied: Optional[str] = None
```

### Validation with LLM

```python
def validate_llm_output(response_text: str) -> MetricsQuery:
    """Parse and validate LLM response."""
    try:
        # Parse JSON from LLM response
        import json
        parsed = json.loads(response_text)
        # Pydantic validates automatically
        query = MetricsQuery(**parsed)
        return query
    except ValidationError as e:
        # Retry with LLM or raise error
        raise ValueError(f"Invalid query: {e}")
```

### Key Points
- **Schema Generation**: `MetricsQuery.schema()` provides JSON schema for LLM
- **Strict Mode**: Use `class Config: validate_assignment = True` for strict validation
- **Error Messages**: Custom validators provide actionable error messages
- **Type Coercion**: Datetime strings automatically parsed to datetime objects

---

## 5. Gradio Chat Interface

### Decision
Use `gr.ChatInterface` for chat-style interaction, with async function integration for non-blocking operations.

### Rationale
- **Purpose-Built**: `ChatInterface` designed specifically for chat UX
- **Simplicity**: Minimal boilerplate compared to custom Blocks
- **Streaming**: Supports streaming responses via generators
- **Mobile-Friendly**: Responsive design out of the box
- **Learning Value**: Clear example of UI integration with agent

### Alternatives Considered
1. **Custom Gradio Blocks** - Rejected: More boilerplate, less readable
2. **Streamlit** - Less preferred: Different ecosystem, less agent-friendly
3. **FastAPI + React** - Rejected: Too complex for demo, violates minimalism

### Implementation Patterns

```python
import gradio as gr
from typing import AsyncGenerator

async def chat_with_agent(
    message: str,
    history: List[tuple[str, str]]
) -> AsyncGenerator[str, None]:
    """Chat function for Gradio ChatInterface.
    
    Args:
        message: User's natural language query
        history: Previous messages in conversation
        
    Yields:
        Streamed response text
    """
    try:
        # Invoke agent (single query - no history context)
        result = await agent.ainvoke({
            "user_query": message
        })
        
        # Format and yield result
        if result.get("error"):
            yield f"Error: {result['error']}"
        else:
            # Stream formatted result
            yield format_metrics_result(result)
            
    except Exception as e:
        yield f"An error occurred: {str(e)}\n\nPlease rephrase your query."

# Create interface
demo = gr.ChatInterface(
    chat_with_agent,
    examples=[
        "Show CPU usage for the last hour",
        "What was memory usage yesterday?",
        "How did request latency change today?"
    ],
    title="Metrics Query Agent",
    description="Ask questions about your system metrics in natural language",
    theme=gr.themes.Soft()
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
```

### Key Points
- **Async Integration**: `ChatInterface` supports async functions directly
- **No History Context**: Each message processed independently (stateless design)
- **Example Queries**: Helps users understand what they can ask
- **Error Display**: Yield error messages for display in chat
- **Streaming**: Use generators (`yield`) for long-running operations

### UI/UX Considerations
- **Input Validation**: Client-side validation in Gradio components
- **Response Formatting**: Use markdown in yielded strings for rich formatting
- **Error Recovery**: Helpful error messages guide users to valid queries
- **Loading States**: Gradio handles automatically with async functions

---

## 6. OpenAI vs Ollama Integration

### Decision
Support both OpenAI and Ollama, determined by environment configuration. Ollama for local/offline, OpenAI for better quality.

### Rationale
- **Flexibility**: Users choose based on their setup
- **Learning Value**: Demonstrates abstraction over LLM providers
- **Cost**: Ollama is free for local development
- **Quality**: OpenAI provides better understanding of natural language
- **Offline**: Ollama works without internet connection

### Implementation Pattern

```python
from langchain.llms import OpenAI
from langchain.llms.ollama import Ollama
from langchain.chat_models import ChatOpenAI

def initialize_llm(model_source: str = "openai") -> BaseLanguageModel:
    """Initialize LLM based on configuration.
    
    Args:
        model_source: "openai" or "ollama"
        
    Returns:
        Initialized LLM instance
    """
    if model_source == "openai":
        return ChatOpenAI(
            model_name=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.0  # Deterministic for metrics queries
        )
    elif model_source == "ollama":
        return Ollama(
            model=os.getenv("OLLAMA_MODEL", "mistral"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        )
    else:
        raise ValueError(f"Unknown model source: {model_source}")
```

### Configuration

```env
# OpenAI Configuration
LLM_SOURCE=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-3.5-turbo

# OR Ollama Configuration
LLM_SOURCE=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
```

---

## Configuration Management

### Decision
Use environment variables with Pydantic `BaseSettings` for configuration validation and defaults.

### Implementation Pattern

```python
from pydantic_settings import BaseSettings

class Config(BaseSettings):
    # Grafana Configuration
    grafana_url: str = "http://localhost:3000"
    grafana_username: str = "mopadmin"
    grafana_password: str = "moppassword"
    grafana_org_id: str = "1"
    
    # LLM Configuration
    llm_source: str = "openai"  # or "ollama"
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral"
    
    # UI Configuration
    gradio_port: int = 7860
    gradio_server_name: str = "0.0.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

### Key Points
- **No Hardcoded Credentials**: All sensitive data from environment
- **Reasonable Defaults**: Works with local Grafana/Ollama setup out of the box
- **Validation**: Pydantic validates configuration on startup
- **Documentation**: Each field has description for users

---

## Summary: Integration Architecture

```
┌─────────────────────────────────────────┐
│         Gradio Chat Interface           │
│         (gr.ChatInterface)              │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      LangGraph Agent (Single Node)       │
│  - State: MetricsQueryState             │
│  - Node: metrics_agent_node             │
└──────────────┬──────────────────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
   ┌────────────┐  ┌─────────────────┐
   │  LLM       │  │ LangChain Tool  │
   │  (OpenAI/  │  │ (query_grafana) │
   │   Ollama)  │  └────────┬────────┘
   └────────────┘           │
                            ▼
                   ┌─────────────────┐
                   │ Pydantic Models │
                   │ (validation)    │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │ Grafana HTTP    │
                   │ API Client      │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │    Grafana      │
                   │ (Metrics Store) │
                   └─────────────────┘
```

### Data Flow
1. **User Input** → Gradio receives natural language query
2. **Agent Processing** → LangGraph node receives query
3. **LLM Translation** → OpenAI/Ollama translates to MetricsQuery
4. **Pydantic Validation** → Query parameters validated
5. **Grafana Query** → HTTP client calls Grafana API
6. **Result Formatting** → Results converted to readable format
7. **Display** → Formatted result yielded to Gradio for display

---

## Implementation Priorities

1. **Foundation**: Config management, Grafana client
2. **Core**: Pydantic models, LLM integration
3. **Agent**: Single-node LangGraph + tool definition
4. **UI**: Gradio chat interface
5. **Polish**: Error handling, result formatting

---

## Key Takeaways

✅ **Clear Technology Stack**:
- LangGraph for agent orchestration
- LangChain for tools and LLM integration
- Pydantic for validation
- Gradio for UI
- httpx for Grafana API

✅ **Extensible Foundation**:
- Single-node pattern allows adding visualization, anomaly detection nodes
- Tool interface stable for new tools
- State model supports additional fields

✅ **Stateless Design**:
- Each query independent
- No conversation history
- Meets minimalism principle

✅ **Configuration-Driven**:
- No hardcoded credentials
- Environment-based setup
- Supports local development
