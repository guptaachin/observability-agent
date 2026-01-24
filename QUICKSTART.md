# Quick Start Guide

## Overview

This is a single-node LangGraph agent for Grafana dashboard discovery. It enables engineers to query dashboards via a chat interface or command line.

## Prerequisites

- Python 3.10+
- pip or conda
- Virtual environment (recommended)

## Setup

### 1. Create Virtual Environment
```bash
cd /Users/achin/code/observability-agent
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -e .
```

Or manually:
```bash
pip install langgraph langchain langchain-openai langchain-community pydantic gradio python-dotenv pyyaml pytest pytest-asyncio
```

## Configuration

### Via Environment Variables
```bash
export GRAFANA_URL=http://localhost:3000
export GRAFANA_USERNAME=admin
export GRAFANA_PASSWORD=admin
export GRAFANA_ORG_ID=1
export LLM_PROVIDER=openai  # or ollama
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4-turbo
# OR for Ollama:
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=llama2
```

### Via .env File
Copy and edit `config/.env.example`:
```bash
cp config/.env.example .env
# Edit .env with your Grafana and LLM settings
```

### Via YAML
Edit `config/config.yaml` with your settings.

## Usage

### Run Demo (with Mock Data)
```bash
python demo.py
```

This runs 7 example queries against the agent with mock Grafana data (no setup required).

### Run Tests
```bash
pytest tests/ -v
# Or just: pytest tests/ -q
```

All 21 tests should pass.

### Launch Gradio Web UI (WIP)
```bash
python src/main.py
# Opens at http://localhost:7860
```

Note: This requires proper Grafana and LLM configuration.

## Example Queries

The agent understands:

### List All Dashboards
- "Show me all dashboards"
- "What dashboards are available?"
- "List all dashboards"

### Filter Dashboards
- "Show dashboards with prod in the name"
- "List dashboards with database"
- "Filter dashboards with api"

### Get Dashboard Info
- "When was the Prod API dashboard updated?"
- "Tell me about the Service Health dashboard"
- "Last update time for database performance"

## Project Structure

```
src/
├── config.py      # Configuration management
├── llm.py         # LLM provider (OpenAI/Ollama)
├── tools.py       # Grafana MCP tool wrapper
├── agent.py       # Single-node LangGraph agent
└── main.py        # Gradio chat UI

tests/
├── conftest.py    # Pytest fixtures
└── test_agent.py  # 21 integration tests

config/
├── .env.example   # Environment template
└── config.yaml    # YAML configuration template

demo.py            # Demo script with sample queries
```

## Key Components

### Configuration ([src/config.py](src/config.py))
- Loads from: environment variables → .env file → config.yaml → defaults
- Validates all settings with pydantic
- Supports OpenAI and Ollama LLM providers

### LLM Support ([src/llm.py](src/llm.py))
- **OpenAI**: gpt-4-turbo (deterministic, temperature=0.0)
- **Ollama**: Local llama2 model support

### Grafana Tools ([src/tools.py](src/tools.py))
- `list_dashboards()`: Get all dashboards
- `search_dashboards(query)`: Filter by name/tags
- `get_dashboard(uid)`: Fetch single dashboard
- Comprehensive error handling with specific exception types

### Agent ([src/agent.py](src/agent.py))
- Single-node LangGraph architecture
- Query → Intent extraction → Tool calling → Response formatting
- Intent types: list, filter, get_info, unknown
- System prompt constrains scope (dashboard retrieval only)

### Web UI ([src/main.py](src/main.py))
- Gradio ChatInterface for lightweight web UI
- Stateless (no conversation persistence)
- Runs on localhost:7860

## Testing

### Test Coverage
- **21 tests** covering:
  - Intent extraction (4 tests)
  - Filter term parsing (3 tests)
  - Out-of-scope detection (2 tests)
  - Response formatting (2 tests)
  - Agent node processing (4 tests)
  - Complete agent integration (3 tests)
  - Acceptance scenarios (3 tests)

### Run Tests
```bash
pytest tests/ -v              # Verbose output
pytest tests/ -q              # Quiet output
pytest tests/test_agent.py::TestIntentExtraction -v  # Specific test class
```

## Troubleshooting

### ModuleNotFoundError
Make sure virtual environment is activated and dependencies are installed:
```bash
source venv/bin/activate
pip install -e .
```

### Tests Failing
Check that all dependencies are installed:
```bash
pip list | grep -E "langgraph|pytest|pydantic"
```

### Gradio UI Not Starting
Ensure:
1. Grafana is running and accessible at the configured URL
2. LLM API key is set (OPENAI_API_KEY or Ollama is running)
3. Firewall allows localhost:7860

## Architecture

```
User Query
    ↓
[Gradio ChatInterface or CLI]
    ↓
[Agent]
├─ Validate input
├─ Invoke LLM with system prompt
├─ Detect out-of-scope requests
├─ Extract intent (list, filter, etc.)
├─ Call Grafana tools
├─ Format response
└─ Return to user
    ↓
[Response]
```

## Next Steps

### For Development
1. Read [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for complete status
2. Review [specs/001-grafana-agent/](specs/001-grafana-agent/) for design documents
3. Check [src/agent.py](src/agent.py) for implementation details

### For Production
1. Implement real MCP server integration (Phase 5)
2. Add conversation memory if needed
3. Deploy with proper error logging and monitoring
4. Test with real Grafana instance

## Support

For questions or issues:
1. Check [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for current status
2. Review inline docstrings in source code
3. Run `pytest tests/ -v` to verify installation
4. Check demo.py for example usage

---

**Status**: MVP Complete (Phases 1-3, Tasks T001-T024)  
**Test Results**: 21/21 passing ✅  
**Ready for**: Phase 4 (Filtering) or real Grafana integration
