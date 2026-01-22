"""Agent module for natural language metrics queries.

Exports the main agent factory and state TypedDict for use in UI layer.
"""

from src.agent.metrics_agent import create_agent, MetricsQueryState

__all__ = ["create_agent", "MetricsQueryState"]
