"""Grafana MCP client - connects to MCP server via SSE."""

import json
import logging
from dataclasses import dataclass
from typing import Any, Optional
from contextlib import asynccontextmanager

from mcp import ClientSession
from mcp.client.sse import sse_client

from src.config import Config


logger = logging.getLogger(__name__)


class GrafanaError(Exception):
    """Grafana MCP error."""
    pass


@dataclass
class Dashboard:
    """Dashboard info from Grafana."""
    uid: str
    title: str
    folder: Optional[str] = None
    tags: Optional[list] = None
    url: Optional[str] = None


class GrafanaMCP:
    """Grafana MCP client using SSE transport."""

    def __init__(self, config: Config):
        self.mcp_url = config.mcp_server_url

    @asynccontextmanager
    async def _session(self):
        """Get MCP session."""
        async with sse_client(f"{self.mcp_url}/sse") as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session

    async def _call(self, tool: str, args: dict = None) -> Any:
        """Call MCP tool."""
        try:
            async with self._session() as session:
                result = await session.call_tool(tool, args or {})
                if result.content:
                    text = "\n".join(b.text for b in result.content if hasattr(b, 'text'))
                    if text.strip().startswith(('[', '{')):
                        return json.loads(text)
                    return text
                return None
        except Exception as e:
            raise GrafanaError(f"MCP call failed: {e}")

    async def list_dashboards(self, query: str = "") -> list[Dashboard]:
        """List/search dashboards."""
        args = {"query": query} if query else {}
        data = await self._call("search_dashboards", args)
        
        if not data:
            return []
        
        if isinstance(data, dict):
            data = data.get("dashboards", data.get("results", [data]))
        
        return [
            Dashboard(
                uid=d.get("uid", ""),
                title=d.get("title", "Untitled"),
                folder=d.get("folderTitle"),
                tags=d.get("tags", []),
                url=d.get("url"),
            )
            for d in (data if isinstance(data, list) else [data])
        ]

    async def list_tools(self) -> list[str]:
        """List available MCP tools."""
        async with self._session() as session:
            result = await session.list_tools()
            return [t.name for t in result.tools]


if __name__ == "__main__":
    import asyncio
    from src.config import load_config
    
    async def main():
        config = load_config()
        mcp = GrafanaMCP(config)
        
        print("Tools:", await mcp.list_tools())
        print("\nDashboards:")
        for d in await mcp.list_dashboards():
            print(f"  - {d.title} ({d.uid})")
    
    asyncio.run(main())
