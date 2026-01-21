# Quickstart Guide

**Feature**: Natural Language Metrics Querying  
**Date**: January 21, 2026

---

## Overview

This guide walks you through setting up and running the Natural Language Metrics Querying system locally.

**Estimated time**: 10-15 minutes

---

## Prerequisites

Before starting, ensure you have:

### System Requirements

- **Python**: 3.11 or higher
- **Docker**: For running Grafana (optional, can use existing Grafana instance)
- **Git**: For cloning the repository

### Knowledge Requirements

- Basic familiarity with command line / terminal
- Understanding of system metrics (CPU, memory, etc.) is helpful but not required

### Accounts/API Keys

Choose ONE of the following:

**Option A: OpenAI (Recommended for better quality)**
- OpenAI API key from https://platform.openai.com/api-keys
- Requires paid account (or free trial credits)

**Option B: Ollama (Free, runs locally)**
- No API key needed
- Requires ~4GB RAM and download of model (~4GB)
- Slower inference than OpenAI

### Grafana Instance

Either:

**Option A: Use existing Grafana**
- Grafana URL, username, password
- Must have metrics already stored (datasource configured)

**Option B: Start Grafana locally**
- Run provided Docker container
- Pre-configured with sample data

---

## Step 1: Clone Repository

```bash
git clone https://github.com/your-org/observability-agent.git
cd observability-agent
```

## Step 2: Create Python Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies include**:
- langchain >= 0.1.0
- langgraph >= 0.1.0
- gradio >= 4.0.0
- pydantic >= 2.0.0
- httpx >= 0.25.0
- python-dotenv >= 1.0.0

---

## Step 4: Configure Grafana

### Option A: Use Existing Grafana

Create `.env` file in project root:

```env
# Grafana Configuration
GRAFANA_URL=http://your-grafana-url:3000
GRAFANA_USERNAME=your_username
GRAFANA_PASSWORD=your_password
GRAFANA_ORG_ID=1

# LLM Configuration
LLM_SOURCE=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-3.5-turbo
```

**To verify Grafana is accessible**:

```bash
curl -X GET "http://your-grafana-url:3000/api/datasources" \
  -H "Authorization: Bearer YOUR_GRAFANA_API_TOKEN"
```

### Option B: Start Grafana with Docker

```bash
# Create data directory
mkdir -p ./grafana-data

# Run Grafana container
docker run -d \
  --name grafana \
  --network host \
  -e GF_SECURITY_ADMIN_PASSWORD=moppassword \
  -v $(pwd)/grafana-data:/var/lib/grafana \
  grafana/grafana:latest
```

Access Grafana:
- URL: http://localhost:3000
- Username: admin
- Password: moppassword

Configure datasource:
1. Go to Configuration → Data Sources
2. Add new datasource (Prometheus or your preferred type)
3. Ensure metrics are available

Create `.env` file:

```env
# Grafana Configuration
GRAFANA_URL=http://localhost:3000
GRAFANA_USERNAME=admin
GRAFANA_PASSWORD=moppassword
GRAFANA_ORG_ID=1

# LLM Configuration
LLM_SOURCE=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-3.5-turbo
```

---

## Step 5: Configure Language Model

### Option A: OpenAI

1. **Get API Key**:
   - Sign up at https://platform.openai.com
   - Create API key in Account Settings → API Keys

2. **Add to `.env`**:
   ```env
   LLM_SOURCE=openai
   OPENAI_API_KEY=sk-your-key-here
   OPENAI_MODEL=gpt-3.5-turbo
   ```

3. **Verify**:
   ```bash
   python -c "import openai; print('OpenAI configured')"
   ```

### Option B: Ollama (Free)

1. **Install Ollama**:
   ```bash
   # macOS/Linux
   curl https://ollama.ai/install.sh | sh
   
   # Or download from https://ollama.ai
   ```

2. **Pull a model**:
   ```bash
   ollama pull mistral  # or llama2, neural-chat, etc.
   ```

3. **Start Ollama server** (runs in background):
   ```bash
   ollama serve
   ```

4. **Add to `.env`**:
   ```env
   LLM_SOURCE=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=mistral
   ```

5. **Verify**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

---

## Step 6: Run the Application

### Start the Chat Interface

```bash
python src/main.py
```

**Expected output**:
```
Starting Gradio interface...
Running on local URL:  http://127.0.0.1:7860

To create a public link, set `share=True` in `launch()`.
```

### Access the Interface

Open browser to: **http://localhost:7860**

---

## Step 7: Try Some Queries

### Example 1: CPU Usage

```
"Show CPU usage for the last hour"
```

Expected response:
```
CPU Usage (%)
Time: 2026-01-21 10:00:00 to 2026-01-21 11:00:00
Data Points: 60

Min:  5.2%
Max:  45.8%
Mean: 22.1%

[time series data...]
```

### Example 2: Memory Usage

```
"What was memory usage yesterday?"
```

### Example 3: Request Latency

```
"How did request latency change over time today?"
```

### Example 4: With Aggregation

```
"Show average CPU usage for the past week"
```

---

## Troubleshooting

### "Module not found" Error

**Problem**: `ModuleNotFoundError: No module named 'langchain'`

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### "Cannot connect to Grafana" Error

**Problem**: `ERROR: grafana_unavailable - Cannot connect to Grafana`

**Solution**:

1. Check Grafana is running:
   ```bash
   curl http://localhost:3000  # or your Grafana URL
   ```

