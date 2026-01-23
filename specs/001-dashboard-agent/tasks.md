---
description: "Task list for Grafana Dashboard Agent feature implementation"
---

# Tasks: Grafana Dashboard Agent (001-dashboard-agent)

**Input**: Design documents from `specs/001-dashboard-agent/`
**Prerequisites**: ✅ plan.md, ✅ spec.md, ✅ research.md, ✅ data-model.md, ✅ contracts/

**Tests**: Optional per Constitution V (Pragmatic Testing). Critical path tests included; comprehensive coverage not mandated.

**Organization**: Tasks grouped by user story (P1 MVP + P2 enhancements) to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[ID]**: Sequential task identifier (T001, T002, etc.)
- **[P]**: Marks parallelizable tasks (independent files, no dependencies on incomplete tasks)
- **[Story]**: User story label (US1, US2, US3) for story-specific phases
- **Description**: Clear action with exact file paths

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root (per Constitution VI)
- Paths assume flat structure: `src/module.py`, not `src/module/init.py`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependencies, structure

- [ ] T001 Create project structure: `src/`, `tests/`, configuration files per plan.md
- [ ] T002 [P] Initialize Python project with pyproject.toml (dependencies: langgraph, langchain, gradio, langsmith, pydantic, python-dotenv)
- [ ] T003 [P] Create `.env.example` template with all configuration variables (GRAFANA_*, LLM_*, LANGSMITH_*, GRADIO_*)
- [ ] T004 [P] Configure linting and formatting tools (ruff, black) in pyproject.toml
- [ ] T005 Create README.md with project overview, quickstart reference, and architecture overview

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure required before any user story implementation

**⚠️ CRITICAL**: All Phase 2 tasks MUST complete before user story work begins

- [ ] T006 [P] Implement configuration management in `src/config.py` (pydantic.Settings, env var loading, defaults, validation; LLM_PROVIDER defaults to OpenAI per Q2)
- [ ] T007 [P] Create data models in `src/models.py` (Dashboard, Query, AgentMessage pydantic models with validation rules)
- [ ] T008 [P] Implement Grafana MCP tool wrapper in `src/tools.py` (MCP server discovery, JSON I/O, error handling; fail-fast on error per Q5, no subprocess management per Q1)
- [ ] T009 [P] Implement LLM initialization in `src/llm.py` (OpenAI (gpt-4) as primary; Ollama (mistral) as optional fallback per Q2)
- [ ] T010 Create system prompt constant in `src/agent.py` skeleton (includes scope boundaries, error patterns per research.md)
- [ ] T011 [P] Setup error handling module in `src/errors.py` (custom exception types, error message formatting)
- [ ] T012 Setup LangSmith integration in `src/config.py` (client initialization, callback configuration via env vars)

**Checkpoint**: Configuration, models, tools, and LLM ready. Agent implementation can now begin.

---

## Phase 3: User Story 1 - Query Dashboards via Natural Language (Priority: P1) 🎯 MVP

**Goal**: Engineer can ask natural language questions ("Show me all dashboards") and receive formatted dashboard lists from Grafana via single-node LangGraph agent.

**Independent Test**: Start Gradio interface → submit "Show me all dashboards" → verify formatted list matches Grafana → confirm <5s response time (SC-002).

### Tests for User Story 1 (Optional, critical path only)

- [ ] T013 [P] [US1] Unit test Grafana tool wrapper with mock MCP server in `tests/test_tools.py` (success case, error cases, timeout)
- [ ] T014 [P] [US1] Unit test configuration loading in `tests/test_config.py` (env vars, .env file, defaults, validation errors)
- [ ] T015 [P] [US1] Integration test agent node with mock LLM in `tests/test_agent.py` (query → LLM → tool call → formatted response)

### Implementation for User Story 1

- [ ] T016 [P] [US1] Implement single-node LangGraph agent in `src/agent.py` (StateGraph, agent node function, LLM + tool calling, error handling)
- [ ] T017 [P] [US1] Implement Gradio chat interface in `src/interface.py` (ChatInterface component, query input, response display, message history)
- [ ] T018 [US1] Create application entry point in `src/main.py` (load config, initialize agent + Gradio, launch interface with LangSmith callback)
- [ ] T019 [US1] Implement response formatting in `src/agent.py` (convert Dashboard list to Markdown with metadata only: ID, title, tags, folder, updated, URL per Q4; handle empty lists)
- [ ] T020 [US1] Add performance monitoring to agent node (measure response time, log to LangSmith, enforce <10s timeout)
- [ ] T021 [US1] Document agent workflow in README.md (dataflow diagram, example interaction flow, reference to contracts/)

