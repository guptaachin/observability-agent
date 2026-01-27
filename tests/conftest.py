"""
Pytest configuration and shared test fixtures for Grafana Agent.

This module provides:
- Mock Grafana MCP responses
- Mock LLM responses  
- Common test utilities
"""

import pytest
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_dashboard_list() -> List[Dict[str, Any]]:
    """Fixture providing mock Grafana dashboard list response."""
    return [
        {
            "id": "1",
            "uid": "prod-api-dashboard",
            "title": "Production API Metrics",
            "folderTitle": "Production",
            "tags": ["prod", "api", "monitoring"],
            "updated": "2026-01-23T10:30:00Z",
            "created": "2025-11-15T14:22:00Z",
            "orgId": 1,
            "starred": True,
        },
        {
            "id": "2",
            "uid": "db-perf-dashboard",
            "title": "Database Performance",
            "folderTitle": "Infrastructure",
            "tags": ["database", "prod"],
            "updated": "2026-01-21T14:22:00Z",
            "created": "2025-10-01T08:00:00Z",
            "orgId": 1,
            "starred": False,
        },
        {
            "id": "3",
            "uid": "svc-health-dashboard",
            "title": "Service Health Overview",
            "folderTitle": "Services",
            "tags": ["services", "observability"],
            "updated": "2026-01-22T09:15:00Z",
            "created": "2025-12-10T12:00:00Z",
            "orgId": 1,
            "starred": False,
        },
    ]


@pytest.fixture
def mock_empty_dashboard_list() -> List[Dict[str, Any]]:
    """Fixture providing empty dashboard list response."""
    return []


@pytest.fixture
def mock_grafana_tool():
    """Fixture providing mock GrafanaMCPTool."""
    tool = AsyncMock()
    tool.list_dashboards = AsyncMock()
    tool.search_dashboards = AsyncMock()
    tool.get_dashboard = AsyncMock()
    return tool


@pytest.fixture
def mock_llm():
    """Fixture providing mock LLM (language model)."""
    llm = AsyncMock()
    llm.invoke = AsyncMock()
    llm.ainvoke = AsyncMock()
    return llm


@pytest.fixture
def test_config():
    """Fixture providing test configuration."""
    return {
        "grafana": {
            "url": "http://localhost:3000",
            "username": "mopadmin",
            "password": "moppassword",
            "org_id": 1,
        },
        "llm": {
            "api_key": "test-openai-key",
            "model": "gpt-4-turbo",
        },
        "agent": {
            "timeout": 30,
            "max_results": 100,
        },
    }


@pytest.fixture
def mock_agent_state():
    """Fixture providing mock LangGraph agent state."""
    return {
        "query": "Show me all dashboards",
        "intent": "list",
        "response": "",
        "status": "pending",
        "error_code": None,
        "data": None,
    }
