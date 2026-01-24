"""
Grafana Agent: Single-node LangGraph agent for Grafana dashboard discovery.

A learning-focused agentic application that enables engineers to query Grafana
dashboards via natural language through a Gradio chat interface.

Key components:
- Agent: Single-node LangGraph graph for query processing
- Tools: Grafana MCP server wrapper for dashboard retrieval
- Config: Environment variable and YAML configuration management
- LLM: OpenAI and Ollama LLM provider support
- UI: Gradio chat interface for local demo
"""

__version__ = "0.1.0"
__author__ = "Learning Project"
__description__ = "Single-node LangGraph agent for Grafana dashboard discovery"
