# Quickstart Guide: Grafana Agent

**Phase 1 Output** | **Status**: Complete | **Date**: 2026-01-23

Get the Grafana Agent running locally in 10 minutes.

---

## Prerequisites

- **Python**: 3.10 or later (`python --version`)
- **Docker**: Latest version with `docker-compose` (for running Grafana)
- **Git**: For cloning the repository
- **Terminal**: bash or zsh (macOS/Linux) or PowerShell (Windows)

---

## Step 1: Clone Repository

```bash
git clone <repository-url>
cd observability-agent
```

---

## Step 2: Create Python Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate  # Windows PowerShell
```

**Verify activation**: Your shell prompt should show `(.venv)` prefix.

---

## Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -e .
```

This installs the agent package and all required dependencies (LangGraph, LangChain, Gradio, etc.).

**Expected output**: "Successfully installed observability-agent..."

---

## Step 4: Configure Grafana Access

### Option A: Use Docker Compose (Recommended for Demo)

If you have an existing Grafana running in Docker:

```bash
# Start Grafana (if not already running)
docker-compose up -d grafana

# Wait for Grafana to be ready (check http://localhost:3000)
```

### Option B: Point to Existing Grafana Instance

If you have Grafana running elsewhere:

```bash
# Skip Step 4A; proceed to Step 5 configuration
```

---

## Step 5: Configure Agent Environment

### Create `.env` file

```bash
cp config/.env.example .env
```

### Edit `.env` with your Grafana details

```env
# Grafana Connection (update if different from defaults)
GRAFANA_URL=http://localhost:3000
GRAFANA_USERNAME=mopadmin
GRAFANA_PASSWORD=moppassword
GRAFANA_ORG_ID=1

# LLM Provider (choose one)
LLM_PROVIDER=ollama  # Use local Ollama (recommended for demo)
# OR
LLM_PROVIDER=openai  # Use OpenAI (requires API key)

# If using Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# If using OpenAI (cloud)
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4-turbo
```

### Setup LLM Provider

**For Ollama (local, recommended)**:
```bash
# Install Ollama from https://ollama.ai (if not already installed)
# Start Ollama in a separate terminal
ollama serve

# In another terminal, pull a model
ollama pull llama2
```

**For OpenAI (cloud)**:
```bash
# Get API key from https://platform.openai.com/api-keys
# Add to .env file:
# OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
```

---

## Step 6: Verify Configuration

Test that the agent can connect to Grafana:

```bash
python -c "from src.config import load_config; config = load_config(); print(f'✓ Grafana: {config.grafana.url}')"
```

**Expected output**: `✓ Grafana: http://localhost:3000`

If this fails, check:
- `.env` file exists and is readable
- Grafana is running (`curl http://localhost:3000/api/health`)
- Credentials are correct

---

## Step 7: Start the Agent

```bash
python src/main.py
```

**Expected output**:
```
* Gradio web interface running at: http://localhost:7860
* Press Ctrl+C to stop
```

A browser window should open automatically at `http://localhost:7860`.

---

## Step 8: Try Your First Query

In the Gradio chat interface:

1. **Type**: "Show me all dashboards"
2. **Press**: Enter or click "Submit"
3. **Expected response**: A numbered list of dashboards with names

**Example response**:
```
I found 3 dashboards:

1. Production API Metrics
   Last updated: 2026-01-23

2. Database Performance
   Last updated: 2026-01-21

3. Service Health Overview
   Last updated: 2026-01-22
```

If this works, congratulations! The agent is working. 🎉

---

## Example Queries

Try these queries to explore the agent:

```
# List all dashboards
"Show me all dashboards"

# Filter by name
"Show me dashboards with 'prod' in the name"

# Get specific dashboard info
"When was the Production API dashboard last updated?"

# Out-of-scope request (should be rejected)
"Analyze my metrics for anomalies"
```

---

## Troubleshooting

### "Unable to connect to Grafana"

**Cause**: Grafana is not running or URL is incorrect.

**Solutions**:
```bash
# Check Grafana health
curl http://localhost:3000/api/health

# If using Docker, check container is running
docker ps | grep grafana

# If not running, start Grafana
docker-compose up -d grafana
```

### "Authentication failed"

**Cause**: Username or password is incorrect.

