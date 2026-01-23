# Tasks: Grafana Agent for Dashboard Discovery

**Input**: Design documents from `/specs/001-grafana-agent/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Format**: `- [ ] [TaskID] [P?] [Story?] Description with file path`

**Organization**: Tasks grouped by user story (P1, P2a, P2b) to enable independent implementation and testing.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and core dependencies

- [ ] T001 Create project structure per implementation plan
- [ ] T002 [P] Initialize Python 3.10+ project with pyproject.toml or setup.py
- [ ] T003 [P] Create core package structure (src/, tests/, config/)
- [ ] T004 [P] Setup virtual environment and dependency management (.python-version, requirements.txt)
- [ ] T005 [P] Create config/.env.example template with Grafana and LLM defaults
- [ ] T006 [P] Create config/config.yaml template for optional YAML configuration
- [ ] T007 [P] Initialize pytest testing framework with conftest.py in tests/
- [ ] T008 Configure logging (logging.config or simple logging setup in src/config.py)

**Checkpoint**: Run `python -m pytest tests/ --collect-only` → confirms pytest is accessible

---

## Phase 2: Foundational (Blocking Prerequisites for All User Stories)

**Purpose**: Core infrastructure that MUST be complete before any user story implementation

- [ ] T009 Implement configuration management in src/config.py (load from env, YAML, defaults; pydantic model)
- [ ] T010 [P] Implement LLM provider initialization in src/llm.py (OpenAI + Ollama support; configurable at runtime)
- [ ] T011 [P] Implement Grafana MCP tool wrapper in src/tools.py (GrafanaMCPTool class with list_dashboards, search_dashboards, get_dashboard methods)
- [ ] T012 Implement error handling utilities in src/tools.py (GrafanaError, GrafanaConnectionError, GrafanaAuthError, GrafanaDataError exception hierarchy)
- [ ] T013 Implement single-node LangGraph agent structure in src/agent.py (create_agent() function returns compiled graph)
- [ ] T014 Implement LLM system prompt in src/agent.py (constraints: dashboard retrieval only, no analysis/insights/recommendations)
- [ ] T015 Implement Gradio chat interface foundation in src/main.py (ChatInterface wrapper, message handling)
- [ ] T016 Create integration test fixtures in tests/conftest.py (mock Grafana MCP responses, mock LLM responses)

**Checkpoint**: Run `python -c "from src.config import load_config; from src.llm import create_llm; from src.tools import GrafanaMCPTool; from src.agent import create_agent"` → all imports succeed

---

## Phase 3: User Story 1 - List All Dashboards (Priority: P1)

**Goal**: Engineer can ask "Show me all dashboards" and receive a formatted list

**Independent Test**: Start agent → submit query "Show me all dashboards" → verify response contains formatted dashboard list with titles

### Acceptance Scenarios

1. **Given** Grafana has 3+ dashboards, **When** user asks "Show me all dashboards", **Then** returns all dashboards with titles in readable text
2. **Given** Grafana has no dashboards, **When** user asks "Show me all dashboards", **Then** returns "No dashboards found"
3. **Given** agent running, **When** user asks "What dashboards are available?", **Then** interprets as equivalent to list query

### Implementation Tasks

- [ ] T017 [P] [US1] Implement list_dashboards() method in src/tools.py (calls MCP server; returns List[DashboardMetadata])
- [ ] T018 [US1] Implement agent node logic in src/agent.py (accept query → invoke LLM → interpret intent as "list_dashboards" → call tool → format response)
- [ ] T019 [US1] Implement response formatting in src/agent.py (convert List[Dashboard] to numbered list with titles; handle empty list case)
- [ ] T020 [P] [US1] Implement Gradio chat integration in src/main.py (wire agent to ChatInterface; handle input/output)
- [ ] T021 [US1] Test "Show me all dashboards" end-to-end in tests/test_agent.py (mock Grafana MCP; verify response format)
- [ ] T022 [US1] Test empty dashboard list in tests/test_agent.py (verify "No dashboards found" message)
- [ ] T023 [US1] Test query interpretation in tests/test_agent.py (verify LLM correctly interprets "What dashboards are available?" as list query)
- [ ] T024 [US1] Create demo script (demo.py) that runs agent with sample Grafana instance for manual testing

**Checkpoint**: `python demo.py` → Gradio UI responds to "Show me all dashboards" with formatted list; all T017-T023 tests pass

---

## Phase 4: User Story 2a - Query Multiple Dashboard Properties (Priority: P2)

**Goal**: Engineer can filter dashboards by name and retrieve metadata

**Independent Test**: Submit query with filter (e.g., "dashboards with 'prod' in name") → verify filtered results returned

### Acceptance Scenarios

1. **Given** dashboards with different names, **When** user asks "Show me dashboards with 'prod' in the name", **Then** returns only matching dashboards
2. **Given** dashboard exists, **When** user asks "When was [dashboard] last updated?", **Then** returns last update timestamp
3. **Given** no matches found, **When** user applies filter, **Then** returns "No dashboards match your criteria"

### Implementation Tasks

- [ ] T025 [P] [US2] Implement search_dashboards(query) method in src/tools.py (filters by name, tags; returns List[DashboardMetadata])
- [ ] T026 [US2] Extend agent node logic in src/agent.py (parse filter intent; call search_dashboards with extracted filter)
- [ ] T027 [US2] Implement filter extraction in src/agent.py (LLM extracts intent + filters from query; maps to tool calls)
- [ ] T028 [US2] Implement timestamp formatting in src/agent.py (format ISO 8601 datetime to readable format "YYYY-MM-DD HH:MM UTC")
- [ ] T029 [P] [US2] Extend response formatting in src/agent.py (include metadata: title, last updated, tags in response)
- [ ] T030 [P] [US2] Test filter by name in tests/test_agent.py (mock Grafana; submit "dashboards with 'prod'"; verify filtered results)
- [ ] T031 [US2] Test get dashboard metadata in tests/test_agent.py (verify timestamp and tag retrieval)
- [ ] T032 [US2] Test no results case in tests/test_agent.py (verify "No dashboards match your criteria" message)
- [ ] T033 [US2] Create filter examples in quickstart.md or demo script (document filtering patterns)

**Checkpoint**: All T025-T032 tests pass; demo script supports filtering queries

---

## Phase 5: User Story 2b - Graceful Error Handling (Priority: P2)

**Goal**: Agent handles errors and out-of-scope requests with clear messages

**Independent Test**: Submit out-of-scope query or break Grafana connection → verify agent returns appropriate error message

### Acceptance Scenarios

1. **Given** out-of-scope question like "Analyze metrics", **When** agent processes, **Then** returns "I can only retrieve dashboard information"
2. **Given** Grafana unreachable, **When** user submits query, **Then** returns "Unable to connect to Grafana"
3. **Given** empty query, **When** agent processes, **Then** returns "Please provide a query about dashboards"

### Implementation Tasks

- [ ] T034 [P] [US3] Implement error handling in src/tools.py (catch MCP errors; raise typed exceptions with user-friendly messages)
- [ ] T035 [US3] Implement out-of-scope detection in src/agent.py (LLM system prompt identifies unsupported requests; returns clear explanation)
- [ ] T036 [P] [US3] Implement timeout handling in src/agent.py (catch timeout errors from Grafana MCP; return "Query took too long" message)
- [ ] T037 [US3] Implement validation in src/main.py (check query is non-empty; return prompt if invalid)
- [ ] T038 [US3] Implement connection error messages in src/tools.py (GrafanaConnectionError → user-friendly message; check Grafana health)
- [ ] T039 [US3] Implement auth error messages in src/tools.py (GrafanaAuthError → prompt to verify credentials)
- [ ] T040 [P] [US3] Test out-of-scope query in tests/test_error_handling.py (submit "Analyze metrics"; verify error message)
- [ ] T041 [US3] Test Grafana connection failure in tests/test_grafana_integration.py (mock MCP timeout; verify error handling)
- [ ] T042 [US3] Test empty query in tests/test_error_handling.py (submit ""; verify validation message)
- [ ] T043 [US3] Test partial/corrupted data in tests/test_error_handling.py (mock Grafana returning incomplete response; verify error)
- [ ] T044 [US3] Test invalid credentials in tests/test_grafana_integration.py (mock auth failure; verify error message)

**Checkpoint**: All T034-T044 tests pass; error paths covered; agent never crashes on invalid input

---

## Phase 6: Integration & Cross-Cutting Concerns

**Purpose**: Ensure all user stories work together; polish and documentation

- [ ] T045 [P] Run full integration test suite against mock Grafana in tests/test_agent.py
- [ ] T046 [P] Run full integration test suite against mock LLM in tests/test_agent.py
- [ ] T047 Test all three user stories in sequence (US1 → US2 → US3) in tests/test_agent.py (verify state management across queries)
- [ ] T048 Update quickstart.md with examples covering all three user stories
- [ ] T049 Update quickstart.md troubleshooting section based on observed errors
- [ ] T050 [P] Run `python src/main.py` and verify Gradio UI works locally
- [ ] T051 Create .env.example with all required and optional variables clearly documented
- [ ] T052 Add inline code documentation to src/ modules (docstrings, type hints)
- [ ] T053 Add README.md at repository root (quick overview, link to spec and quickstart)
- [ ] T054 Verify all requirements from spec are implemented (FR-001 through FR-011 checklist)

**Checkpoint**: 
- All tests pass: `pytest tests/`
- Agent runs locally: `python src/main.py` → Gradio UI at localhost:7860
- All user story acceptance scenarios verified
- Documentation complete and accurate

---

## Dependency Graph & Execution Order

### Critical Path (Blocking)
```
T001-T008 (Setup)
    ↓
