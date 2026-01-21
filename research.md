# Research: Natural Language Metrics Querying System

This document outlines research findings for building a natural language metrics querying system using Python, covering key architectural and implementation decisions.

## 1. LangGraph Single-Node Agent Pattern

### Decision
Use LangChain's `create_agent` function built on LangGraph for a single-node agent implementation with extensible architecture.

### Rationale
- **Production-Ready**: Built on LangGraph, LangChain's low-level orchestration framework trusted by companies like Klarna and Replit
- **Durable Execution**: Agents persist through failures and can resume from checkpoints
- **Extensible**: Single-node architecture easily extends to multi-node workflows by adding additional nodes as needed
- **Flexible State Management**: TypedDict-based state schema allows easy addition of custom state beyond messages
- **Built-in Tool Support**: Native support for tool calling with automatic error handling and retry logic

### Alternatives Considered
1. **Direct LLM calls**: Simpler but lacks state persistence, tool integration, and error recovery
2. **LangGraph manual graphs**: More control but requires more boilerplate code for basic agent functionality
3. **Simple function chains**: Limited extensibility and no built-in retry/error handling

### Key Implementation Patterns

**Basic Single-Node Agent Structure:**
```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
agent = create_agent(
    model=model,
    tools=tools,
    system_prompt="You are a helpful assistant that queries Grafana metrics."
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "What is the CPU usage?"}]
})
```

**Custom State Management:**
```python
from typing import TypedDict
from langchain.agents import AgentState

class MetricsQueryState(AgentState):
    messages: list  # Built-in from AgentState
    query_context: dict
    query_cache: dict

agent = create_agent(
    model=model,
    tools=tools,
    state_schema=MetricsQueryState
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "..."}],
    "query_context": {"dashboard": "main"},
    "query_cache": {}
})
```

**Error Handling via Middleware:**
```python
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage

@wrap_tool_call
def handle_tool_errors(request, handler):
    try:
        return handler(request)
    except Exception as e:
        return ToolMessage(
            content=f"Tool error: {str(e)}. Please check your input.",
            tool_call_id=request.tool_call["id"]
        )

agent = create_agent(
    model=model,
    tools=tools,
    middleware=[handle_tool_errors]
)
```

**Extending to Multi-Node Architecture:**
- Initial agent uses single node with ReAct pattern (Reasoning + Acting)
- Add sequential nodes by creating StateGraph with multiple nodes
- Each node performs distinct operation (query parsing, metric retrieval, formatting)
- Edges define flow between nodes based on conditions

### Best Practices
- Keep state minimal and focused on domain-specific needs
- Use middleware for cross-cutting concerns (logging, error handling, validation)
- Leverage middleware for dynamic system prompts based on runtime context
- Implement proper error handling at tool level and middleware level
- Stream responses for long-running operations to show progress

---

## 2. LangChain Tool Design

### Decision
Use `@tool` decorator with Pydantic field annotations for parameter validation, comprehensive documentation, and automatic schema generation.

### Rationale
- **Type Safety**: Pydantic automatically validates inputs and generates JSON schema for tool parameters
- **Documentation**: Type hints and docstrings are converted to tool descriptions automatically
- **Flexibility**: Supports both sync and async functions
- **Schema Generation**: Produces proper JSON schemas for LLM tool calling without manual specification
- **Error Handling**: Validation errors are caught before tool execution

### Alternatives Considered
1. **Raw functions**: No validation or automatic documentation
2. **Manual Tool class**: More verbose, requires manual schema definition
3. **Langchain's StructuredTool**: More control but requires more code
4. **Pydantic dataclasses only**: Works but `@tool` decorator is more concise

### Key Implementation Patterns

**Basic Tool with Validation:**
```python
from langchain.tools import tool
from pydantic import Field

@tool
def query_metric(
    metric_name: str = Field(description="The name of the metric (e.g., 'cpu_usage', 'memory_free')"),
    time_range: str = Field(description="Time range (e.g., '1h', '24h', '7d')"),
    aggregation: str = Field(default="avg", description="Aggregation method: 'avg', 'min', 'max', 'sum'")
) -> str:
    """Query metrics from Grafana for a specified time range.
    
    Returns formatted metric data with statistics.
    """
    # Implementation
    pass
```

