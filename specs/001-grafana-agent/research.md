# Research: Grafana Agent for Dashboard Discovery

**Phase 0 Output** | **Status**: Complete | **Date**: 2026-01-23

## Summary

All technical decisions are fully specified by user input and project constitution. No external research required; no NEEDS CLARIFICATION items remain.

## Design Decisions (Rationale by Research)

### 1. Single-Node LangGraph Architecture

**Decision**: Implement agent as single-node LangGraph graph
- **Node responsibility**: Accept query → call LLM → return response
- **No multi-node orchestration, branching, or loops**

**Rationale**:
- **User requirement**: "Limit to create one node agent in langgraph"
- **Constitution principle**: Minimal Code & Education-driven (demonstrates core patterns without orchestration complexity)
- **Extensibility**: State dict design allows future nodes (e.g., query router, multi-hop reasoning) to be added as separate nodes without refactoring current node
- **Learning value**: Teaches single-node implementation before multi-node concepts

**References**:
- User input: "Implement the agent as a single-node graph"
- Constitution Principle III (Extensibility): "The single-node LangGraph structure should allow additional nodes to be added in future iterations without refactoring the core flow"
- Constitution Principle VII (Minimal Code): "Every line of code should earn its place"

---

### 2. Gradio Chat Interface

**Decision**: Use Gradio ChatInterface for user interaction
- **No custom web framework** (FastAPI, Flask, etc.)
- **Local demo only** (not production deployment)

**Rationale**:
- **User requirement**: "Use Gradio to provide a lightweight, local chat interface"
- **Constitution principle**: Minimal Code (Gradio requires minimal boilerplate)
- **Setup simplicity**: Engineers cloning repo can run `python src/main.py` without Docker, manual port forwarding, or server configuration
- **Learning value**: Demonstrates agent-UI integration without framework complexity

**Alternatives considered**:
- Custom FastAPI + Vue frontend: Rejected (violates Minimal Code principle; unnecessary for local demo)
- Streamlit: Rejected (Gradio explicitly requested; both equally valid, user chose Gradio)
- Terminal-only CLI: Rejected (chat interface explicitly requested for UX)

**References**:
- User input: "Use Gradio to provide a lightweight, local chat interface"
- Constitution Principle VI (Simplistic Structure): "No nested code directories only when absolutely necessary"

---

### 3. Grafana MCP Server Integration (No Direct APIs)

**Decision**: Communicate with Grafana exclusively via MCP server
- **No direct HTTP calls to Grafana API** (`GET /api/dashboards`, etc.)
- **All queries routed through MCP server interface** (Docker-based, stdio transport)

**Rationale**:
- **User requirement**: "Talking to grafana can only be done via Grafana MCP server. Do not use APIs"
- **Constraint satisfaction**: "The capability must operate on top of the existing observability stack running in docker"
- **Tool abstraction**: MCP server isolates agent from Grafana API changes; tool interface remains stable for future multi-node extensions
- **Learning value**: Demonstrates MCP client integration pattern (increasingly relevant for LLM-based applications)

**Alternatives considered**:
- Direct Grafana HTTP API: Rejected (explicitly forbidden; also violates intent to demonstrate MCP)
- Custom middleware: Rejected (unnecessary; MCP server already handles protocol translation)

**Implementation approach**:
```python
# Tool receives MCP config (connection details)
# Initializes MCP client to Docker-based server
# Calls methods: list_dashboards(), get_dashboard(uid)
# Returns structured data to LLM
```

**References**:
- User input: "Talking to grafana can only be done via Grafana MCP server. Do not use APIs"
- User input: Grafana MCP configuration in `.specify/memory/` or deployment guide
- Spec FR-008: "Agent MUST use only the Grafana MCP server for all Grafana interactions; no direct API calls"

---

### 4. LLM Support (OpenAI & Ollama)

**Decision**: Support both OpenAI (cloud) and Ollama (local) LLMs
- **Configuration at runtime** (via environment variable)
- **Default**: Configurable (e.g., gpt-4-turbo for OpenAI, llama2 for Ollama)

**Rationale**:
- **User requirement**: "We add support for both OpenAI and Ollama"
- **Learning value**: Demonstrates LLM abstraction; teaches switching between providers
- **Accessibility**: Engineers can use free Ollama locally or OpenAI API
- **Cost control**: Local Ollama option avoids API costs for classroom/learning environments
- **Implementation simplicity**: LangChain abstracts both as `ChatOpenAI` and `ChatOllama` with consistent interface

**Alternatives considered**:
- OpenAI only: Rejected (learning value lost; user specified both)
- Ollama only: Rejected (OpenAI provides better default experience; both requested)
- Add other providers (Claude, Gemini, etc.): Rejected (scope creep; not in user request; Constitution Principle II: Minimalism)