**Solutions**:
```bash
# Test credentials manually
curl -u mopadmin:moppassword http://localhost:3000/api/user

# If returns 401, check credentials in .env match Grafana instance
# For Docker, default is mopadmin/moppassword
```

### "No module named 'src'"

**Cause**: Package not installed or virtual environment not activated.

**Solutions**:
```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # macOS/Linux

# Reinstall package
pip install -e .
```

### "Unable to connect to Ollama" or "OpenAI API error"

**Cause**: LLM provider is not running or API key is invalid.

**Solutions**:
```bash
# For Ollama
ollama serve  # Start in separate terminal

# For OpenAI
# Check API key is valid at https://platform.openai.com/api-keys
# Verify key in .env is correct: OPENAI_API_KEY=sk-...
```

### Chat responds with error instead of dashboards

**Cause**: LLM or Grafana is slow, or query is out of scope.

**Check**:
1. Try simpler query: "Show me all dashboards"
2. Check Grafana has dashboards: Visit http://localhost:3000 directly
3. Check LLM is responding: Test with simple prompt
4. Check for error message (should be clear about what went wrong)

---

## Configuration File (Advanced)

If you prefer YAML configuration instead of `.env`:

**`config/config.yaml`**:
```yaml
grafana:
  url: http://localhost:3000
  username: mopadmin
  password: moppassword
  org_id: 1

llm:
  provider: ollama
  ollama:
    base_url: http://localhost:11434
    model: llama2

logging:
  level: INFO
```

**Priority**: Env variables override `.env` file, which overrides `config.yaml`.

---

## Architecture Overview

```
┌─────────────────────────────┐
│   Gradio Chat Interface     │ ← You interact here
│  (http://localhost:7860)    │
└────────────────┬────────────┘
                 │
                 ↓
┌─────────────────────────────┐
│   LangGraph Agent Node      │
│  (query → LLM → response)   │
└────────────────┬────────────┘
                 │
         ┌───────┴──────────┐
         ↓                  ↓
    ┌─────────┐         ┌──────────┐
    │ LLM     │         │ Grafana  │
    │ (OpenAI │         │ MCP      │
    │ /Ollama)│         │ Server   │
    └─────────┘         └─────┬────┘
                               ↓
                        ┌──────────────┐
                        │ Grafana API  │
                        │ (dashboards) │
                        └──────────────┘
```

---

## Next Steps

### For Exploration
- Ask different queries about your dashboards
- Test out-of-scope questions and see how agent responds
- Check agent logs to understand decision-making

### For Learning
- Read [research.md](research.md) to understand design decisions
- Read [data-model.md](data-model.md) to understand data structures
- Read [contracts/agent_interface.md](contracts/agent_interface.md) for API contracts
- Read [plan.md](plan.md) for architecture and implementation approach

### For Development
- See `/speckit/tasks` for development task breakdown
- Check `src/` directory structure for code organization
- Look at integration tests in `tests/` for usage examples

### For Extension
- To add more LLM models: Modify `src/llm.py`
- To add more Grafana tools: Extend `src/tools.py`
- To add new agent nodes: Modify `src/agent.py`

---

## Stopping the Agent

Press **Ctrl+C** in the terminal running `python src/main.py`.

```
KeyboardInterrupt
Shutting down Gradio interface...
```

---

## Getting Help

### Check Status
```bash
# Verify Grafana health
curl http://localhost:3000/api/health

# Test LLM connection
curl http://localhost:11434/api/tags  # For Ollama

# View agent logs
tail -f logs/agent.log  # (if logging configured)
```

### Common Issues Reference
- Grafana connection: Check `GRAFANA_URL` and credentials
- LLM timeout: Check LLM provider is running and responding
- Out-of-memory: Reduce `OLLAMA_MODEL` to smaller model (e.g., `neural-chat`)

### Documentation
- [Grafana API Docs](https://grafana.com/docs/grafana/latest/developers/http_api/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [Gradio Docs](https://www.gradio.app/docs/)

---

## Summary

You now have:
- ✅ Agent running locally
- ✅ Gradio chat interface
- ✅ Connected to Grafana via MCP
- ✅ LLM answering questions about dashboards

Enjoy exploring the agent! 🚀