**Tool with Complex Return Type:**
```python
from typing import TypedDict

class MetricResult(TypedDict):
    metric_name: str
    values: list[float]
    timestamps: list[str]
    aggregation: str
    time_range: str

@tool
def query_metric(metric_name: str) -> str:
    """Query metric from Grafana.
    
    Returns JSON string with metric data that can be parsed by the agent.
    """
    result: MetricResult = {
        "metric_name": metric_name,
        "values": [...],
        "timestamps": [...],
        "aggregation": "avg",
        "time_range": "1h"
    }
    import json
    return json.dumps(result)
```

**Tool with Error Handling:**
```python
@tool
def query_metric(metric_name: str, time_range: str = "1h") -> str:
    """Query Grafana metric.
    
    Raises ValueError if metric not found or parameters invalid.
    """
    if not metric_name or not metric_name.strip():
        raise ValueError("metric_name cannot be empty")
    
    if time_range not in ["1h", "6h", "24h", "7d"]:
        raise ValueError(f"Invalid time_range: {time_range}")
    
    try:
        # Query implementation
        pass
    except Exception as e:
        raise ValueError(f"Failed to query metric: {str(e)}")
```

**Async Tool for Performance:**
```python
import asyncio

@tool
async def query_multiple_metrics(metric_names: list[str]) -> str:
    """Query multiple metrics in parallel from Grafana."""
    tasks = [get_metric_data(name) for name in metric_names]
    results = await asyncio.gather(*tasks)
    return format_results(results)
```

**Tool Parameter Validation with Constraints:**
```python
from pydantic import Field

@tool
def query_metric(
    metric_name: str = Field(description="Metric name"),
    limit: int = Field(default=100, ge=1, le=1000, description="Max data points to return")
) -> str:
    """Query metric with result size limit.
    
    The limit parameter must be between 1 and 1000.
    """
    pass
```

### Best Practices
- Always include docstrings describing what the tool does
- Use Field descriptors for parameter documentation
- Implement validation with constraints (ge, le, pattern, etc.)
- Return JSON strings from tools for complex data structures
- Keep tool return values concise and parseable
- Provide meaningful error messages that guide the LLM on how to fix issues
- Use async tools for I/O-bound operations
- Test tool schemas by inspecting generated JSON schemas

---

## 3. Grafana MCP Server Integration

### Decision
Implement direct API integration with Grafana using HTTP client library; MCP servers are for exposing your own services to other systems, not for consuming external APIs.

### Rationale
- **MCP Purpose**: Model Context Protocol (MCP) is a standardized protocol for connecting AI applications to external systems. MCP servers *expose* data/tools, they don't consume them.
- **Direct Integration**: Use standard HTTP client (httpx, requests) for direct Grafana API queries
- **Flexibility**: Direct API access provides full control over authentication and request patterns
- **Performance**: Eliminates unnecessary protocol layer overhead
- **Simplicity**: Grafana's REST API is well-documented and straightforward

### Alternatives Considered
1. **Build MCP client**: Over-engineered for this use case; MCP is more useful when you want to expose your metrics system to other AI applications
2. **Grafana Python SDK**: Could use if available, but direct HTTP requests are more flexible
3. **GraphQL query endpoint**: Overkill for basic metrics queries
4. **Webhook approach**: One-directional, not suitable for agent-driven queries

### Key Implementation Patterns