2. Verify credentials in `.env`

3. If using Docker Grafana:
   ```bash
   docker ps | grep grafana  # Should show running container
   docker logs grafana        # Check logs for errors
   ```

4. Restart Grafana:
   ```bash
   docker restart grafana
   ```

### "OpenAI API Error"

**Problem**: `AuthenticationError: Invalid API key`

**Solution**:

1. Verify API key in `.env`:
   ```bash
   echo $OPENAI_API_KEY  # Should print your key
   ```

2. Check key is active on OpenAI dashboard

3. Ensure no trailing spaces: `sk-xxx` not `sk-xxx ` (with space)

4. Test directly:
   ```python
   from langchain.chat_models import ChatOpenAI
   llm = ChatOpenAI(api_key="YOUR_KEY")
   llm.invoke("Hello")
   ```

### "Ollama Connection Error"

**Problem**: `Cannot connect to http://localhost:11434`

**Solution**:

1. Ensure Ollama is running:
   ```bash
   ollama serve  # In a separate terminal
   ```

2. Verify model is pulled:
   ```bash
   ollama pull mistral
   ollama list  # Should show downloaded models
   ```

3. Check port 11434 is not blocked

### "No metrics available" Error

**Problem**: "Metric 'cpu_usage' not found"

**Solution**:

1. Verify Grafana has data:
   - Open http://localhost:3000
   - Go to Explore
   - Select your datasource
   - Check metrics exist

2. Verify datasource is configured:
   - Configuration → Data Sources
   - Should have at least one datasource

3. Check metric names match exactly:
   ```bash
   # Query available metrics via Grafana API
   curl -X GET "http://localhost:3000/api/search" \
     -H "Authorization: Bearer YOUR_API_TOKEN"
   ```

4. Try example queries:
   - Instead of "Show CPU usage"
   - Try "Show cpu_usage" (with underscore)
   - Or check actual metric names in Grafana

---

## Next Steps

### Learn More

- Read [data-model.md](data-model.md) to understand data structures
- Read [agent-contract.md](contracts/agent-contract.md) to understand agent workflow
- Read [research.md](research.md) for technical deep dives

### Develop

- Modify `src/main.py` to customize UI
- Add new metrics query tools in `src/tools/`
- Extend agent logic in `src/agent/metrics_agent.py`

### Deploy

- See `DEPLOYMENT.md` for running in production
- Configure authentication for multi-user access
- Set up monitoring and logging

---

## Common Questions

### Q: Can I use both OpenAI and Ollama?

**A**: You can configure one at a time. Switch by changing `LLM_SOURCE` in `.env`:
```env
LLM_SOURCE=openai  # or "ollama"
```

### Q: Why doesn't the agent remember previous questions?

**A**: By design - each query is stateless. This keeps the system simple and enables scaling. See [specification](spec.md#non-goals).

### Q: Can I add new metrics?

**A**: Yes! The agent automatically discovers available metrics from Grafana. Just ensure they're stored in your datasource.

### Q: Is this production-ready?

**A**: This is a learning project. For production:
- Add authentication
- Set up proper logging
- Add rate limiting
- Deploy behind a load balancer
- See [production-setup.md](../../../docs/production-setup.md)

### Q: How do I modify the UI?

**A**: Edit `src/ui.py` to customize Gradio interface. Changes to:
- Title, description
- Example queries
- Result formatting
- Theme and colors

### Q: Can I use a different LLM?

**A**: Yes! The system uses LangChain which supports many LLM providers:
- Anthropic Claude
- Google PaLM
- Local LLMs via HuggingFace
- etc.

See [research.md](research.md#openai-vs-ollama-integration) for integration patterns.

---

## Getting Help

### Check Documentation

- [Specification](spec.md) - What the system does
- [Research](research.md) - Technical background
- [Data Model](data-model.md) - Entity definitions
- [Agent Contract](contracts/agent-contract.md) - Workflow details

### Enable Debug Logging

```bash
# Add to .env
DEBUG=true
LOG_LEVEL=DEBUG
```

View logs in terminal where you started the app.

### Common Error Codes

| Error Type | Meaning | Solution |
|-----------|---------|----------|
| `metric_not_found` | Metric doesn't exist in Grafana | Check metric name in Grafana |
| `invalid_time_range` | Start/end times invalid | Use format: `start < end` |
| `parsing_error` | LLM couldn't understand query | Rephrase more clearly |
| `grafana_unavailable` | Can't reach Grafana | Verify Grafana is running |
| `unsupported_operation` | Requested feature not available | Check what's supported |

---

## Success Checklist

You've successfully set up the system when:

- [ ] Python virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file configured with Grafana and LLM details
- [ ] Grafana running and accessible (`http://localhost:3000`)
- [ ] Application starts without errors (`python src/main.py`)
- [ ] Gradio interface loads at `http://localhost:7860`
- [ ] First query returns results or helpful error message
- [ ] Multiple queries work independently (no state carried over)

Once all items checked, you're ready to start querying metrics!

---

## Example Queries to Try

```
1. "Show CPU usage for the last hour"
2. "What was memory utilization yesterday?"
3. "Request latency over the past week"
4. "Show average disk I/O for the past 24 hours"
5. "Network traffic last month"
6. "Database connections right now"
7. "Error rate for the past 6 hours"
8. "Response time trends today"
```

Adjust metric names based on what's available in your Grafana instance.
