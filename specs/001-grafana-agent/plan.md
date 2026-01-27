# Implementation Plan: Grafana Agent for Dashboard Discovery

**Branch**: `001-grafana-agent` | **Date**: 2026-01-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-grafana-agent/spec.md`

## Summary

Build a single-node LangGraph agent that accepts natural language queries about Grafana dashboards and returns formatted lists via a Gradio chat interface. The agent uses LLMs (OpenAI/Ollama) to interpret queries and the Grafana MCP server exclusively for backend integration. Core MVP: enable "Show me all dashboards" query with graceful error handling for connection failures and out-of-scope requests.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: LangGraph, LangChain, Gradio, pydantic (for config); OpenAI and Ollama for LLM support  
**Storage**: N/A (no persistence between sessions)  
**Testing**: pytest for integration tests; unit tests optional if they don't advance learning  
**Target Platform**: Linux/macOS local development; runs in Docker environment with Grafana  
**Project Type**: Single Python application (CLI + local UI)  
**Performance Goals**: Query-to-response within 5 seconds; no concurrent user requirements (single local user)  
**Constraints**: Must operate on existing Docker Observability stack; no changes to metric storage/ingestion; no hardcoded credentials  
**Scale/Scope**: Single-user learning application; 0-2 dashboards initially (scales to 100+ dashboards in real Grafana instances)

## Constitution Check

**GATE 1: Principle Alignment**
- ✅ **Purpose (Education)**: Single-node agent design demonstrates core LangGraph/LLM patterns
- ✅ **Minimalism**: No analysis, insights, or autonomous actions; query → retrieve → return
- ✅ **Extensibility**: Single-node architecture designed for future node additions without refactoring
- ✅ **Accuracy & Clarity**: All responses grounded in actual Grafana data via MCP
- ✅ **Pragmatic Testing**: Integration tests required; unit test coverage optional
- ✅ **Simplistic Structure**: Flat src/ layout; no premature subdirectories
- ✅ **Minimal Code**: Single-node agent, Gradio UI, minimal tool wrapper—nothing extra

**GATE 2: Technology Constraints**
- ✅ **LangGraph**: Single-node only (no multi-node orchestration)
- ✅ **LLM**: OpenAI + Ollama supported
- ✅ **Grafana Integration**: MCP server exclusively (no direct API calls)
- ✅ **Configuration**: Environment variables + optional config file; no hardcoded secrets
- ✅ **UI**: Gradio for local demo (not production)

**GATE 3: Scope Validation**
- ✅ **In Scope**: Dashboard listing, filtering, error handling, Grafana MCP integration
- ✅ **Out of Scope**: Metrics analysis, anomaly detection, recommendations, multi-session memory, complex orchestration
- ✅ No scope creep indicators in user input

**GATE STATUS**: ✅ **PASS** - All gates satisfied. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-grafana-agent/
├── spec.md                          # Feature specification
├── plan.md                          # This file (implementation plan)
├── research.md                      # Phase 0 output (NEXT)
├── data-model.md                    # Phase 1 output (NEXT)
├── quickstart.md                    # Phase 1 output (NEXT)
├── contracts/                       # Phase 1 output (NEXT)
│   └── agent_interface.md           # LangGraph node input/output spec
└── checklists/
    └── requirements.md              # Specification validation (complete)
```

### Source Code (repository root)

```text
src/
├── main.py                          # Gradio chat interface entry point
├── agent.py                         # Single-node LangGraph agent
├── tools.py                         # Grafana MCP query tool wrapper
├── config.py                        # Configuration management
└── llm.py                           # LLM initialization (OpenAI/Ollama)

tests/
├── test_agent.py                    # Integration tests for agent
├── test_grafana_integration.py      # Grafana MCP integration tests
└── test_error_handling.py           # Error path testing

config/
├── .env.example                     # Template for environment variables
└── config.yaml                      # Optional configuration file template
```

---

## Phase 0: Research & Requirements Clarification

**Status**: ✅ Complete - No clarifications needed

### Research Findings

All technical decisions specified by user input and constitution. No unknowns requiring external research.

#### 1. LangGraph Single-Node Design
**Decision**: Single-node graph executing query → LLM → response pipeline
**Rationale**: Meets minimal code, education-first principles. Demonstrates core LangGraph patterns without orchestration complexity.
**Implementation**: 
- Node accepts StateDict with `{"query": str, "response": str}`
- Node calls LLM with system prompt constraining scope
- Node returns formatted response or error message
**Future Expansion**: Additional nodes can be added (e.g., web search, metric correlation) without refactoring node interface

