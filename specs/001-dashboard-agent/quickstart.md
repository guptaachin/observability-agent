# Quickstart Guide: Grafana Dashboard Agent

**Audience**: Engineers who want to run the agent locally for learning or exploration.

**Time to First Query**: 10–15 minutes (including Grafana MCP server setup).

---

## Prerequisites

- **Python 3.11+** (check: `python3 --version`)
- **Docker** (for Grafana MCP server)
- **Git** (to clone repository)
- One of: OpenAI API key OR Ollama running locally

### Option A: OpenAI

```bash
# Get API key from https://platform.openai.com/api-keys
export OPENAI_API_KEY="sk-..."
```

### Option B: Ollama (Free, Local)

```bash
# Install from https://ollama.ai
# Start Ollama server
ollama serve &

# Pull a model (e.g., Mistral)
ollama pull mistral
```

---

## Step 1: Clone Repository & Set Up Python Environment

```bash
# Clone
git clone <repo-url>
cd observability-agent

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
# Or manually: pip install langgraph langchain gradio langsmith pydantic python-dotenv
```

---

## Step 2: Start Grafana with MCP Server (Docker)

Grafana MCP server runs in a Docker container and communicates with the agent via stdio.

```bash
# Start Grafana + MCP in Docker
docker-compose up -d  # (requires docker-compose.yml in repo root)

# Or manually start Grafana
docker run -d \
  -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=moppassword \
  -e GF_SECURITY_ADMIN_USER=mopadmin \
  grafana/grafana:latest

# Verify Grafana is running
curl http://localhost:3000/api/health
# Expected response: {"status":"ok"}
```

**Default Credentials**: 
- URL: `http://localhost:3000`
- Username: `mopadmin`
- Password: `moppassword`

---

## Step 3: Configure Agent Environment Variables

Create a `.env` file in the repository root:

```bash
# .env

# === GRAFANA CONNECTION ===
GRAFANA_URL=http://localhost:3000
GRAFANA_USERNAME=mopadmin
GRAFANA_PASSWORD=moppassword
GRAFANA_ORG_ID=1

# === LLM CHOICE ===
# Option A: OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# Option B: Ollama (if running locally)
# LLM_PROVIDER=ollama
# OLLAMA_URL=http://localhost:11434
# OLLAMA_MODEL=mistral

# === LANGSMITH (Optional, for Observability) ===
# LANGSMITH_API_KEY=ls_...
# LANGSMITH_PROJECT_NAME=grafana-dashboard-agent

# === GRADIO UI ===
GRADIO_SERVER_PORT=7860
GRADIO_SERVER_NAME=127.0.0.1
```

**Copy provided template**:
```bash
cp .env.example .env
# Then edit .env with your API key
```

**Load environment variables**:
```bash
# Linux/macOS
source .env

# Windows
# Manually set or use: set OPENAI_API_KEY=...
```

---

## Step 4: Create Some Test Dashboards in Grafana (Optional)

Visit `http://localhost:3000` and create 2–3 simple dashboards so the agent has something to list.

**Example Dashboard**:
1. Click "+" → "Create" → "Dashboard"
2. Name: "System Metrics"
3. Add a panel (any metric)
4. Save
5. Repeat for "Application Logs", "Network Traffic", etc.