**Configuration approach**:
```env
LLM_PROVIDER=openai  # or ollama
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

**References**:
- User input: "We add support for both OpenAI and Ollama"
- Spec FR-010: "Agent MUST support OpenAI and Ollama LLMs; model selection configurable at runtime"

---

### 5. Configuration Management (Environment Variables + Optional YAML)

**Decision**: Two-tier configuration
1. **Primary**: Environment variables (zero-config with defaults; easy CI/CD)
2. **Secondary**: Optional YAML config file (templates for complex setups)

**Rationale**:
- **User requirement**: "Configuration should be provided via environment variables or a config file. No credentials or endpoints should be hardcoded."
- **Constitution principle**: Simplistic Structure (minimal configuration complexity)
- **Local dev simplicity**: Copy `.env.example` to `.env`, edit, run
- **Production safety**: Secrets never in version control; can use managed secrets services
- **Learning value**: Demonstrates configuration patterns used in production systems

**Alternatives considered**:
- YAML only: Rejected (more verbose; environment variables simpler for local dev)
- Environment variables only: Rejected (template config file useful for documentation)
- CLI arguments: Rejected (less standard; doesn't support server deployments)
- Hardcoded with env override: Rejected (violates security constraint)

**Default values for local development**:
```
GRAFANA_URL=http://localhost:3000
GRAFANA_USERNAME=mopadmin
GRAFANA_PASSWORD=moppassword
GRAFANA_ORG_ID=1
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
```

**Configuration hierarchy**:
1. Hardcoded defaults (see above)
2. `.env` file (if exists)
3. Environment variables (override all)
4. YAML config file (optional, for advanced setups)

**References**:
- User input: "Configuration should be provided via environment variables or a config file"
- User input: "No credentials or endpoints should be hardcoded. Reasonable defaults may be provided for local development"
- Spec FR-009: "Agent MUST be configurable via environment variables or config file"

---

### 6. Error Handling Strategy

**Decision**: Try-except at agent node level with user-facing error messages
- **Connection failures**: Clear message about Grafana unreachability
- **Out-of-scope queries**: Guidance on what agent can/cannot do
- **Invalid input**: Prompt for valid query format
- **MCP errors**: Transparent error reporting

**Rationale**:
- **User requirement**: "Handle invalid or unsupported queries gracefully. Return clear error messages."
- **Specification requirement**: FR-006, FR-007 (clear errors for out-of-scope and connection failures)
- **Learning value**: Demonstrates robust error handling essential for production agents
- **User experience**: Engineers understand why queries fail and how to fix them
- **Safety**: No silent failures or hallucinated responses

**Error categories and responses**:

| Scenario | User Query | Agent Response |
|----------|-----------|-----------------|
| Grafana unavailable | "Show me dashboards" | "Unable to connect to Grafana. Please check your configuration and ensure the MCP server is running." |
| Out-of-scope request | "Analyze my metrics" | "I can only retrieve dashboard information. I cannot analyze metrics, detect anomalies, or make recommendations." |
| Empty/malformed query | "" or "(invalid)" | "Please provide a query about dashboards, e.g., 'Show me all dashboards' or 'List dashboards with prod in the name'" |
| Partial/corrupted response | Query succeeds, Grafana returns incomplete data | "Grafana returned incomplete data. Please try again or contact your administrator." |

**Implementation pattern**:
```python
@node.as_runnable()
def agent_node(state):
    try:
        llm_response = llm.invoke(...)  # May fail if no MCP connection
        parsed = parse_response(llm_response)
        return {"response": format_output(parsed), "status": "success"}
    except GrafanaConnectionError as e:
        return {"response": "Unable to connect to Grafana. [details]", "status": "error"}
    except OutOfScopeError as e:
        return {"response": "I can only retrieve dashboard information. [details]", "status": "out_of_scope"}
```

**References**:
- User input: "Handle invalid or unsupported queries gracefully"
- Spec FR-006, FR-007: "Agent MUST return clear error messages when queries are out of scope or Grafana is unreachable"
- Constitution Principle IV (Accuracy & Clarity): "Error messages must be explicit and actionable"

---

## Technology Stack Summary

| Layer | Technology | Justification |
|-------|-----------|---------------|
| **Language** | Python 3.10+ | Standard for LLM/agent development; good LangGraph/LangChain support |
| **Agent Framework** | LangGraph | User requirement; demonstrates state machine patterns for agents |
| **LLM Interface** | LangChain | Abstracts OpenAI/Ollama; consistent ChatInterface |
| **LLMs** | OpenAI gpt-4-turbo, Ollama llama2 | User requirements; both accessible to developers |
| **UI** | Gradio ChatInterface | User requirement; minimal boilerplate |
| **Grafana Integration** | MCP client (stdio) | User requirement; demonstrates MCP pattern |
| **Config** | pydantic + python-dotenv | Standard Python pattern; simple and type-safe |
| **Testing** | pytest | Standard Python test framework; critical path integration tests |

---

## Design Decisions Not Made (Deferred)

The following are explicitly deferred to Phase 2 (task planning) or future work:

1. **Database/Persistence**: Not required; specification explicitly out of scope
2. **Logging/Monitoring**: Future enhancement; not in MVP
3. **API endpoint** (e.g., `/query`): Local demo only; no server deployment initially
4. **Caching**: Not needed; each query hits Grafana directly
5. **Query optimization**: Single-user local demo; no performance tuning needed
6. **Authentication**: Uses Grafana credentials from config; no separate auth layer
7. **Multi-language support**: English only (specification requirement)
8. **Frontend framework** (e.g., React): Gradio handles UI; no custom frontend needed

---

## Conclusion

All technical decisions are driven by:
- **User input** (explicit requirements from feature specification)
- **Project constitution** (learning-first, minimal code, safe extensibility)
- **Specification** (clear acceptance criteria and success measures)

No external research or clarification needed. Design is complete and ready for Phase 1 implementation.

**Next phase**: Generate data models, API contracts, and quickstart guide.
