# Implementation Tasks: Natural Language Metrics Querying

**Feature**: Natural Language Metrics Querying  
**Branch**: `001-natural-language-metrics`  
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)  
**Task Generation Date**: January 21, 2026

---

## Overview

This document breaks down implementation into atomic, reviewable tasks organized by user story. Each task specifies:
- **Files to create/modify**
- **Exact scope of work**
- **Independent testability**
- **Parallelization opportunities** (marked with `[P]`)

### Task Organization

- **Phase 1**: Setup & Foundation (shared infrastructure)
- **Phase 2**: Foundational Tasks (blocking prerequisites for all user stories)
- **Phase 3**: User Story 1 - Natural Language Metric Queries (P1)
- **Phase 4**: User Story 2 - Multiple Question Formats (P2)
- **Phase 5**: User Story 3 - Clear Error Handling (P2)
- **Final Phase**: Polish & Validation

### Implementation Strategy

**MVP Scope**: Complete Phase 1-3 to deliver core value (single natural language query returning metrics).

**Incremental Delivery**: 
1. Phase 1-2: Infrastructure and models (non-blocking to stories)
2. Phase 3: Core story (basic query → metrics flow)
3. Phase 4-5: Robustness (variations and errors)
4. Final: Polishing and E2E validation

**Parallelization**: Tasks marked `[P]` can be implemented in parallel (different files, no dependencies).

---

## Phase 1: Project Setup & Foundation

**Goal**: Initialize project structure and dependencies  
**Blocking**: All subsequent phases depend on Phase 1  
**Est. Time**: 1-2 hours  
**Test**: Project runs without import errors

### Setup Tasks

