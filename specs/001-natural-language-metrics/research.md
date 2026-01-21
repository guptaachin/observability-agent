# Research: Natural Language Metric Queries

**Feature**: 001-natural-language-metrics  
**Date**: 2026-01-20  
**Purpose**: Resolve technical decisions and establish best practices for implementation

## Technology Decisions

### LangGraph Single-Node Agent Pattern

**Decision**: Use LangGraph with a single-node graph structure for the agent workflow.

**Rationale**: 
- LangGraph provides a clear foundation for future multi-node expansion while keeping current implementation simple
- Single-node pattern aligns with minimalism principle (core functionality only)
- Graph structure makes extension points explicit and well-documented
- Standard pattern in LangGraph documentation for simple agent workflows

**Alternatives Considered**:
- Direct LangChain chain: Rejected - lacks extensibility for future multi-node workflows
- Custom workflow: Rejected - reinvents patterns already solved by LangGraph
- Multi-node from start: Rejected - violates minimalism principle

**Implementation Notes**:
- Node receives user query, calls LLM for interpretation, invokes metrics tool, formats response
- Node returns formatted response directly (no routing needed for single node)
- Graph state should be minimal (just query and response)

### LangChain Tool for Grafana MCP Integration

**Decision**: Implement a LangChain tool that wraps Grafana MCP server communication.

**Rationale**:
- LangChain tool interface provides standard integration point for agent workflows
- Tool abstraction allows swapping MCP implementation without changing agent code
- Tool can handle structured query parameters (metric name, time range, filters)
- Error handling can be encapsulated within tool

**Alternatives Considered**:
- Direct MCP client calls in agent node: Rejected - violates separation of concerns
- Custom tool interface: Rejected - LangChain tool is standard and extensible

**Implementation Notes**:
- Tool input: Structured query parameters (dict with metric_name, time_range, filters)
- Tool output: Raw time-series data or simple aggregates
- Tool should handle MCP connection errors gracefully
- Tool interface should remain stable for future capabilities

### Gradio Chat Interface

**Decision**: Use Gradio for the chat-style user interface.

**Rationale**:
- Minimal setup required (single Python file)
- Built-in chat interface components
- Easy to run locally for demo purposes
- Lightweight and suitable for exploration/demo use case

**Alternatives Considered**:
- Streamlit: Rejected - more complex setup, better for dashboards than chat
- Custom web UI: Rejected - violates minimalism, too much overhead
- CLI only: Rejected - doesn't meet user experience requirements

**Implementation Notes**:
- Simple text input/output interface
- No history persistence (stateless per constitution)
- Clear error message display
- Minimal styling (focus on functionality)

### Configuration Management

**Decision**: Use environment variables with optional config file, Python-dotenv for local development.

**Rationale**:
- Environment variables are standard for deployment scenarios
- Config file provides convenience for local development
- No hardcoded credentials or endpoints (security best practice)
- Reasonable defaults enable quick local setup

**Alternatives Considered**:
- Config file only: Rejected - less flexible for deployment
- Hardcoded defaults: Rejected - violates security best practices
- Complex config system: Rejected - violates minimalism

**Implementation Notes**:
- Required: Grafana MCP server URL/connection details
- Optional: LLM API key, model selection, timeouts
- Defaults: Local development values (localhost, common ports)
- Validation: Check required config on startup

### LLM Integration via LangChain

**Decision**: Use LangChain for LLM interaction, supporting OpenAI-compatible APIs.

**Rationale**:
- LangChain provides abstraction over different LLM providers
- Standard patterns for prompt management and response parsing
- Easy to swap LLM providers without changing agent code
- Supports structured output parsing for query interpretation

**Alternatives Considered**:
- Direct LLM API calls: Rejected - less flexible, more code
- Custom LLM wrapper: Rejected - reinvents LangChain patterns

**Implementation Notes**:
- Use structured output parsing to extract metric query parameters
- Prompt should focus on translation: natural language → structured query
- No multi-step reasoning or planning (single pass)
- Error handling for LLM failures (rate limits, API errors)

## Integration Patterns

### Grafana MCP Server Communication

**Decision**: Use MCP (Model Context Protocol) client library to communicate with Grafana MCP server.

**Rationale**:
- MCP provides standard protocol for tool integration
- Grafana MCP server exposes metrics query capabilities
- Client library handles protocol details

**Implementation Notes**:
- Query format: Structured parameters (metric name, time range)
- Response format: Time-series data (values + timestamps)
- Error handling: Network errors, invalid queries, missing metrics
- Connection management: Handle disconnections gracefully

### Query Interpretation Strategy

**Decision**: Use LLM with structured output to parse natural language into query parameters.

**Rationale**:
- LLMs excel at natural language understanding
- Structured output ensures consistent parameter extraction
- Single-pass interpretation aligns with minimalism (no multi-step reasoning)

**Implementation Notes**:
- Input: Natural language question
- Output: Structured dict with metric_name, time_range (start, end), filters
- Validation: Check extracted parameters before querying metrics
- Fallback: Clear error if interpretation fails

## Best Practices

### Error Handling

- User-facing errors: Clear, actionable messages (e.g., "Metric 'xyz' not found")
- System errors: Log details, return user-friendly message
- LLM errors: Handle gracefully, suggest reformulation
- MCP errors: Distinguish between network errors and invalid queries

### Testing Strategy

- Unit tests: Agent node logic, tool logic, config parsing
- Integration tests: End-to-end flow with mock MCP server
- Contract tests: Verify tool interface stability
- Test data: Use real metric names/patterns, avoid synthetic data

### Code Organization

- Separation of concerns: Agent workflow, tool integration, UI, config
- Clear interfaces: Tool interface stable for extensibility
- Documentation: Inline comments explain intent (clarity principle)
- Extensibility: Single-node graph allows adding nodes without refactoring

## Open Questions Resolved

1. **Q**: How to handle ambiguous queries?  
   **A**: Return error asking for clarification (no automatic inference beyond user request)

2. **Q**: What format for metric data response?  
   **A**: Human-readable text format (table or simple summary), not raw JSON

3. **Q**: How to handle time range parsing?  
   **A**: LLM extracts time range, convert to absolute timestamps before querying

4. **Q**: Should we cache metric queries?  
   **A**: No (stateless, no persistence per constitution)

5. **Q**: How to validate metric names exist?  
   **A**: Query MCP server, return error if metric not found

## References

- LangGraph documentation: Single-node agent patterns
- LangChain tools: Tool interface and integration patterns
- Grafana MCP: Protocol specification and client usage
- Gradio: Chat interface components and best practices