T009-T016 (Foundational)
    ↓
T017-T024 (US1: List Dashboards) ← MVP COMPLETE AT THIS POINT
    ↓
T025-T033 (US2a: Filtering)
    ↓
T034-T044 (US2b: Error Handling)
    ↓
T045-T054 (Integration & Polish)
```

### Parallelizable Phases

**Phase 1 (Setup)**: T001-T008 can all run in parallel (independent files/directories)

**Phase 2 (Foundational)**: 
- T009 (config.py) blocks all others
- T010 (llm.py) independent after T009
- T011-T012 (tools.py) independent after T009
- T013-T014 (agent.py foundation) independent after T009
- T015 (main.py foundation) independent after T009
- T016 (test fixtures) can run in parallel

Parallelization within Phase 2: After T009, run {T010, T011-T012, T013-T014, T015, T016} in parallel

**Phase 3 (US1)**: 
- T017 (list_dashboards) must complete before T018
- T018-T019 can run in parallel
- T020 independent after T018
- T021-T024 parallel after T018-T019

**Phase 4 (US2a)**: 
- T025 (search_dashboards) must complete before T026
- T026-T029 can run in parallel
- T030-T033 parallel after implementations

**Phase 5 (US2b)**:
- T034-T039 can run in parallel
- T040-T044 parallel after T034-T039

**Phase 6 (Integration)**:
- T045-T046 parallel
- T047 must wait for T045-T046
- T048-T054 can run in parallel

### Suggested MVP Scope (Minimal Viable Product)

**Phase 1**: T001-T008 (Project setup)
**Phase 2**: T009-T016 (Foundational infrastructure)  
**Phase 3**: T017-T024 (US1: List all dashboards)

→ After Phase 3, engineers have working MVP:
- Agent accepts "Show me all dashboards" query
- Returns formatted list from Grafana via MCP
- Runs in Gradio UI locally

**Phase 4-6**: P2 features and polish (can be done iteratively)

---

## Task Summary by Story

| User Story | P | Tasks | Acceptance Criteria |
|------------|---|-------|-------------------|
| US1: List Dashboards | P1 | T017-T024 (8 tasks) | Query "Show me all dashboards" → formatted list |
| US2a: Filtering | P2 | T025-T033 (9 tasks) | Query with filter → filtered results |
| US2b: Error Handling | P2 | T034-T044 (11 tasks) | Out-of-scope/error queries → clear messages |
| Setup | - | T001-T008 (8 tasks) | Project structure + dependencies |
| Foundational | - | T009-T016 (8 tasks) | Config, LLM, tools, agent, UI frameworks |
| Integration | - | T045-T054 (10 tasks) | Full system tests + documentation |

**Total Tasks**: 54
**Setup Phase**: 8 tasks (T001-T008)
**Foundational Phase**: 8 tasks (T009-T016)
**US1 Phase**: 8 tasks (T017-T024)
**US2a Phase**: 9 tasks (T025-T033)
**US2b Phase**: 11 tasks (T034-T044)
**Integration Phase**: 10 tasks (T045-T054)

---

## Testing Strategy

**Critical Path Integration Tests** (required):
- T021: List all dashboards (US1 core)
- T030: Filter dashboards (US2 core)
- T040: Out-of-scope handling (US3 core)
- T041: Connection error handling (US3 core)
- T045-T047: Full system integration

**Optional Unit Tests** (if they advance learning):
- Individual tool methods (GrafanaMCPTool)
- Config parsing (edge cases)
- Response formatting (edge cases)
- LLM prompt construction

**Manual Testing**:
- T050: Run Gradio UI locally
- Demo script (T024, T033): Interactive testing with mock/real Grafana

---

## Implementation Notes

### Task Scope & Clarity

Each task is specific enough for autonomous implementation:
- ✅ Tasks reference exact file paths (src/agent.py, tests/test_agent.py)
- ✅ Tasks specify methods/classes to implement (GrafanaMCPTool.list_dashboards)
- ✅ Tasks map to acceptance scenarios from spec
- ✅ Tests specify expected behavior (mock setup, assertions)

### File Path Conventions

- **Source**: `src/` (Python modules)
- **Tests**: `tests/` (pytest test files)
- **Config**: `config/` (.env, yaml templates)
- **Spec docs**: `specs/001-grafana-agent/` (reference only during implementation)

### Parallelization Strategy

Tasks marked with `[P]` can run in parallel (independent files, no blocking dependencies on incomplete tasks).

Example parallel execution:
```bash
# Phase 2, after T009:
# Terminal 1: T010 (llm.py)
# Terminal 2: T011-T012 (tools.py)
# Terminal 3: T013-T014 (agent.py)
# Terminal 4: T015 (main.py)
# Terminal 5: T016 (test fixtures)
# → All complete independently, then merge
```

---

## Validation Checklist

- [ ] All 54 tasks follow strict format: `- [ ] [ID] [P?] [Story?] Description + file path`
- [ ] All tasks have unique sequential IDs (T001-T054)
- [ ] Story labels correct ([US1], [US2], [US3] for story phases only)
- [ ] [P] markers accurate (parallel tasks verified)
- [ ] All file paths exact and workspace-relative
- [ ] No placeholder text ([NEEDS CLARIFICATION], [FIXME])
- [ ] Acceptance scenarios from spec reflected in task acceptance criteria
- [ ] Setup and Foundational phases complete before user stories
- [ ] Integration phase follows all feature implementation
- [ ] Dependency graph is acyclic
- [ ] MVP scope clearly identified (Phase 1-3)

---

## Suggested Commit

```bash
git add specs/001-grafana-agent/tasks.md
git commit -m "tasks: add task breakdown for grafana-agent implementation

Phase 1 (Setup): 8 tasks - project structure and dependencies
Phase 2 (Foundational): 8 tasks - config, LLM, tools, agent, UI
Phase 3 (US1): 8 tasks - list all dashboards MVP
Phase 4 (US2a): 9 tasks - filter dashboards
Phase 5 (US2b): 11 tasks - graceful error handling
Phase 6 (Integration): 10 tasks - full system tests and polish

Total: 54 tasks organized by user story
MVP: Phase 1-3 (24 tasks for working agent)
All tasks follow strict checklist format with file paths
Dependency graph and parallelization strategy documented"
```

---

## Ready for Implementation

✅ All design documents complete (spec, plan, research, data-model, contracts, quickstart)
✅ All 54 tasks defined with clear acceptance criteria
✅ Task format validated (checklist, IDs, story labels, file paths)
✅ Dependency graph verified (no circular dependencies)
✅ Parallelization opportunities identified
✅ MVP scope clearly marked
✅ Testing strategy defined (critical path + optional unit tests)

Proceed to `/speckit.implement` for implementation guidance.