#### 2. Gradio Chat Interface
**Decision**: Simple Gradio ChatInterface for user input/output
**Rationale**: Lightweight, no external dependencies, demo-suitable. Meets "simple enough to try without context" constraint.
**Implementation**: ChatInterface with text input, agent callback, message history display
**Scope**: Stateless interface (no conversation persistence between sessions)

#### 3. Grafana MCP Server Integration
**Decision**: Communicate exclusively via MCP server (Docker-based)
**Rationale**: Meets constraint "talking to grafana can only be done via Grafana MCP server"
**Tool Wrapper**: 
```python
class GrafanaTool:
    def __init__(self, mcp_config: MCPConfig):
        # Initialize MCP client from config
    
    def list_dashboards(self):
        # Call MCP server list_dashboards endpoint
    
    def get_dashboard_by_uid(self, uid: str):
        # Call MCP server get_dashboard endpoint
```

#### 4. LLM Support (OpenAI & Ollama)
**Decision**: Support both via LangChain's ChatOpenAI and ChatOllama
**Rationale**: Enables learning with both cloud (OpenAI) and local (Ollama) LLMs
**Configuration**: 
- Environment variable: `LLM_PROVIDER` (openai|ollama)
- Provider-specific vars: `OPENAI_API_KEY`, `OLLAMA_BASE_URL`
- Default model: OpenAI gpt-4-turbo (can override via env)

#### 5. Configuration Management
**Decision**: Environment variables + optional YAML config
**Rationale**: No hardcoded credentials; simple setup for local dev
**Config Hierarchy**: Defaults → environment variables → config.yaml
**Required for local dev**:
```env
GRAFANA_URL=http://localhost:3000
GRAFANA_USERNAME=mopadmin
GRAFANA_PASSWORD=moppassword
GRAFANA_ORG_ID=1
LLM_PROVIDER=ollama  # or openai
OPENAI_API_KEY=sk-... (if using OpenAI)
OLLAMA_BASE_URL=http://localhost:11434 (if using Ollama)
```

#### 6. Error Handling Strategy
**Decision**: Try-except at node level + user-facing error messages
**Rationale**: Prevents silent failures; teaches robust agent design for learning
**Error Categories**:
- **Connection errors** (Grafana unavailable): "Unable to connect to Grafana. Please check your configuration."
- **Out-of-scope queries** (metrics analysis): "I can only retrieve dashboard information, not analyze metrics."
- **Invalid queries** (empty/malformed): "Please provide a valid query about dashboards."
- **MCP response errors** (partial data): "Grafana returned incomplete data. Please try again."

### Deliverable

➜ [research.md](research.md) generated (see file above)

---

## Phase 1: Design & Architecture

### Design: Data Model

**Entities** (from spec, implementation-agnostic):

1. **Dashboard Entity**
   - id: str (UUID from Grafana)
   - title: str (dashboard name)
   - uid: str (unique identifier)
   - updated: datetime (last modification)
   - tags: List[str] (optional labels)
   - folderTitle: str (folder name)
   - orgId: int (organization)

2. **Query Entity**
   - user_input: str (raw text from engineer)
   - intent: str (parsed intent: "list_dashboards", "filter_dashboards", "get_dashboard_info")
   - filters: Dict[str, str] (extracted filters: name_contains, tag_contains, etc.)

3. **Response Entity**
   - status: "success" | "error" | "out_of_scope"
   - data: Union[List[Dashboard], str] (formatted results or error message)
   - raw_llm_output: str (for debugging)

### Design: API Contracts

**LangGraph Node Interface** (single node)

Input:
```python
state = {
    "query": "Show me all dashboards",
    "context": {},  # Optional additional context
}
```

Output:
```python
state = {
    "query": str,
    "response": str,  # Formatted text response for user
    "parsed_intent": Optional[str],
    "status": "success" | "error" | "out_of_scope",
}
```

**Grafana Tool Interface** (wrapper around MCP)

```python
class GrafanaMCPTool:
    async def list_dashboards() -> List[DashboardMetadata]
    async def get_dashboard(uid: str) -> DashboardMetadata
    async def search_dashboards(query: str) -> List[DashboardMetadata]
```

