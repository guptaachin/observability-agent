"""
Grafana MCP Server tool wrapper for dashboard retrieval.

This module provides GrafanaMCPTool class that communicates exclusively
with Grafana via the MCP (Model Context Protocol) server running in Docker.

No direct Grafana API calls are made; all communication routes through MCP.
"""

import logging
import asyncio
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from contextlib import asynccontextmanager

from mcp import ClientSession
from mcp.client.sse import sse_client

from src.config import AppConfig


logger = logging.getLogger(__name__)


# Exception hierarchy for Grafana errors
class GrafanaError(Exception):
    """Base exception for Grafana-related errors."""
    pass


class GrafanaConnectionError(GrafanaError):
    """Raised when connection to Grafana MCP server fails."""
    pass


class GrafanaAuthError(GrafanaError):
    """Raised when authentication with Grafana fails."""
    pass


class GrafanaDataError(GrafanaError):
    """Raised when Grafana returns malformed or incomplete data."""
    pass


@dataclass
class DashboardMetadata:
    """Dashboard metadata returned from Grafana."""

    id: str
    uid: str
    title: str
    updated: str  # ISO 8601 datetime
    folder_title: Optional[str] = None
    tags: Optional[List[str]] = None
    org_id: int = 1
    starred: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "uid": self.uid,
            "title": self.title,
            "updated": self.updated,
            "folder_title": self.folder_title,
            "tags": self.tags or [],
            "org_id": self.org_id,
            "starred": self.starred,
        }