- [x] T001 Create project directory structure in `src/` with subdirectories: `agent/`, `tools/`, `models/` per [plan.md](plan.md#project-structure)

- [x] T002 Create project directory structure in `tests/` with subdirectories: `unit/`, `integration/`, `fixtures/`

- [x] T003 Create `requirements.txt` with dependencies: `langchain>=0.1.0`, `langgraph>=0.1.0`, `gradio>=4.0.0`, `pydantic>=2.0.0`, `python-dotenv`, `pytest>=7.0.0`, `pytest-asyncio`, `aiohttp` (for MCP client HTTP calls)

- [x] T004 Create `.env.example` file with required environment variables:
  - `MCP_GRAFANA_HOST=localhost`
  - `MCP_GRAFANA_PORT=8000`
  - `LLM_SOURCE=openai` (or `ollama`)
  - `OPENAI_API_KEY=sk-...` (if using OpenAI)
  - `OLLAMA_BASE_URL=http://localhost:11434` (if using Ollama)
  - `GRADIO_SERVER_PORT=7860`

- [x] T005 Create `src/__init__.py` (empty file to make src a package)

- [x] T006 Create `tests/__init__.py` (empty file to make tests a package)

---

## Phase 2: Foundational Tasks (Blocking Prerequisites)

**Goal**: Implement shared infrastructure and data models  
**Dependencies**: Phase 1  
**Blocking**: User Story implementation cannot begin without these  
**Est. Time**: 2-3 hours  
**Test**: Models validate correctly; config loads from env

### Data Models

- [x] T007 [P] Implement Pydantic data models in `src/models/query.py` following [data-model.md](data-model.md#metricsquery-entity):
  - `TimeRange` class (start_time: datetime, end_time: datetime)
  - `MetricsQuery` class (metric_name: str, time_range: TimeRange, aggregation: Optional[str])
  - Include validation decorators, field descriptions, and example values
  - Add `to_mcp_request()` method that formats query for MCP server call

- [ ] T008 [P] Implement Pydantic data models in `src/models/result.py` following [data-model.md](data-model.md#metricsqueryresult-entity):
  - `DataPoint` class (timestamp: datetime, value: float)
  - `AggregationStats` class (min: float, max: float, mean: float, count: int)
  - `MetricsQueryResult` class (metric_name: str, unit: str, data_points: List[DataPoint], stats: Optional[AggregationStats])
  - Include formatted output methods for readability
- [x] T008 [P] Implement Pydantic data models in `src/models/result.py` following [data-model.md](data-model.md#metricsqueryresult-entity):
  - `DataPoint` class (timestamp: datetime, value: float)
  - `AggregationStats` class (min: float, max: float, mean: float, count: int)
  - `MetricsQueryResult` class (metric_name: str, unit: str, data_points: List[DataPoint], stats: Optional[AggregationStats])
  - Include formatted output methods for readability
 - [x] T009 [P] Implement Pydantic data models in `src/models/result.py` for error handling following [data-model.md](data-model.md#queryerror-entity):
  - `QueryError` class (error_code: str, message: str, suggestion: Optional[str])
  - Predefined error codes: `METRIC_NOT_FOUND`, `INVALID_TIME_RANGE`, `QUERY_TIMEOUT`, `MCP_SERVER_UNAVAILABLE`

- [x] T010 [P] Create `src/models/__init__.py` exporting: `TimeRange`, `MetricsQuery`, `DataPoint`, `AggregationStats`, `MetricsQueryResult`, `QueryError`

### Configuration Management

- [x] T011 Implement `src/config.py` to load environment variables:
  - `mcp_grafana_host`: str (from `MCP_GRAFANA_HOST`)
  - `mcp_grafana_port`: int (from `MCP_GRAFANA_PORT`)
  - `llm_source`: Literal["openai", "ollama"] (from `LLM_SOURCE`)
  - `openai_api_key`: Optional[str] (from `OPENAI_API_KEY`, required if llm_source="openai")
  - `ollama_base_url`: str (from `OLLAMA_BASE_URL`, defaults to `http://localhost:11434`)
  - `gradio_server_port`: int (from `GRADIO_SERVER_PORT`, defaults to 7860)
  - Validate configuration on load (raise error if llm_source=openai but OPENAI_API_KEY missing)
  - Include `@functools.lru_cache` for single initialization

### LLM Integration

- [x] T012 Implement `src/llm.py` with factory function `get_llm()` returning LLM instance following [research.md](research.md#llm-integration):
  - If `config.llm_source == "openai"`: Return `ChatOpenAI(model="gpt-4-turbo", temperature=0.3, api_key=config.openai_api_key)`
  - If `config.llm_source == "ollama"`: Return `ChatOllama(model="llama2", base_url=config.ollama_base_url, temperature=0.3)`
  - Include docstring explaining temperature choice (0.3 for deterministic query translation)

---

## Phase 3: User Story 1 - Natural Language Metric Queries (P1)

**Goal**: Core value - translate natural language to metric queries and return data  
**Dependencies**: Phase 1, Phase 2  
**Independent Test**: Ask "Show CPU usage for the last hour" and verify metric data returned  
**Est. Time**: 4-5 hours  
**Test**: E2E test query returns valid MetricsQueryResult with correct metric name and data points

### MCP Client & Grafana Tool

- [ ] T013 Implement MCPClient helper in `src/tools/mcp_client.py` following [metric-tool-contract.md](contracts/metric-tool-contract.md#mcp-server-architecture):
  - `class MCPClient` with methods:
    - `async connect(host: str, port: int)`: Establish connection to MCP server
    - `async call_tool(tool_name: str, arguments: dict) -> dict`: Call MCP server tool and return response
    - `async disconnect()`: Clean up connection
  - Use `aiohttp.ClientSession` for HTTP communication with MCP server
  - Handle connection errors with descriptive messages
  - Include timeout (5 seconds) for MCP server calls

- [ ] T014 Implement Grafana metrics tool in `src/tools/grafana_metrics_tool.py` following [metric-tool-contract.md](contracts/metric-tool-contract.md):
  - Implement `query_grafana_metrics(query: MetricsQuery) -> MetricsQueryResult` async function
  - Use MCPClient to call MCP server's `query_grafana_metrics` tool
  - Parse MCP server response into MetricsQueryResult
  - Handle MCP server errors (timeout, unavailable) and convert to QueryError
  - Decorate function with `@tool` from `langchain.tools` for LangChain integration
  - Include docstring explaining tool purpose and parameters per LangChain tool standards

- [ ] T015 Create `src/tools/__init__.py` exporting: `query_grafana_metrics`

### Agent Implementation

- [ ] T016 Implement LangGraph agent in `src/agent/metrics_agent.py` following [agent-contract.md](contracts/agent-contract.md):
  - Define `MetricsQueryState` TypedDict with fields: `user_question: str`, `parsed_query: Optional[MetricsQuery]`, `query_result: Optional[MetricsQueryResult]`, `error: Optional[QueryError]`, `final_response: str`
  - Implement `parse_question_node(state: MetricsQueryState) -> dict` to:
    - Call LLM with prompt to extract metric_name and time_range from user_question
    - Create MetricsQuery from LLM output
    - Return updated state with parsed_query
  - Implement `execute_query_node(state: MetricsQueryState) -> dict` to:
    - Call `query_grafana_metrics` tool with parsed_query
    - Capture response or error
    - Return updated state with query_result or error
  - Implement `format_response_node(state: MetricsQueryState) -> dict` to:
    - Format query_result into readable string output
    - Or format error message if error occurred
    - Return updated state with final_response
  - Build graph using StateGraph with three nodes: parse → execute → format
  - Compile graph and expose as `create_agent()` function returning runnable workflow

- [ ] T017 Create `src/agent/__init__.py` exporting: `create_agent`, `MetricsQueryState`

### LLM Prompting for Query Parsing

- [ ] T018 [P] Create `src/agent/prompts.py` with LLM prompt templates:
  - `QUERY_PARSING_PROMPT`: Instructs LLM to extract metric_name and relative_time_range from user question
    - Input: natural language question
    - Output: JSON with `metric_name: str`, `relative_time_range: str` (e.g., "last 1 hour")
    - Example: "Show CPU usage for the last hour" → `{"metric_name": "cpu_usage", "relative_time_range": "last 1 hour"}`
    - Include instructions to return ONLY valid JSON, no explanations
  - `TIME_RANGE_CONVERSION_PROMPT`: Instructs LLM to convert relative time expression to ISO datetime range
    - Input: relative time expression (e.g., "last 1 hour")
    - Output: JSON with `start_time: str`, `end_time: str` (ISO format)
    - Include current time context in prompt
  - Include docstrings explaining each prompt's purpose

- [ ] T019 [P] Create utility function `src/agent/query_parser.py` with:
  - `parse_user_question(question: str, llm) -> MetricsQuery`: Orchestrates LLM calls to extract metric_name and time_range
  - `convert_relative_time(relative_expr: str, llm) -> TimeRange`: Converts relative time expression to absolute range
  - Error handling: Catch JSON parse errors from LLM output and raise QueryError with `INVALID_QUERY` code

### UI Implementation

- [ ] T020 Implement Gradio interface in `src/ui.py` following [ui-contract.md](contracts/ui-contract.md):
  - Create async function `answer_question(message: str, history: list) -> Generator[str, None, None]`:
    - Initialize agent from Phase 3
    - Call agent.invoke() with user question
    - Yield response progressively (can be single yield for MVP)
    - Handle agent errors and yield formatted error message
  - Create Gradio `ChatInterface` with:
    - `fn=answer_question`
    - `examples=["Show CPU usage for the last hour", "Memory utilization in the last 24 hours", "Average request latency today"]`
    - `title="Natural Language Metrics Query"`
    - `description="Ask about system metrics in plain English"`
  - Return interface object

### Main Entry Point

- [ ] T021 Create `src/main.py` CLI entrypoint:
  - Load configuration
  - Create Gradio interface
  - Launch server with `interface.launch(server_name="0.0.0.0", server_port=config.gradio_server_port, share=False)`

### Unit Tests for Phase 3

- [ ] T022 [P] Create `tests/unit/test_models.py`:
  - Test `TimeRange` validation (start < end, datetime parsing)
  - Test `MetricsQuery` creation and `to_mcp_request()` output format
  - Test `MetricsQueryResult` creation with data points and stats
  - Test `QueryError` creation with all error codes
  - 8-10 test cases total

- [ ] T023 [P] Create `tests/unit/test_query_parser.py`:
  - Mock LLM responses and test `parse_user_question()` with sample questions
  - Test `convert_relative_time()` with various relative expressions ("last hour", "yesterday", "past week")
  - Test error handling for invalid LLM outputs
  - 6-8 test cases total

- [ ] T024 [P] Create `tests/unit/test_agent.py`:
  - Mock MCPClient and test agent node transitions (parse → execute → format)
  - Test successful query flow with mock data
  - Test error handling when query execution fails
  - 6-8 test cases total

### Integration Tests for Phase 3

- [ ] T025 Create `tests/integration/test_e2e_basic_query.py`:
  - Setup: Create MCPClient connected to real or mocked MCP server
  - Test: End-to-end flow from user question to formatted response
  - Expected: Verify response contains metric name, unit, data points, and statistics
  - Single test case for MVP (can add more in later phases)

---

## Phase 4: User Story 2 - Multiple Question Formats (P2)

**Goal**: Handle varied natural language patterns for same metric  
**Dependencies**: Phase 1, Phase 2, Phase 3  
**Independent Test**: Ask same metric 3+ ways ("Show CPU", "What's the CPU usage", "CPU load for last hour") and verify all return equivalent data  
**Est. Time**: 1-2 hours  
**Test**: Multiple query formats route to same metric name

### Enhanced Query Parsing

- [ ] T026 Update `src/agent/prompts.py` with new prompt:
  - `QUERY_INTENT_MATCHING_PROMPT`: Instructs LLM to handle variations
    - Include known metric mappings: `{"cpu": ["cpu usage", "cpu load", "cpu utilization"], "memory": ["memory", "memory usage", "RAM"]}`
    - Extract intent from varied questions and normalize to canonical metric name
    - Example: "What's the CPU doing?" → `{"metric_name": "cpu_usage"}`

- [ ] T027 Update `src/agent/query_parser.py`:
  - Enhance `parse_user_question()` to use QUERY_INTENT_MATCHING_PROMPT
  - Add fuzzy matching fallback: If LLM returns metric not in known list, try string similarity match against known metrics
  - Document supported metrics in module docstring

### New Unit Tests for Phase 4

- [ ] T028 [P] Create `tests/unit/test_query_variations.py`:
  - Test variations of CPU query (5+ variations)
  - Test variations of memory query (5+ variations)
  - Test metric name normalization (e.g., "CPU" → "cpu_usage")
  - Verify all variations resolve to same canonical metric name
  - 10-15 test cases total

### Integration Tests for Phase 4

- [ ] T029 Create `tests/integration/test_e2e_query_variations.py`:
  - Test 3 different phrasings of same metric query
  - Verify all 3 return data for same metric
  - Verify data is equivalent (same time range, same data points count)

---

## Phase 5: User Story 3 - Clear Error Handling (P2)

**Goal**: Provide clear, actionable error messages  
**Dependencies**: Phase 1, Phase 2, Phase 3  
**Independent Test**: Submit invalid query and receive helpful error message  
**Est. Time**: 2-3 hours  
**Test**: Invalid queries return QueryError with clear message and suggestion

### Error Handling & Reporting

- [ ] T030 Update `src/agent/metrics_agent.py`:
  - Enhance `parse_question_node()` to catch parsing errors and return error state
  - Enhance `execute_query_node()` to catch MCP client errors and convert to QueryError with suggestion
  - Enhance `format_response_node()` to format errors with: error code, clear message, recovery suggestion

- [ ] T031 Create `src/agent/error_handler.py`:
  - Implement `format_error_for_user(error: QueryError) -> str` to convert error objects to user-friendly messages
  - Map error codes to user-friendly descriptions:
    - `METRIC_NOT_FOUND`: "That metric is not available. Try one of: [list of available metrics]"
    - `INVALID_TIME_RANGE`: "I couldn't understand the time range. Try: 'last hour', 'yesterday', 'past week'"
    - `QUERY_TIMEOUT`: "The query took too long. Try a shorter time range or different metric"
    - `MCP_SERVER_UNAVAILABLE`: "Can't reach the metrics server. Check if Grafana is running"
  - Include suggestion field with actionable next steps

- [ ] T032 Update `src/ui.py`:
  - Modify `answer_question()` to detect error in response and format specially
  - Display errors with distinct styling (different color or marker) to distinguish from successful results
  - Include suggestion in error output

### Available Metrics Discovery

- [ ] T033 [P] Create `src/tools/available_metrics.py`:
  - Implement `get_available_metrics() -> List[str]` function
  - Query MCP server for list of available metrics on startup
  - Cache result with TTL (5 minutes) to avoid repeated server calls
  - Include fallback list of common metrics if server unavailable

- [ ] T034 [P] Update `src/agent/error_handler.py`:
  - Modify `format_error_for_user()` to include available metrics in error message for `METRIC_NOT_FOUND`
  - Use `get_available_metrics()` to provide suggestions

### Unit Tests for Phase 5

- [ ] T035 [P] Create `tests/unit/test_error_handling.py`:
  - Test QueryError creation with all error codes
  - Test `format_error_for_user()` produces user-friendly output for each error type
  - Test error message includes suggestions
  - 8-10 test cases total

- [ ] T036 [P] Create `tests/unit/test_available_metrics.py`:
  - Mock MCP server response and test `get_available_metrics()` returns list
  - Test caching (second call returns cached result)
  - Test fallback list when MCP server unavailable
  - 6-8 test cases total

### Integration Tests for Phase 5

- [ ] T037 Create `tests/integration/test_e2e_error_scenarios.py`:
  - Test querying non-existent metric returns clear error message
  - Test invalid time range returns helpful suggestion
  - Test MCP server unavailable returns appropriate error
  - 3-5 test cases total (one per error type)

---

## Final Phase: Polish & Validation

**Goal**: Ensure quality and completeness  
**Dependencies**: All previous phases  
**Est. Time**: 2-3 hours  
**Test**: Full E2E test passes; project runs from README

### Documentation & Quickstart

- [ ] T038 Update `quickstart.md` section "Running the Application":
  - Test: `python src/main.py` launches Gradio interface on port 7860
  - Test: Example queries work as described in quickstart
  - Verify all 7 example queries from quickstart.md execute successfully

- [ ] T039 Create `README.md` at repository root with:
  - Feature overview (2-3 sentences)
  - Quick start (5 lines: clone, pip install, setup .env, python main.py)
  - Architecture overview (pointing to contracts/)
  - Example queries (3-4 examples with expected output format)
  - Troubleshooting (link to quickstart.md troubleshooting section)

### Comprehensive Integration Testing

- [ ] T040 Create `tests/integration/test_e2e_complete.py` (final comprehensive test):
  - Setup: Start application with mock MCP server
  - Test Case 1: Simple metric query returns valid data
  - Test Case 2: Query variation returns equivalent data
  - Test Case 3: Invalid query returns helpful error
  - Test Case 4: Verify response includes metric name, unit, timestamps, values, stats
  - Verify all tests pass and no unhandled exceptions

### Code Quality & Review Preparation

- [ ] T041 [P] Run code quality checks:
  - `black src/ tests/` - Format code
  - `isort src/ tests/` - Sort imports (if using isort)
  - `pylint src/` - Lint check (or flake8)
  - Target: All files pass formatting and linting

- [ ] T042 [P] Create `src/py.typed` marker file (for type checking support)

- [ ] T043 [P] Add type hints to all functions missing them:
  - Use `mypy src/ tests/` to identify issues
  - Add type annotations to all function signatures
  - Target: No untyped function definitions remain

### Documentation & Comments

- [ ] T044 [P] Add docstrings to all public functions following Google-style:
  - Module-level docstring for each file
  - Function-level docstring with Args, Returns, Raises sections
  - Class-level docstring for all Pydantic models
  - Include examples in docstrings where helpful

- [ ] T045 [P] Add inline comments explaining LangGraph workflow:
  - Explain state transitions in `metrics_agent.py`
  - Explain LLM prompting strategy in `prompts.py`
  - Explain MCP client communication in `mcp_client.py`
  - Target: Clarity for new readers

### Performance Validation

- [ ] T046 Create `tests/integration/test_performance.py`:
  - Benchmark query execution time (should be < 6 seconds per spec)
  - Measure LLM response time, MCP server call time, formatting time separately
  - Log results (for optimization in future phases)

### Final Integration & Verification

- [ ] T047 Create `tests/integration/test_complete_user_stories.py`:
  - **User Story 1 Test**: "Show CPU usage for the last hour" → returns valid metric data
  - **User Story 2 Test**: Ask same metric 3 ways → all return equivalent data
  - **User Story 3 Test**: Query invalid metric → returns clear error message
  - **Acceptance Criteria Check**: Verify all 6 success criteria from spec.md can be demonstrated

### Pre-Release Checklist

- [ ] T048 Verify setup and dependencies:
  - Test: Clean clone of repo → `pip install -r requirements.txt` → no errors
  - Test: `.env.example` has all required variables documented
  - Test: Missing env var raises clear error on startup (not cryptic error mid-flow)

- [ ] T049 Final README check:
  - Test: Follow README from scratch (no prior setup)
  - Test: Can run application in < 5 minutes from clone
  - Test: Example queries work as advertised
  - Verify: README is clear for someone new to the codebase

- [ ] T050 Create `IMPLEMENTATION_LOG.md` documenting:
  - Total lines of code per module
  - Test coverage summary
  - Known limitations (e.g., only works with specific Grafana versions)
  - Future improvement opportunities

---

## Task Statistics

**Total Tasks**: 50 main implementation tasks  
**Parallelizable Tasks**: 18 (marked with `[P]`)

### By Phase

| Phase | Tasks | Duration | Blocking |
|-------|-------|----------|----------|
| **Phase 1: Setup** | T001-T006 | 1-2h | Yes |
| **Phase 2: Foundation** | T007-T019 | 2-3h | Yes |
| **Phase 3: Story 1 (Core)** | T020-T025 | 4-5h | Partial |
| **Phase 4: Story 2 (Variations)** | T026-T029 | 1-2h | No |
| **Phase 5: Story 3 (Errors)** | T030-T037 | 2-3h | No |
| **Final: Polish** | T038-T050 | 2-3h | No |

### By Type

- **Setup/Configuration**: 6 tasks
- **Data Models**: 4 tasks
- **LLM/Prompting**: 4 tasks
- **Agent Implementation**: 3 tasks
- **Tools/MCP Integration**: 3 tasks
- **UI**: 2 tasks
- **Testing (Unit)**: 6 tasks
- **Testing (Integration)**: 6 tasks
- **Documentation/Polish**: 13 tasks

### Suggested MVP Scope

**Minimum to deliver core value**: Phase 1 + Phase 2 + Phase 3 (T001-T025)  
**Time**: 7-10 hours  
**Delivers**: Natural language query → metric data (User Story 1 complete)

**Add robustness**: Phase 4 + Phase 5 (T026-T037)  
**Time**: 3-5 hours additional  
**Delivers**: All user stories and clear error handling

---

## Parallelization Opportunities

### Independent File Sets (Can be worked in parallel)

**Set 1** (Models & Config):
- T007: `src/models/query.py`
- T008: `src/models/result.py`
- T009: `src/models/result.py` (errors)
- T011: `src/config.py`
- T012: `src/llm.py`

**Set 2** (Agent & Prompts):
- T016: `src/agent/metrics_agent.py`
- T018: `src/agent/prompts.py`
- T019: `src/agent/query_parser.py`

**Set 3** (Tools & MCP):
- T013: `src/tools/mcp_client.py`
- T014: `src/tools/grafana_metrics_tool.py`

**Set 4** (Testing):
- T022-T025, T028-T029, T035-T037, T040, T046-T047 (all tests)

**Set 5** (UI & Entrypoint):
- T020: `src/ui.py`
- T021: `src/main.py`

### Suggested Parallel Workflow

1. **Person A**: T001-T002 (setup directories) - 15 min
2. **Person B**: T003-T004 (requirements and env) - 15 min
3. **All**: T005-T006 (touch __init__.py files) - 5 min
4. **Parallel Groups** (after Phase 1):
   - **Group 1**: T007-T012 (Models + Config + LLM) - 1.5h
   - **Group 2**: T013-T019 (Agent + Tools + Prompts) - 2h
   - **Group 3**: T022-T025 (Unit & Integration Tests) - 1.5h
5. **Sequential**: T020-T021 (UI depends on agent) - 30 min
6. **Parallel Groups** (Stories 2 & 3):
   - **Group 1**: T026-T029 (Story 2: Variations)
   - **Group 2**: T030-T037 (Story 3: Errors)
7. **Final**: T038-T050 (Polish & validation) - 2h

---

## Quality Gates by Phase

### Phase 1 Gate
✅ All imports work without errors  
✅ Project structure matches plan.md  
✅ `.env.example` documents all variables  

### Phase 2 Gate
✅ All Pydantic models validate correctly  
✅ Config loads from environment with proper error messages  
✅ LLM factory returns correct instance based on config  

### Phase 3 Gate
✅ Agent workflow executes: parse → execute → format  
✅ E2E test query returns MetricsQueryResult with data  
✅ UI launches without errors  
✅ At least one example query works end-to-end  

### Phase 4 Gate
✅ Multiple query formats resolve to same metric  
✅ Query variations return equivalent data  

### Phase 5 Gate
✅ Invalid query returns QueryError with clear message  
✅ Error message includes helpful suggestion  
✅ Available metrics list populates correctly  

### Final Gate
✅ All 6 success criteria from spec.md can be demonstrated  
✅ All tests pass  
✅ README accurate and project runnable from clone  
✅ No unhandled exceptions in normal flow  

---

## Next Steps

1. **Review this tasks.md** for clarity and completeness
2. **Choose implementation approach**:
   - Sequential: Complete Phase 1 → Phase 2 → Phase 3 → ...
   - Parallel: Use "Parallelization Opportunities" section to assign work
3. **Start Phase 1 tasks** (T001-T006)
4. **Track progress** by marking completed tasks
5. **Run tests at each phase gate** to validate completion

---

**Generated**: January 21, 2026  
**Status**: Ready for Implementation  
**MVP Completion Target**: Phase 1-3 (T001-T025)  
**Full Feature Target**: Phase 1-5 (T001-T037)  
**Polish & Validation**: T038-T050