**Checkpoint**: User Story 1 complete. Engineer can clone repo → set OPENAI_API_KEY / OLLAMA_URL → python src/main.py → interact with agent.

---

## Phase 4: User Story 2 - Handle Invalid or Unsupported Queries (Priority: P2)

**Goal**: Agent recognizes out-of-scope queries (metrics, anomalies, recommendations) and returns clear, actionable error messages per spec scope boundaries.

**Independent Test**: Submit "Show me CPU trends" → receive error "I can list dashboards, but metrics queries are not yet supported" → confirm no partial data returned (SC-003).

### Tests for User Story 2 (Optional, critical path only)

- [ ] T022 [P] [US2] Unit test LLM scope classification in `tests/test_agent.py` (valid query scope, unsupported metrics query, unsupported anomaly query, recommendations rejection)
- [ ] T023 [P] [US2] Integration test error path in `tests/test_agent.py` (submit unsupported query → verify error message clarity, no Grafana call made, <5s response)

### Implementation for User Story 2

- [ ] T024 [US2] Enhance system prompt in `src/agent.py` with detailed scope boundaries (metrics, anomalies, recommendations, future scopes) per research.md findings
- [ ] T025 [US2] Implement query intent classification in `src/agent.py` (LLM extracts Query.scope: all_dashboards|unsupported)
- [ ] T026 [US2] Add conditional routing in agent node: valid queries → call MCP tool once, invalid queries → return error message per FR-006; fail-fast on MCP error per Q5 (no retries)
- [ ] T027 [US2] Create error message templates in `src/errors.py` (metrics, anomalies, recommendations, unsupported patterns with helpful guidance)
- [ ] T028 [US2] Log unsupported queries to LangSmith for analysis in `src/agent.py` (track scope rejections for future feature planning)
- [ ] T029 [US2] Update Gradio interface examples in `src/interface.py` to include unsupported query examples (demonstrate error handling)

**Checkpoint**: User Story 1 + 2 complete. Agent handles both valid (dashboard list) and invalid (clear errors) queries per spec.

---

## Phase 5: User Story 3 - Configure Grafana Connection (Priority: P2)

**Goal**: Engineer can configure custom Grafana instance via environment variables without code changes; supports local dev defaults, staging, production.

**Independent Test**: Set GRAFANA_URL=custom-grafana-url, GRAFANA_PASSWORD=pwd → start agent → verify connection to custom instance, correct org_id filtering, no credentials in logs (SC-001, SC-006).

### Tests for User Story 3 (Optional, critical path only)

- [ ] T030 [P] [US3] Unit test configuration with custom Grafana URL in `tests/test_config.py` (env var override, validation, error on bad URL)
- [ ] T030b [P] [US3] Integration test MCP tool with custom Grafana in `tests/test_tools.py` (connect to custom URL, fetch dashboards, verify org_id filtering)

### Implementation for User Story 3

- [ ] T031 [US3] Ensure GRAFANA_* config variables fully implemented in `src/config.py` (GRAFANA_URL, USERNAME, PASSWORD, ORG_ID, with documented defaults)
- [ ] T032 [P] [US3] Implement Grafana MCP subprocess spawning in `src/tools.py` with config (use configured URL, pass credentials securely via stdin)
- [ ] T033 [US3] Add connection health check in `src/config.py` on startup (verify Grafana reachable before agent starts, fail-fast with clear error)
- [ ] T034 [US3] Implement org_id filtering in `src/tools.py` (MCP tool only returns dashboards for configured org, not all orgs)
- [ ] T035 [US3] Add credential handling security in `src/tools.py` (never log passwords, mask in error messages, use environment variables not hardcoded)
- [ ] T036 [US3] Update `src/main.py` startup sequence to validate Grafana connection before launching Gradio
- [ ] T037 [US3] Update `.env.example` with Grafana customization examples (local dev defaults + staging example)
- [ ] T038 [US3] Document multi-environment setup in README.md (local, staging, production examples with env var patterns)

**Checkpoint**: All user stories complete. System is production-ready for multi-environment deployment with flexible Grafana configuration.

---

## Phase 6: Integration & Observability

**Purpose**: End-to-end testing, observability setup, LangGraph CLI integration