class GrafanaMCPTool:
    """
    Wrapper for Grafana MCP Server communication.

    This class communicates with the Grafana MCP server running in Docker
    via SSE (Server-Sent Events) transport using the Model Context Protocol.
    """

    def __init__(self, config: AppConfig):
        """
        Initialize Grafana MCP tool.

        Args:
            config: AppConfig with Grafana connection details
        """
        self.config = config
        self.mcp_url = config.mcp_server_url
        logger.info(f"GrafanaMCPTool initialized, MCP server at {self.mcp_url}")

    @asynccontextmanager
    async def _get_session(self):
        """
        Context manager for MCP session via SSE.
        
        Connects to the running Docker MCP server via HTTP/SSE transport.
        
        Yields:
            ClientSession: Active MCP session
        """
        sse_url = f"{self.mcp_url}/sse"
        
        async with sse_client(sse_url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                logger.debug(f"MCP session initialized via SSE at {sse_url}")
                yield session

    async def _call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
        """
        Call an MCP tool and return the result.
        
        Args:
            tool_name: Name of the MCP tool to call
            arguments: Optional arguments to pass to the tool
            
        Returns:
            Tool result content
            
        Raises:
            GrafanaConnectionError: If connection fails
            GrafanaDataError: If tool returns error
        """
        try:
            async with self._get_session() as session:
                logger.debug(f"Calling MCP tool: {tool_name} with args: {arguments}")
                
                result = await session.call_tool(tool_name, arguments or {})
                
                # Extract content from result
                if result.content:
                    # MCP returns content as list of content blocks
                    content_parts = []
                    for block in result.content:
                        if hasattr(block, 'text'):
                            content_parts.append(block.text)
                    
                    combined = "\n".join(content_parts)
                    
                    # Try to parse as JSON if it looks like JSON
                    if combined.strip().startswith(('[', '{')):
                        try:
                            return json.loads(combined)
                        except json.JSONDecodeError:
                            return combined
                    return combined
                
                return None
                
        except Exception as e:
            logger.error(f"MCP tool call failed: {tool_name} - {e}")
            raise GrafanaConnectionError(f"Failed to call {tool_name}: {e}")

    async def list_tools(self) -> List[str]:
        """
        List available tools from the MCP server.
        
        Returns:
            List of tool names available on the server
        """
        try:
            async with self._get_session() as session:
                result = await session.list_tools()
                tools = [tool.name for tool in result.tools]
                logger.info(f"Available MCP tools: {tools}")
                return tools
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            raise GrafanaConnectionError(f"Failed to list tools: {e}")

    async def list_dashboards(self) -> List[DashboardMetadata]:
        """
        Retrieve all dashboards from Grafana via MCP server.

        Returns:
            List of DashboardMetadata objects for all dashboards

        Raises:
            GrafanaConnectionError: If MCP server unreachable
            GrafanaAuthError: If authentication fails
            GrafanaDataError: If response is malformed
        """
        try:
            logger.info("Calling MCP server: search_dashboards")
            
            # Call the Grafana MCP search_dashboards tool
            result = await self._call_tool("search_dashboards", {})
            
            # Parse the response
            dashboards = self._parse_dashboard_list(result)
            
            logger.info(f"Retrieved {len(dashboards)} dashboards from Grafana")
            return dashboards

        except GrafanaConnectionError:
            raise
        except GrafanaAuthError:
            raise
        except GrafanaDataError:
            raise
        except Exception as e:
            logger.error(f"Error listing dashboards: {e}")
            raise GrafanaConnectionError(f"Unable to list dashboards: {e}")

    async def search_dashboards(self, query: str) -> List[DashboardMetadata]:
        """
        Search dashboards by name or tags via MCP server.

        Args:
            query: Search query string (e.g., "prod", "monitoring")

        Returns:
            List of DashboardMetadata matching the query

        Raises:
            GrafanaConnectionError: If MCP server unreachable
            GrafanaDataError: If response is malformed
        """
        try:
            if not query or not query.strip():
                raise GrafanaDataError("Search query cannot be empty")
            
            logger.info(f"Searching dashboards with query: {query}")
            
            # Call MCP search with query parameter
            result = await self._call_tool("search_dashboards", {"query": query})
            
            # Parse and return results
            dashboards = self._parse_dashboard_list(result)
            
            logger.info(f"Search returned {len(dashboards)} matching dashboards")
            return dashboards

        except GrafanaConnectionError:
            raise
        except GrafanaDataError:
            raise
        except Exception as e:
            logger.error(f"Error searching dashboards: {e}")
            raise GrafanaDataError(f"Unable to search dashboards: {e}")

    async def get_dashboard(self, uid: str) -> DashboardMetadata:
        """
        Retrieve single dashboard by UID via MCP server.

        Args:
            uid: Dashboard UID (unique identifier)

        Returns:
            DashboardMetadata for the requested dashboard

        Raises:
            GrafanaConnectionError: If MCP server unreachable
            GrafanaDataError: If dashboard not found or response malformed
        """
        try:
            if not uid or not uid.strip():
                raise GrafanaDataError("Dashboard UID cannot be empty")
            
            logger.info(f"Getting dashboard: {uid}")
            
            # Call MCP get_dashboard_by_uid tool
            result = await self._call_tool("get_dashboard_by_uid", {"uid": uid})
            
            if not result:
                raise GrafanaDataError(f"Dashboard not found: {uid}")
            
            # Parse single dashboard
            dashboard = self._parse_dashboard(result)
            
            logger.info(f"Retrieved dashboard: {dashboard.title}")
            return dashboard

        except GrafanaConnectionError:
            raise
        except GrafanaDataError:
            raise
        except Exception as e:
            logger.error(f"Error getting dashboard {uid}: {e}")
            raise GrafanaDataError(f"Unable to get dashboard: {e}")

    def _parse_dashboard_list(self, data: Any) -> List[DashboardMetadata]:
        """
        Parse raw dashboard data into DashboardMetadata objects.
        
        Args:
            data: Response data from MCP (can be list, dict, or string)
            
        Returns:
            List of DashboardMetadata objects
            
        Raises:
            GrafanaDataError: If data is malformed
        """
        try:
            # Handle different response formats
            if data is None:
                return []
            
            if isinstance(data, str):
                # Try to parse as JSON
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse response as JSON: {data[:100]}")
                    return []
            
            # If data is a dict with a list inside (e.g., {"dashboards": [...]})
            if isinstance(data, dict):
                if "dashboards" in data:
                    data = data["dashboards"]
                elif "results" in data:
                    data = data["results"]
                else:
                    # Single dashboard wrapped in dict
                    data = [data]
            
            if not isinstance(data, list):
                data = [data]
            
            parsed_dashboards = []
            for item in data:
                try:
                    dashboard = self._parse_dashboard(item)
                    parsed_dashboards.append(dashboard)
                except Exception as e:
                    logger.warning(f"Skipping malformed dashboard entry: {e}")
                    continue
            
            return parsed_dashboards
            
        except Exception as e:
            logger.error(f"Error parsing dashboard data: {e}")
            raise GrafanaDataError(f"Malformed dashboard data: {e}")

    def _parse_dashboard(self, data: Dict[str, Any]) -> DashboardMetadata:
        """
        Parse a single dashboard dict into DashboardMetadata.
        
        Args:
            data: Dashboard dictionary from MCP response
            
        Returns:
            DashboardMetadata object
        """
        if isinstance(data, str):
            data = json.loads(data)
        
        return DashboardMetadata(
            id=str(data.get("id", "")),
            uid=data.get("uid", ""),
            title=data.get("title", "Untitled"),
            updated=data.get("updated", data.get("updatedAt", "")),
            folder_title=data.get("folderTitle") or data.get("folder_title") or data.get("folderName"),
            tags=data.get("tags", []),
            org_id=data.get("orgId", 1) or data.get("org_id", 1),
            starred=data.get("isStarred", False) or data.get("starred", False),
        )


async def create_grafana_tool(config: AppConfig) -> GrafanaMCPTool:
    """
    Factory function to create GrafanaMCPTool.

    Args:
        config: AppConfig with Grafana connection details

    Returns:
        GrafanaMCPTool instance ready for use

    Raises:
        GrafanaConnectionError: If MCP server cannot be reached
    """
    tool = GrafanaMCPTool(config)
    
    # Verify connection by listing tools
    try:
        tools = await tool.list_tools()
        logger.info(f"Connected to Grafana MCP server. Available tools: {tools}")
    except Exception as e:
        logger.warning(f"Could not verify MCP connection: {e}")
    
    return tool


if __name__ == "__main__":
    # Test tool initialization
    from src.config import load_config
    
    logging.basicConfig(level=logging.DEBUG)

    async def test():
        config = load_config()
        print(f"Connecting to Grafana at {config.grafana_url}...")
        
        tool = GrafanaMCPTool(config)
        
        try:
            # List available tools
            print("\n=== Available MCP Tools ===")
            tools = await tool.list_tools()
            for t in tools:
                print(f"  - {t}")
            
            # List dashboards
            print("\n=== Dashboards ===")
            dashboards = await tool.list_dashboards()
            print(f"Found {len(dashboards)} dashboards:")
            for d in dashboards:
                print(f"  - {d.title} (uid: {d.uid})")
                
        except GrafanaConnectionError as e:
            print(f"Connection error: {e}")
        except Exception as e:
            print(f"Error: {e}")

    asyncio.run(test())