**Basic Grafana API Integration:**
```python
import httpx
import json
from typing import Optional

class GrafanaClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.client = httpx.Client()
    
    def query_metric(
        self,
        metric_name: str,
        time_range: str = "1h",
        aggregation: str = "avg"
    ) -> dict:
        """Query metrics from Grafana.
        
        Args:
            metric_name: Prometheus metric name
            time_range: Time range like '1h', '24h', '7d'
            aggregation: Aggregation function
            
        Returns:
            Dictionary with metric data
        """
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        # Convert time range to Prometheus duration
        duration = self._parse_time_range(time_range)
        
        # Query Grafana Prometheus datasource
        query = f"{aggregation}({metric_name})"
        params = {
            "query": query,
            "start": f"now-{duration}",
            "step": "60s"
        }
        
        response = self.client.get(
            f"{self.base_url}/api/datasources/proxy/1/query",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        
        return response.json()
    
    def _parse_time_range(self, time_range: str) -> str:
        """Convert user-friendly time range to Prometheus format."""
        mapping = {"1h": "1h", "6h": "6h", "24h": "24h", "7d": "7d"}
        return mapping.get(time_range, "1h")
```

**Authentication Patterns:**
```python
# API Key Authentication
class GrafanaClient:
    def __init__(self, base_url: str, api_key: str):
        self.headers = {"Authorization": f"Bearer {api_key}"}

# Basic Authentication
class GrafanaClient:
    def __init__(self, base_url: str, username: str, password: str):
        import base64
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        self.headers = {"Authorization": f"Basic {credentials}"}

# OAuth Token (if Grafana Cloud)
class GrafanaClient:
    def __init__(self, base_url: str, token: str):
        self.headers = {"Authorization": f"Bearer {token}"}
```

**Response Format Examples:**
```python
# Prometheus range query response
{
    "status": "success",
    "data": {
        "resultType": "matrix",
        "result": [
            {
                "metric": {"__name__": "cpu_usage", "instance": "localhost"},
                "values": [
                    [1642598400, "42.5"],
                    [1642598460, "43.1"],
                    [1642598520, "41.8"]
                ]
            }
        ]
    }
}

# Grafana annotation response
{
    "annotations": [
        {
            "time": 1642598400000,
            "text": "Deployment v1.2.3",
            "tags": ["release"]
        }
    ]
}
```

**Async Integration for Agent:**
```python
import asyncio
import httpx

class AsyncGrafanaClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
    
    async def query_metric(self, metric_name: str, time_range: str = "1h") -> dict:
        """Async metric query."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/datasources/proxy/1/query",
                headers=headers,
                params={"query": metric_name}
            )
            return response.json()
    
    async def query_multiple_metrics(self, metric_names: list[str]) -> list[dict]:
        """Query multiple metrics in parallel."""
        tasks = [
            self.query_metric(name) for name in metric_names
        ]
        return await asyncio.gather(*tasks)
```

### Connection Best Practices
- Store credentials in environment variables, not hardcoded
- Implement connection pooling for better performance
- Add timeout configuration for API requests
- Handle rate limiting with exponential backoff
- Cache metric metadata for performance
- Validate API key at client initialization

---

## 4. Pydantic for LLM Output Validation

### Decision
Use Pydantic `BaseModel` with strict field validation, custom validators, and error handling strategies for validating and parsing LLM-generated structured output.

### Rationale
- **Type Safety**: Leverages Python type hints for validation
- **Performance**: Core validation logic written in Rust (Pydantic v2)
- **JSON Schema Generation**: Automatic JSON schema for tool calling
- **Error Details**: Provides detailed validation error information
- **Customizable**: Supports custom validators and serializers
- **Ecosystem**: Widely used with LangChain, FastAPI, and others (8,000+ packages depend on it)

### Alternatives Considered
1. **Manual JSON parsing**: Prone to errors, no validation
2. **dataclasses only**: Basic validation, less flexible
3. **TypedDict**: Type hints but no runtime validation
4. **Regular expressions**: Only for string parsing, not comprehensive

### Key Implementation Patterns

**Basic LLM Output Model:**
```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal

class MetricsQuery(BaseModel):
    """Structured output for parsed metrics query."""
    metric_name: str = Field(description="Name of the metric to query")
    time_range: str = Field(description="Time range for the query")
    aggregation: Literal["avg", "min", "max", "sum"] = Field(description="Aggregation method")
    dashboard: str = Field(default="main", description="Dashboard name")

# Parse LLM output
llm_output = {
    "metric_name": "cpu_usage",
    "time_range": "1h",
    "aggregation": "avg"
}

query = MetricsQuery(**llm_output)
print(query.metric_name)  # "cpu_usage"
```