- [ ] T039 [P] Setup LangSmith callback in `src/main.py` (initialize client, register callback if LANGSMITH_API_KEY set, log all interactions)
- [ ] T040 [P] Create langgraph.json configuration for LangGraph CLI in repository root (enable `langgraph dev` inspection)
- [ ] T041 [US1] End-to-end test: Run full workflow from `quickstart.md` (clone, setup, first query, verify response in <5s)
- [ ] T042 [US2] End-to-end test: Invalid query error path (submit unsupported query, verify error message)
- [ ] T043 [US3] End-to-end test: Custom Grafana configuration (set env vars, connect to different instance, verify data matches)
- [ ] T044 [P] Create test Grafana dashboard helper (script to populate test Grafana with sample dashboards for testing)
- [ ] T045 Verify LangSmith observability (run agent, check LangSmith dashboard for trace with query → LLM → tool → response)
- [ ] T046 Verify LangGraph CLI (run `langgraph dev`, inspect agent graph visually, test query interactively)

**Checkpoint**: Full integration tested, observability verified, system ready for user testing.

---

## Phase 7: Documentation & Polish

**Purpose**: Complete user-facing documentation, troubleshooting, code quality

- [ ] T047 [P] Add docstrings to all modules (src/agent.py, src/tools.py, src/interface.py, src/config.py, src/models.py per PEP 257)
- [ ] T048 [P] Create `CONTRIBUTING.md` guide (how to extend agent for future user stories, tool interface stability note)
- [ ] T049 [P] Create `TROUBLESHOOTING.md` from quickstart.md (common issues, solutions, debug steps with LangSmith reference)
- [ ] T050 [P] Add logging throughout codebase (config loading, LLM calls, MCP tool calls, errors) using Python logging module; redact sensitive fields (passwords, API keys) in normal logs; log full context only in error paths per Q3
- [ ] T051 Update quickstart.md with final paths and tested commands (validate all examples work end-to-end)
- [ ] T052 Create `ARCHITECTURE.md` (reference contracts/, data-model.md, explain component responsibilities)
- [ ] T053 Add type hints to all functions in src/ (enable pyright/mypy static analysis)
- [ ] T054 Run linting/formatting (ruff check, black format) across codebase, fix violations
- [ ] T055 [P] Create example .env files for OpenAI and Ollama configurations
- [ ] T056 Final code review: verify Principles I–VI from constitution (minimalism, extensibility, accuracy, no hardcoded creds, etc.)

**Checkpoint**: Production-ready codebase with comprehensive documentation, error handling, observability, and code quality.

---

## Phase 8: Learning Validation & Handoff

**Purpose**: Ensure engineers can learn from codebase; prepare for future expansion

