#!/usr/bin/env python3
"""
Demo script for manual testing of the Grafana agent.

Usage: python demo.py

This script runs a few example queries against the agent with mock Grafana data.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

from src.config import AppConfig, GrafanaConfig, LLMConfig, AgentConfig
from src.tools import DashboardMetadata
from src.agent import create_agent


async def create_mock_components():
    """Create mock LLM and Grafana tool for demo."""
    # Mock Grafana tool
    now = datetime.now()
    sample_dashboards = [
        DashboardMetadata(
            id=1,
            uid="prod-api",
            title="Prod API Dashboard",
            updated=now - timedelta(hours=2),
            folder_title="Production",
            tags=["production", "api"],
            org_id=1,
            starred=True,
        ),
        DashboardMetadata(
            id=2,
            uid="db-perf",
            title="Database Performance",
            updated=now - timedelta(days=1),
            folder_title="Infrastructure",
            tags=["database", "performance"],
            org_id=1,
            starred=False,
        ),
        DashboardMetadata(
            id=3,
            uid="service-health",
            title="Service Health",
            updated=now - timedelta(hours=24),
            folder_title="Monitoring",
            tags=["services", "health"],
            org_id=1,
            starred=True,
        ),
    ]

    grafana_tool = AsyncMock()
    grafana_tool.list_dashboards = AsyncMock(return_value=sample_dashboards)
    grafana_tool.search_dashboards = AsyncMock(return_value=sample_dashboards[:1])
    grafana_tool.get_dashboard = AsyncMock(return_value=sample_dashboards[0])

    # Mock LLM
    llm = AsyncMock()
    response = MagicMock()
    response.content = "Here are all available dashboards in your Grafana instance."
    llm.ainvoke = AsyncMock(return_value=response)

    # Config
    config = AppConfig(
        grafana=GrafanaConfig(
            url="http://localhost:3000",
            username="admin",
            password="admin",
            org_id=1,
        ),
        llm=LLMConfig(provider="openai"),
        agent=AgentConfig(timeout=30, max_results=100),
    )

    return config, llm, grafana_tool


async def demo():
    """Run demo queries."""
    print("=" * 70)
    print("Grafana Agent Demo")
    print("=" * 70)
    print()

    # Setup
    config, llm, grafana_tool = await create_mock_components()
    agent = await create_agent(config, llm, grafana_tool)

    # Demo queries
    demo_queries = [
        "Show me all dashboards",
        "What dashboards are available?",
        "List dashboards with prod in the name",
        "Show me dashboards with database",
        "When was the Prod API dashboard updated?",
        "Tell me about the Service Health dashboard",
        "Analyze the performance trends",  # Out of scope
    ]

    for i, query in enumerate(demo_queries, 1):
        print(f"Query {i}: {query}")
        print("-" * 70)
        
        try:
            result = await agent.ainvoke({"query": query})
            
            status = result.get("status", "unknown")
            response = result.get("response", "No response")
            
            print(f"Status: {status}")
            print(f"Response:\n{response}")
            
        except Exception as e:
            print(f"Error: {e}")
        
        print()


if __name__ == "__main__":
    asyncio.run(demo())