**Validation with Constraints:**
```python
from pydantic import Field, field_validator
from typing import Optional

class MetricsQueryRequest(BaseModel):
    metric_name: str = Field(
        min_length=1,
        max_length=100,
        description="Metric name"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Maximum number of data points"
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Filter tags"
    )
    
    @field_validator('metric_name')
    @classmethod
    def validate_metric_name(cls, v):
        # Only alphanumeric, underscore, and dot allowed
        if not all(c.isalnum() or c in '_.' for c in v):
            raise ValueError('Invalid characters in metric name')
        return v.lower()
```

**Handling Multiple Output Types:**
```python
from typing import Union
from pydantic import Field

class MetricQuery(BaseModel):
    type: Literal["metric"]
    metric_name: str

class AlertQuery(BaseModel):
    type: Literal["alert"]
    alert_name: str
    state: Literal["firing", "resolved"]

class DashboardQuery(BaseModel):
    type: Literal["dashboard"]
    dashboard_name: str

# Union type for flexible parsing
QueryType = Union[MetricQuery, AlertQuery, DashboardQuery]

def parse_llm_output(output: dict) -> QueryType:
    """Parse LLM output into appropriate query type."""
    if output.get("type") == "metric":
        return MetricQuery(**output)
    elif output.get("type") == "alert":
        return AlertQuery(**output)
    elif output.get("type") == "dashboard":
        return DashboardQuery(**output)
    else:
        raise ValueError(f"Unknown query type: {output.get('type')}")
```

**Error Handling and Retries:**
```python
from pydantic import ValidationError
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

class QueryRequest(BaseModel):
    metric: str
    time_range: str

agent = create_agent(
    model=model,
    tools=tools,
    response_format=ToolStrategy(
        schema=QueryRequest,
        handle_errors=True  # Automatic retry on validation error
    )
)

# Access parsed result
result = agent.invoke({
    "messages": [{"role": "user", "content": "Query CPU metric"}]
})
parsed_query = result["structured_response"]
```

**Custom Validation Logic:**
```python
from pydantic import BaseModel, field_validator, model_validator
from datetime import datetime
from typing import Optional

class TimeSeriesQuery(BaseModel):
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_time_specification(self):
        """Ensure exactly one time specification method is used."""
        specified = sum([
            self.start_time is not None,
            self.end_time is not None,
            self.duration is not None
        ])
        
        if specified == 0:
            raise ValueError("Must specify start_time, end_time, or duration")
        if specified > 1:
            raise ValueError("Specify only one time specification method")
        
        return self
```

**Serialization and Response Formatting:**
```python
from pydantic import BaseModel, ConfigDict
from enum import Enum

class ResponseFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    TABLE = "table"

class QueryResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "metric": "cpu_usage",
                    "value": 42.5,
                    "timestamp": "2024-01-20T12:00:00Z"
                }
            ]
        }
    )
    
    metric: str
    value: float
    timestamp: str
    
    def to_string(self, format: ResponseFormat = ResponseFormat.JSON) -> str:
        if format == ResponseFormat.JSON:
            return self.model_dump_json(indent=2)
        elif format == ResponseFormat.CSV:
            return f"{self.metric},{self.value},{self.timestamp}"
        else:
            return f"{self.metric}: {self.value} @ {self.timestamp}"
```

### Best Practices
- Define models with clear field descriptions for LLM context
- Use `Literal` types for constrained choices
- Leverage `field_validator` for complex validation logic
- Use Union types when LLM output can have multiple formats
- Implement retry logic for validation failures
- Provide detailed error messages that guide LLM corrections
- Use `ConfigDict` to customize model behavior
- Test models with sample LLM outputs to validate schemas

---

## 5. Gradio Chat Interface

### Decision
Use `gr.ChatInterface` for rapid chat UI development with streaming support and custom message styling.