(Or use Grafana's sample dashboards.)

---

## Step 5: Run the Agent

### Option A: Interactive Chat Interface (Gradio)

```bash
# In repository root
python src/main.py
```

**Expected output**:
```
Running on local URL:  http://127.0.0.1:7860
Opening in existing browser session.
```

**In your browser**:
- Open http://127.0.0.1:7860
- Chat interface appears
- Type: `"Show me all dashboards"`
- Press Enter

**Expected response**:
```
Available Dashboards

1. System Metrics (ID: 1)
   Tags: []
   Last updated: 2026-01-23

2. Application Logs (ID: 2)
   Tags: []
   Last updated: 2026-01-23
```

### Option B: Command-Line Testing

```bash
python -c "
from src.agent import agent_app

result = agent_app.invoke({
    'query': 'Show me all dashboards'
})
print(result['response'])
"
```

---

## Example Queries & Expected Responses

### ✅ Valid Query: List Dashboards

**User**: "Show me all dashboards"

**Agent Response**:
```
Available Dashboards

1. System Metrics (ID: 1)
2. Application Logs (ID: 2)
3. Network Traffic (ID: 3)

Total: 3 dashboards
```

---

### ✅ Valid Query: Variation

**User**: "What dashboards are available?"

**Agent Response**:
```
Found 3 dashboards in Grafana:
- System Metrics
- Application Logs
- Network Traffic
```

---

### ❌ Invalid Query: Metrics (Out of Scope)

**User**: "Show me CPU usage over the last hour"

**Agent Response**:
```
I can list dashboards, but metrics queries are not yet supported. 
Please use the Grafana UI or Prometheus API directly.
```

---

### ❌ Invalid Query: Anomaly Detection

**User**: "Detect anomalies in my data"

**Agent Response**:
```
I cannot detect anomalies. I can only list dashboards. 
For anomaly detection, use Grafana's alerting rules or external tools.
```

---

### ❌ Invalid Query: Recommendations

**User**: "Which dashboard should I use?"

**Agent Response**:
```
I can show you available dashboards, but I don't make recommendations. 
Try asking "Show me all dashboards" to see what's available.
```

---

## Troubleshooting

### Problem: "Cannot connect to Grafana"

**Cause**: Grafana MCP server not running or wrong URL.

**Solution**:
```bash
# Check Grafana is running
curl http://localhost:3000/api/health

# If not, start it
docker run -d -p 3000:3000 grafana/grafana:latest

# Verify GRAFANA_URL in .env matches
grep GRAFANA_URL .env
```

---

### Problem: "Authentication failed"

**Cause**: Wrong username or password.

**Solution**:
```bash
# Check credentials in .env
grep GRAFANA_USERNAME .env
grep GRAFANA_PASSWORD .env

# Test manually
curl -u mopadmin:moppassword http://localhost:3000/api/dashboards/search
# Should return JSON list of dashboards
```

---

### Problem: "OpenAI API key invalid"

**Cause**: Missing or incorrect API key.

**Solution**:
```bash
# Generate new key at https://platform.openai.com/api-keys
export OPENAI_API_KEY="sk-..."

# Test LLM
python -c "from langchain.llms import OpenAI; llm = OpenAI(); print(llm.invoke('Hello'))"
```

---

### Problem: "Ollama not reachable"

**Cause**: Ollama server not running.

**Solution**:
```bash
# Start Ollama
ollama serve &

# Check connectivity
curl http://localhost:11434/api/health

# Pull a model
ollama pull mistral
```

---

### Problem: "Gradio port already in use"

**Cause**: Port 7860 occupied by another process.

**Solution**:
```bash
# Change port in .env
GRADIO_SERVER_PORT=7861

# Or find and kill process on 7860
lsof -i :7860
kill -9 <PID>
```

---

## Observability: View Agent Traces

### Via LangSmith (if configured)

1. Set `LANGSMITH_API_KEY` in `.env`
2. Run agent (any query)
3. Visit https://smith.langchain.com
4. Select project: `grafana-dashboard-agent` (or your `LANGSMITH_PROJECT_NAME`)
5. See full trace: query → LLM call → tool invocation → response

**Example Trace**:
```
Trace ID: abc123xyz789
├─ Agent Node
│  ├─ Input: {query: "Show me all dashboards"}
│  ├─ LLM Call (gpt-4)
│  │  └─ "...list_dashboards..."
│  ├─ Tool: grafana
│  │  ├─ Input: {action: "list_dashboards"}
│  │  └─ Output: {success: true, data: [...]}
│  └─ Output: {response: "Available Dashboards..."}
└─ Duration: 1.2s
```

### Via LangGraph CLI

```bash
# Start LangGraph development server
langgraph dev --host 127.0.0.1 --port 8080

# Visit http://127.0.0.1:8080 in browser
# See agent graph, test queries interactively
```

---

## Next Steps

1. **Modify Agent Behavior**: Edit `src/agent.py` to change system prompt, add new query types
2. **Extend Tools**: Edit `src/tools.py` to add new Grafana MCP actions (metrics, specific dashboards)
3. **Customize UI**: Edit `src/interface.py` to change Gradio theme, add examples
4. **Run Tests**: `pytest tests/` (pragmatic per constitution—not required for MVP)

---

## Architecture Reference

```
.env (configuration)
 ↓
src/config.py (load & validate)
 ↓
src/main.py (entry point)
 ├─ src/agent.py (LangGraph single-node agent)
 │  ├─ src/llm.py (OpenAI or Ollama)
 │  └─ src/tools.py (Grafana MCP wrapper)
 └─ src/interface.py (Gradio chat UI)

LangSmith (if LANGSMITH_API_KEY set) ← logs all interactions
```

---

## Learning Resources

- **LangGraph Basics**: https://python.langchain.com/docs/langgraph
- **Grafana API**: https://grafana.com/docs/grafana/latest/developers/http_api/
- **Gradio**: https://www.gradio.app/docs
- **LangSmith Observability**: https://docs.smith.langchain.com

---

## Common Questions

**Q: Can I use this without OpenAI/Ollama?**  
A: No, the agent uses an LLM to interpret natural language queries. Choose OpenAI (paid, cloud) or Ollama (free, local).

**Q: Can I persist chat history?**  
A: No, by design (Principle II: No memory). Each query is independent. This is intentional for learning—focus on single-interaction patterns first.

**Q: Can I add metrics querying?**  
A: Yes, but it's out of scope for MVP. Phase 2 will extend agent to support metrics via new tools/nodes.

**Q: Where are logs stored?**  
A: In terminal output (console) and LangSmith (if API key set). No local file logs by default.

**Q: Can I run this in production?**  
A: Not recommended. This is a learning tool. Production deployments need: authentication, rate limiting, audit logs, security hardening.