- [ ] T057 Verify quickstart.md is end-to-end reproducible (fresh clone → 15 min to first query)
- [ ] T058 Create architecture learning guide (explain LangGraph single-node pattern, how to extend for P2 stories, tool interface stability)
- [ ] T059 Document extension points for future features (where to add metrics queries, multi-dashboard operations, etc. per Principle III)
- [ ] T060 Create `ROADMAP.md` (P1 delivered, future P2 scopes: search_dashboards, get_specific, then Phase 2: metrics querying)
- [ ] T061 Validate no Constitution violations (code adheres to Principles I–VI, no over-engineering, minimal dependencies)
- [ ] T062 Prepare deployment checklist (what's needed beyond MVP for production: security review, rate limiting, audit logs, etc.)

**Checkpoint**: System is ready for handoff to engineers for learning and future expansion.

---

## Dependency Graph & Parallelization Strategy

### Parallel Execution Example (Phase 2 Foundational):

```
T006 (config.py) ─────┐
T007 (models.py) ├─→ T010 (agent.py) → T018 (Gradio) → T021 (observability)
T008 (tools.py) ──┤
T009 (llm.py) ────┤
T011 (errors.py) ─┤
T012 (LangSmith) ─┘
```

All Phase 2 tasks with `[P]` can run in parallel; final agent skeleton (T010) depends on them.

### Parallel Execution Example (Phase 1 Setup):

```
T002 (pyproject.toml)
T003 (.env.example)    ───→ T005 (README) [can start in parallel, complete after T002]
T004 (linting)
```

### Critical Path (Sequential):

1. **Phase 1**: T001 → T002 → (T003, T004 parallel) → T005
2. **Phase 2**: (T006–T009, T011–T012 parallel) → T010
3. **Phase 3 US1**: (T013–T015 parallel) → T016–T017 → T018 → T019–T021 (last 2 parallel)
4. **Phase 4 US2**: (T022–T023 parallel) → T024–T028 → T029
5. **Phase 5 US3**: (T030–T030b parallel) → T031–T038 (some parallelizable)
6. **Phases 6–8**: After all user stories complete

### Total Estimated Duration:

- Phase 1: 2–3 hours
- Phase 2: 4–6 hours (core infrastructure)
- Phase 3 (US1 MVP): 6–8 hours
- Phases 4–5 (US2, US3): 6–8 hours
- Phases 6–8 (integration, polish): 4–6 hours
- **Total MVP (Phase 1–3): 12–17 hours**
- **Full feature (Phase 1–8): 24–30 hours**

---

## Success Criteria Per Phase

| Phase | Completion Criteria |
|-------|---------------------|
| **1** | Project structure exists, dependencies installable |
| **2** | Config loads from env vars, models validate, LLM initializes, MCP tool wrapper ready |
| **3** | User queries work end-to-end, response <5s, formatted output matches Grafana |
| **4** | Invalid queries return clear errors, no partial data, no fabrication |
| **5** | Grafana connection configurable, custom URLs work, credentials secure |
| **6** | All interactions logged in LangSmith, `langgraph dev` works |
| **7** | Docstrings complete, code linted, troubleshooting guide ready |
| **8** | Quickstart reproducible, no Constitution violations, ready for learning & extension |

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| **LLM may misinterpret queries** | System prompt includes detailed scope boundaries + examples; test with multiple LLM models |
| **MCP server unreachable** | Health check on startup; clear error message to user; retry logic in tool wrapper |
| **Performance exceeds 5s** | Profile LLM call, MCP call, formatting; cache Grafana list if needed; set hard timeout |
| **Credentials leak in logs** | Mask passwords in config validation; never log env vars; use LangSmith secret filtering |
| **Grafana API changes** | Keep MCP tool wrapper thin; stable interface documented in contracts/ |
| **Test coverage gaps** | Focus on critical paths (LLM, MCP, Gradio); pragmatic testing per Constitution V |

---

## Acceptance Criteria Summary

**MVP Complete** (Phase 1–3):
- ✅ Engineer clones repo, sets OPENAI_API_KEY, runs python src/main.py
- ✅ Gradio interface opens with chat
- ✅ Query "Show me all dashboards" returns formatted list in <5s
- ✅ Response matches actual Grafana dashboard list
- ✅ All interactions logged in LangSmith (if API key set)
- ✅ No hardcoded credentials
- ✅ No autonomous actions, no memory, no insights
- ✅ Single-node LangGraph agent (extensible for future multi-node)

**Full Feature Complete** (Phase 1–8):
- ✅ All user stories (P1, P2, P2) implemented and tested
- ✅ Error handling for out-of-scope queries with clear messages
- ✅ Configurable Grafana connection (custom URLs, orgs)
- ✅ Production-ready code (docstrings, type hints, linting, logging)
- ✅ Comprehensive documentation (README, quickstart, architecture, troubleshooting)
- ✅ Observability complete (LangSmith traces, LangGraph CLI)
- ✅ Constitutional compliance verified (Principles I–VI)
- ✅ Ready for learning & future expansion

---

## Task Execution Tips

1. **Phase 2 First**: All foundational tasks (T006–T012) must complete before user story work. Prioritize config, models, tools, LLM.

2. **Parallel Where Possible**: Tasks marked with `[P]` have no dependencies; run in parallel to save time.

3. **Test-First (Optional)**: Tests in Phases 3–5 are optional per Constitution V. If including tests, write them BEFORE implementation (T013 before T016, etc.).

4. **Validate Frequently**: After each phase checkpoint, run quickstart.md steps to ensure no regressions.

5. **LangSmith Early**: Set LANGSMITH_API_KEY from Phase 3 onward to see traces during development (invaluable for debugging LLM behavior).

6. **Use Contracts**: Reference contracts/ directory (agent-interface.md, grafana-mcp.md, config-schema.json) during implementation to ensure compliance.

---

## Notes for Implementers

- **Constitution Compliance**: All code must respect Principles I–VI. No over-engineering, no autonomous actions, secure configuration.
- **Extensibility**: Single-node agent design is minimal but designed for Phase 2 multi-node expansion. Keep tool interface stable.
- **Learning Focus**: Per Constitution V, priority is understanding LangGraph + MCP integration, not test coverage. Test critical paths only.
- **Pragmatic Defaults**: Use sensible defaults for local dev (Grafana localhost:3000, OpenAI gpt-4). Externalize for other environments.
- **Error Boundaries**: System prompt and scope classification prevent out-of-scope queries. Test with the 4 scope types (all_dashboards, search, specific, unsupported).
