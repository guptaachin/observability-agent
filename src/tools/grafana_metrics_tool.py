"""
Grafana metrics tool that calls the Grafana MCP server via MCPClient.

Provides an async function `query_grafana_metrics` which takes a
`MetricsQuery` and returns a `MetricsQueryResult`. Errors are translated
into `QueryError` instances.
"""

from __future__ import annotations

from typing import Any, Dict, List
import asyncio

from src.models.query import MetricsQuery
from src.models.result import DataPoint, MetricsQueryResult, QueryError
from src.tools.mcp_client import MCPClient, MCPClientError


try:
    # langchain's @tool decorator is optional for runtime; fall back to noop
    from langchain.tools import tool
except Exception:
    def tool(func):
        return func


@tool
async def query_grafana_metrics(query: MetricsQuery) -> Any:
    """
    Query Grafana via the MCP server and return a MetricsQueryResult.

    This function formats the `MetricsQuery` into the MCP tool args,
    calls the MCP server, and converts the response into our internal
    `MetricsQueryResult` model. On errors it returns a `QueryError`.
    """
    client = MCPClient()
    mcp_request = query.to_mcp_request()
    try:
        resp = await client.call_tool("query_grafana_metrics", mcp_request)
    except MCPClientError as e:
        return QueryError(error_type="grafana_unavailable", message=str(e), suggestion="Check Grafana MCP server")

    # Expect response containing: metric_name, unit, time_range, datapoints
    try:
        metric_name = resp.get("metric_name")
        unit = resp.get("unit", "")
        tr = resp.get("time_range", {})
        datapoints_raw: List[Dict[str, Any]] = resp.get("datapoints", [])

        datapoints = [DataPoint(timestamp=dp["timestamp"], value=float(dp["value"])) for dp in datapoints_raw]

        result = MetricsQueryResult(
            metric_name=metric_name,
            unit=unit,
            time_range=query.time_range,
            datapoints=datapoints,
            aggregation_applied=query.aggregation,
            datapoint_count=len(datapoints),
        )
        return result
    except Exception as e:
        return QueryError(error_type="invalid_query", message=f"Invalid response from MCP server: {e}", suggestion="Verify MCP server tool output format")
