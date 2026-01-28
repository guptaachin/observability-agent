# Observability Agent

A learning project to build AI agents that interact with observability tools via [Model Context Protocol (MCP)](https://github.com/grafana/mcp-grafana).

## Progress

| Week | Focus | Status | Docs |
|------|-------|--------|------|
| 1 | Grafana dashboard queries via MCP | ✅ Done | [week-1.md](week-1.md) |
| 2 | Tool-calling, alerts, memory | 🔜 Planned | - |

## Quick Start

```bash
# 1. Start Grafana + MCP server
git clone https://github.com/guptaachin/metrics-observability-pipeline.git
cd metrics-observability-pipeline && ./start-mop

# 2. Run the agent
cd observability-agent
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add OPENAI_API_KEY
python -m src.main
```

Open http://localhost:7860

## Related

- [metrics-observability-pipeline](https://github.com/guptaachin/metrics-observability-pipeline) - Grafana + MCP server setup
- [mcp-grafana](https://github.com/grafana/mcp-grafana) - Grafana MCP server