### Rationale
- **Specialized for Chat**: Purpose-built for conversational interfaces, not generic Interface
- **Minimal Code**: Handles chat UX automatically (message history, scrolling, styling)
- **Streaming Support**: Built-in support for streaming responses token-by-token
- **Async Integration**: Seamlessly integrates with async Python functions
- **Error Display**: Native error message handling in chat interface
- **Production Ready**: Used by major ML projects, supports sharing to Hugging Face Spaces

### Alternatives Considered
1. **gr.Interface**: Generic, requires more custom code for chat behavior
2. **gr.Blocks**: Maximum flexibility but requires manual chat UI implementation
3. **Custom HTML/CSS**: Full control but high development overhead
4. **FastAPI + frontend**: More complex architecture, not ideal for prototyping
5. **Streamlit**: Alternative, but Gradio better for chat-specific features

### Key Implementation Patterns

**Basic ChatInterface:**
```python
import gradio as gr

def chat_function(message: str, history: list) -> str:
    """Simple chat function that responds to metric queries.
    
    Args:
        message: Current user message
        history: List of [user_msg, bot_msg] pairs
    
    Returns:
        Bot response as string
    """
    # Get context from history if needed
    context = "\n".join([f"User: {h[0]}\nAssistant: {h[1]}" for h in history])
    
    # Use agent to process query
    response = agent.invoke({
        "messages": [{"role": "user", "content": message}]
    })
    
    return response["messages"][-1].content

demo = gr.ChatInterface(
    chat_function,
    title="Metrics Query Assistant",
    description="Ask about your Grafana metrics"
)

demo.launch()
```

**Streaming Responses:**
```python
import gradio as gr
from typing import Generator

def streaming_chat(message: str, history: list) -> Generator[str, None, None]:
    """Chat function that streams response tokens.
    
    Yields:
        Partial response strings to display progressively
    """
    # Stream from agent
    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": message}]},
        stream_mode="values"
    ):
        latest_message = chunk["messages"][-1]
        if latest_message.content:
            yield latest_message.content

demo = gr.ChatInterface(
    streaming_chat,
    title="Streaming Metrics Assistant"
)

demo.launch()
```

**Async Integration:**
```python
import gradio as gr
import asyncio

async def async_chat(message: str, history: list) -> str:
    """Async chat function for non-blocking operations."""
    
    # Can now use async operations
    result = await agent.ainvoke({
        "messages": [{"role": "user", "content": message}]
    })
    
    return result["messages"][-1].content

demo = gr.ChatInterface(
    async_chat,
    title="Async Metrics Assistant"
)

demo.launch()
```

**Error Handling in Chat:**
```python
import gradio as gr

def chat_with_errors(message: str, history: list) -> str:
    """Chat function with error handling."""
    try:
        # Validate input
        if not message or not message.strip():
            return "Please enter a query"
        
        if len(message) > 500:
            return "Query is too long (max 500 chars)"
        
        # Process with agent
        result = agent.invoke({
            "messages": [{"role": "user", "content": message}]
        })
        
        return result["messages"][-1].content
        
    except ValueError as e:
        return f"⚠️ Invalid input: {str(e)}"
    except Exception as e:
        return f"❌ Error: {str(e)}. Please try again."

demo = gr.ChatInterface(
    chat_with_errors,
    title="Metrics Assistant",
    examples=[
        "What is the current CPU usage?",
        "Show me memory metrics for the last 24 hours",
        "Compare disk usage across instances"
    ]
)

demo.launch()
```

**Custom Message Formatting:**
```python
import gradio as gr
import json
from typing import Union

def chat_with_formatting(message: str, history: list) -> Union[str, dict]:
    """Chat with formatted responses."""
    
    result = agent.invoke({
        "messages": [{"role": "user", "content": message}]
    })
    
    response = result["messages"][-1].content
    
    # Format as markdown for better display
    if isinstance(response, dict):
        # Format metric results nicely
        formatted = "```json\n" + json.dumps(response, indent=2) + "\n```"
        return formatted
    
    return response

demo = gr.ChatInterface(
    chat_with_formatting,
    title="Metrics Query Assistant"
)

demo.launch()
```