**System Prompt for LLM**

```
You are an agent that helps engineers retrieve information about Grafana dashboards.

CAPABILITIES:
- List all available dashboards
- Filter dashboards by name or tags
- Retrieve basic dashboard metadata (title, last updated, tags)

RESTRICTIONS:
- You CANNOT analyze metrics, detect anomalies, or explain metric behavior
- You CANNOT make recommendations or provide predictions
- You only retrieve and display data as-is from Grafana
- If asked about metrics, query interpretation, or predictions, clearly explain you cannot do that

USER QUERY: {query}

Return a clear, formatted response with the requested information.
```

### Design: Quickstart

**Quickstart** (quickstart.md): Setup instructions for local dev

1. Clone repository and cd to root
2. Install Python 3.10+: `python --version` (check)
3. Create virtual environment: `python -m venv .venv && source .venv/bin/activate`
4. Install dependencies: `pip install -e .` (uses setup.py/pyproject.toml)
5. Configure Grafana (provide .env.example template):
   ```bash
   cp config/.env.example .env
   # Edit .env with Grafana Docker credentials
   ```
6. Start Grafana (docker-compose up -d grafana) or use existing Docker stack
7. Run agent: `python src/main.py`
8. Open Gradio UI at `http://localhost:7860`
9. Submit query: "Show me all dashboards"
10. Expected output: Numbered list of dashboards with titles

**Troubleshooting section** covers:
- MCP server connection errors
- LLM provider issues
- Docker network errors

### Design: Contracts

Create [contracts/agent_interface.md](contracts/agent_interface.md) documenting:
- LangGraph node state schema
- Grafana MCP tool interface
- System prompt for LLM
- Error response formats

### Deliverables

Generated files:

1. ✅ [data-model.md](data-model.md) - Entity definitions
2. ✅ [contracts/](contracts/) - API contracts
3. ✅ [quickstart.md](quickstart.md) - Local setup guide

### Phase 1: Update Agent Context

Run context update script to inform agent of technology stack:

```bash
.specify/scripts/bash/update-agent-context.sh copilot
```

This updates `.github/copilot-context.md` with:
- LangGraph single-node architecture
- Gradio UI framework
- Grafana MCP server integration
- Configuration via environment variables
- OpenAI and Ollama LLM support

### Constitution Re-Check (Post-Design)

**GATE 1: Principle Alignment (Design Verification)**
- ✅ Single-node LangGraph confirmed in architecture
- ✅ No analysis/insights in LLM system prompt
- ✅ Minimal code: Gradio + single node + tool wrapper
- ✅ All responses from actual Grafana via MCP
- ✅ No persistence design implemented

**GATE 2: Technology Constraints (Design Verification)**
- ✅ LangGraph single-node confirmed
- ✅ OpenAI/Ollama support designed
- ✅ Grafana MCP exclusive (no direct API calls)
- ✅ Environment variable configuration
- ✅ Gradio UI scoped to demo

**GATE 3: Extensibility Verification**
- ✅ Single-node state dict design allows future node additions
- ✅ Grafana tool interface stable
- ✅ System prompt can be extended without refactoring
- ✅ LLM provider abstraction supports additions

**GATE STATUS**: ✅ **PASS** - Design compliant with constitution. Ready for Phase 2.

---

## Deployment & Runability

**Local Development**:
- Requires Python 3.10+, Docker (for Grafana)
- Clone repo → `pip install -e .` → `python src/main.py`
- Gradio UI auto-opens at localhost:7860
- Configurable via .env file

**Docker Compose** (future):
- Can containerize agent for consistent deployment
- Not required for MVP (local demo acceptable)

**Configuration**:
- Defaults: localhost:3000, mopadmin/moppassword (for Docker dev)
- Override: environment variables or config.yaml
- Zero hardcoded credentials

---

## Next Steps

Proceed to `/speckit.tasks` to generate task breakdown organized by user story (P1 → P2a → P2b priority order).

**Summary of Artifacts Generated**:
- ✅ plan.md (this file) - Technical approach and architecture
- ✅ research.md - Research findings (no unknowns)
- ✅ data-model.md - Entity definitions
- ✅ contracts/agent_interface.md - API contracts
- ✅ quickstart.md - Local setup guide
- ✅ Constitution re-check (all gates pass)
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
