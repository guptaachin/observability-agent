# Tasks: Natural Language Metric Queries

**Input**: Design documents from `/specs/001-natural-language-metrics/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are REQUIRED per constitution (Testing is NON-NEGOTIABLE). Test-first approach: write tests before implementation, ensure tests fail initially, then implement.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (src/agent/, src/tools/, src/ui/, src/config/, tests/unit/, tests/integration/, tests/fixtures/)
- [ ] T002 Initialize Python project with dependencies (requirements.txt with gradio, langgraph, langchain, python-dotenv, pytest)
- [ ] T003 [P] Configure linting and formatting tools (setup black, flake8 or ruff)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement configuration management in src/config/settings.py (env vars, defaults, validation)
- [ ] T005 [P] Setup error handling and logging infrastructure (error types, user-friendly messages)
- [ ] T006 [P] Create test fixtures with sample metrics data in tests/fixtures/sample_metrics_data.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Query System Metrics with Natural Language (Priority: P1) 🎯 MVP

**Goal**: Enable engineers to ask questions about system metrics in natural language and receive metric data in readable format. Delivers complete end-to-end capability from natural language input to formatted metric output.

**Independent Test**: Ask a natural language question about system metrics (e.g., "Show CPU usage for the last hour"), verify the system interprets the question correctly, retrieves the corresponding metric data from the observability system, and returns the data in a readable format. Test independently by running the Gradio interface and submitting queries.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T007 [P] [US1] Contract test for metrics query tool in tests/unit/test_metrics_query_tool.py (verify tool interface matches contract)
- [ ] T008 [P] [US1] Contract test for agent node in tests/unit/test_agent_node.py (verify node interface matches contract)
- [ ] T009 [P] [US1] Unit test for configuration parsing in tests/unit/test_config.py
- [ ] T010 [P] [US1] Unit test for response formatting in tests/unit/test_response_formatter.py
- [ ] T011 [US1] Integration test for end-to-end flow in tests/integration/test_end_to_end.py (natural language query → formatted response)
- [ ] T012 [P] [US1] Integration test for Grafana MCP integration in tests/integration/test_grafana_mcp_integration.py (mock MCP server)

### Implementation for User Story 1

- [ ] T013 [P] [US1] Create __init__.py files in src/agent/, src/tools/, src/ui/, src/config/
- [ ] T014 [US1] Implement configuration settings in src/config/settings.py (load from env, validate required config, provide defaults)
- [ ] T015 [US1] Implement metrics query tool in src/tools/metrics_query.py (LangChain tool, Grafana MCP integration, error handling per contract)
- [ ] T016 [US1] Implement response formatter in src/agent/formatter.py (format MetricData to human-readable text, handle errors)
- [ ] T017 [US1] Implement agent node in src/agent/node.py (interpret query with LLM, invoke metrics tool, format response per contract)
- [ ] T018 [US1] Implement agent graph in src/agent/graph.py (LangGraph single-node graph, define state schema, wire up node)
- [ ] T019 [US1] Implement Gradio chat interface in src/ui/gradio_app.py (text input/output, connect to agent graph, display errors)
- [ ] T020 [US1] Implement main entry point in src/main.py (initialize config, create agent graph, launch Gradio interface)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Can run end-to-end demo locally.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect the overall system

- [ ] T021 [P] Documentation updates (README.md with setup instructions, usage examples)
- [ ] T022 [P] Code cleanup and refactoring (review for clarity per constitution)
- [ ] T023 [P] Additional error handling refinements (edge cases from spec)
- [ ] T024 [P] Run quickstart.md validation checklist
- [ ] T025 Verify all tests pass before proceeding

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
- **Polish (Phase 4)**: Depends on User Story 1 completion

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories

### Within User Story 1

- Tests (T007-T012) MUST be written and FAIL before implementation
- Configuration (T014) before tools/agent (needed for initialization)
- Metrics query tool (T015) before agent node (node depends on tool)
- Response formatter (T016) before agent node (node depends on formatter)
- Agent node (T017) before agent graph (graph depends on node)
- Agent graph (T018) before UI (UI depends on graph)
- UI (T019) before main entry point (main launches UI)
- Core implementation before integration
- Story complete before Polish phase

### Parallel Opportunities

- **Phase 1**: T003 can run in parallel with T001/T002 after structure exists
- **Phase 2**: T005 and T006 can run in parallel (different files, no dependencies)
- **Phase 3 Tests**: T007, T008, T009, T010, T012 can all run in parallel (different test files)
- **Phase 3 Implementation**: T013 can run in parallel with others (just __init__.py files)
- **Phase 4**: All tasks can run in parallel (documentation, cleanup, validation)

---

## Parallel Example: User Story 1

```bash
# Launch all unit tests for User Story 1 together:
Task: T007 Contract test for metrics query tool in tests/unit/test_metrics_query_tool.py
Task: T008 Contract test for agent node in tests/unit/test_agent_node.py
Task: T009 Unit test for configuration parsing in tests/unit/test_config.py
Task: T010 Unit test for response formatting in tests/unit/test_response_formatter.py
Task: T012 Integration test for Grafana MCP integration in tests/integration/test_grafana_mcp_integration.py

# After tests are written (and failing), launch implementation tasks:
Task: T013 Create __init__.py files in src/agent/, src/tools/, src/ui/, src/config/
Task: T014 Implement configuration settings in src/config/settings.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T006) - CRITICAL, blocks all stories
3. Complete Phase 3: User Story 1 (T007-T020)
   - Write tests first (T007-T012), verify they fail
   - Implement components (T013-T020)
   - Verify tests pass
4. **STOP and VALIDATE**: Test User Story 1 independently via quickstart.md
5. Complete Phase 4: Polish (T021-T025) if needed
6. Demo/deploy if ready

### Test-First Discipline (Per Constitution)

1. Write test for component (e.g., T007 for metrics query tool)
2. Verify test fails (red phase)
3. Implement minimum code to make test pass (green phase)
4. Refactor while maintaining passing tests
5. Ensure all existing tests pass before proceeding

### Incremental Validation

- After Foundational phase: Verify config and error handling work
- After tool implementation: Verify tool contract tests pass
- After agent node: Verify node contract tests pass
- After full implementation: Verify all tests pass, run end-to-end test
- After Polish: Verify quickstart.md validation checklist

---

## Notes

- [P] tasks = different files, no dependencies
- [US1] label maps task to User Story 1 for traceability
- All tests must pass before proceeding per constitution (Testing is NON-NEGOTIABLE)
- Tests must be written before implementation (test-first approach)
- Each component should have clear error handling (Accuracy & Clarity principle)
- Code should be minimal and focused (Minimalism principle)
- Interfaces should be stable for future extension (Extensibility principle)
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at checkpoints to validate independently