**Advanced: Custom Chat Component with State:**
```python
import gradio as gr
from typing import Optional

class MetricsChatBot:
    def __init__(self, agent):
        self.agent = agent
        self.current_dashboard = "main"
    
    def chat(self, message: str, history: list) -> str:
        """Chat with dashboard context."""
        
        # Inject context into message
        enhanced_message = f"Dashboard: {self.current_dashboard}\nQuery: {message}"
        
        result = self.agent.invoke({
            "messages": [{"role": "user", "content": enhanced_message}],
            "dashboard": self.current_dashboard
        })
        
        return result["messages"][-1].content
    
    def set_dashboard(self, dashboard: str):
        """Change dashboard context."""
        self.current_dashboard = dashboard

chatbot = MetricsChatBot(agent)

with gr.Blocks() as demo:
    gr.Markdown("# Grafana Metrics Query Assistant")
    
    with gr.Row():
        dashboard_select = gr.Dropdown(
            choices=["main", "performance", "security"],
            value="main",
            label="Dashboard"
        )
    
    chat_interface = gr.ChatInterface(chatbot.chat)
    
    dashboard_select.change(
        fn=chatbot.set_dashboard,
        inputs=dashboard_select
    )

demo.launch()
```

**Using with Environment Variables:**
```python
import gradio as gr
import os

def create_app():
    # Load configuration from env
    title = os.getenv("APP_TITLE", "Metrics Assistant")
    theme = os.getenv("APP_THEME", "soft")
    share = os.getenv("SHARE", "False").lower() == "true"
    
    demo = gr.ChatInterface(
        chat_function,
        title=title,
        theme=theme,
        examples=[...],
        retry_btn=None,
        undo_btn="↶ Undo",
        clear_btn="🗑️ Clear"
    )
    
    return demo

if __name__ == "__main__":
    app = create_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
```

### Best Practices
- Keep chat function responsive with timeout handling
- Provide clear examples in `examples` parameter
- Use streaming for better UX with long-running operations
- Implement input validation before processing
- Show helpful error messages formatted for readability
- Store conversation state in history for multi-turn queries
- Use async functions for I/O operations (API calls)
- Test with various message lengths and special characters
- Implement proper logging for debugging
- Consider rate limiting for production deployments

---

## Integration Architecture

### Complete System Flow

```
User Input (Gradio Chat)
        ↓
   Agent (LangGraph)
        ↓
    Tools (with Pydantic validation)
        ↓
  Grafana API (HTTP client)
        ↓
   Metric Data
        ↓
   Format Response (Pydantic)
        ↓
  Display in Chat (Gradio)
```

### Component Dependencies
- **Gradio**: Chat UI layer
- **LangChain Agents**: Orchestration and tool calling
- **LangGraph**: Agent state management and workflow
- **Pydantic**: Data validation for tools and LLM outputs
- **httpx**: Grafana API integration
- **OpenAI/Anthropic SDK**: LLM integration

### Suggested Implementation Order
1. Start with Pydantic models for query and response types
2. Build Grafana API client with proper authentication
3. Create LangChain tools wrapping API client
4. Set up agent with tools and basic system prompt
5. Build Gradio chat interface
6. Add streaming and async support
7. Implement error handling and retry logic
8. Add caching and optimization

---

## Summary Table

| Topic | Approach | Why | Key Benefit |
|-------|----------|-----|------------|
| Agent | LangGraph + `create_agent` | Production-ready, extensible | Built-in error handling, state persistence |
| Tools | `@tool` decorator + Pydantic | Automatic validation & docs | Type safety, JSON schema generation |
| Grafana | Direct HTTP API | MCP is for serving, not consuming | Simplicity, full control |
| Validation | Pydantic BaseModel | Type-safe, fast, flexible | Detailed errors, custom validators |
| Chat UI | `gr.ChatInterface` | Purpose-built for chat | Minimal code, streaming support |
