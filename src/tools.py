"""
Grafana MCP Server tool wrapper for dashboard retrieval.

This module provides GrafanaMCPTool class that communicates exclusively
with Grafana via the MCP (Model Context Protocol) server.

No direct Grafana API calls are made; all communication routes through MCP.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from src.config import GrafanaConfig


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

    This class is responsible for:
    - Initializing connection to MCP server
    - Calling dashboard retrieval endpoints
    - Parsing and validating responses
    - Converting to internal data structures
    """

    def __init__(self, config: GrafanaConfig):
        """
        Initialize Grafana MCP tool.

        Args:
            config: GrafanaConfig with connection details
        """
        self.config = config
        self.mcp_client = None
        logger.info(f"GrafanaMCPTool initialized for {config.url}")

    async def _init_mcp_connection(self) -> None:
        """
        Initialize MCP server connection (placeholder).

        In a full implementation, this would:
        1. Start MCP client process
        2. Initialize stdio transport
        3. Authenticate with credentials
        4. Verify connection health

        For now, this is a placeholder that demonstrates the pattern.
        """
        # TODO: Implement actual MCP client initialization
        # This would use the mcp Python package to:
        # - Create MCPClient instance
        # - Set up stdio transport
        # - Call Grafana endpoints through MCP
        logger.debug("MCP connection initialized")

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
            # TODO: Replace with actual MCP call
            # Example: response = await self.mcp_client.call("grafana_list_dashboards")
            
            # For now, return empty list (will be populated by tests via mocks)
            logger.info("Calling MCP server: list_dashboards")
            
            # Simulate MCP call (in real implementation, this calls actual MCP)
            dashboards = self._simulate_mcp_list_dashboards()
            
            logger.info(f"Retrieved {len(dashboards)} dashboards from Grafana")
            return dashboards

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
            logger.info(f"Searching dashboards with query: {query}")
            
            # TODO: Replace with actual MCP call
            # Example: response = await self.mcp_client.call("grafana_search_dashboards", {"query": query})
            
            all_dashboards = await self.list_dashboards()
            
            # Filter by name or tags
            query_lower = query.lower()
            filtered = [
                d for d in all_dashboards
                if query_lower in d.title.lower()
                or (d.tags and any(query_lower in tag.lower() for tag in d.tags))
            ]
            
            logger.info(f"Search returned {len(filtered)} matching dashboards")
            return filtered

        except GrafanaConnectionError:
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
            logger.info(f"Getting dashboard: {uid}")
            
            # TODO: Replace with actual MCP call
            # Example: response = await self.mcp_client.call("grafana_get_dashboard", {"uid": uid})
            
            all_dashboards = await self.list_dashboards()
            dashboard = next((d for d in all_dashboards if d.uid == uid), None)
            
            if not dashboard:
                raise GrafanaDataError(f"Dashboard not found: {uid}")
            
            return dashboard

        except GrafanaConnectionError:
            raise
        except GrafanaDataError:
            raise
        except Exception as e:
            logger.error(f"Error getting dashboard {uid}: {e}")
            raise GrafanaDataError(f"Unable to get dashboard: {e}")

    def _simulate_mcp_list_dashboards(self) -> List[DashboardMetadata]:
        """
        Simulate MCP response for list_dashboards (for testing/demo).

        In production, this would be replaced with actual MCP call.
        """
        # This is a placeholder that returns empty list
        # Tests will mock this to return sample data
        return []


async def create_grafana_tool(config: GrafanaConfig) -> GrafanaMCPTool:
    """
    Factory function to create and initialize GrafanaMCPTool.

    Args:
        config: GrafanaConfig with connection details

    Returns:
        Initialized GrafanaMCPTool instance

    Raises:
        GrafanaConnectionError: If MCP server cannot be reached
    """
    tool = GrafanaMCPTool(config)
    await tool._init_mcp_connection()
    return tool


if __name__ == "__main__":
    # Test tool initialization
    from src.config import load_config

    async def test():
        config = load_config()
        tool = await create_grafana_tool(config.grafana)
        
        try:
            dashboards = await tool.list_dashboards()
            print(f"Found {len(dashboards)} dashboards")
        except GrafanaConnectionError as e:
            logger.warning(f"MCP connection issue (expected in dev): {e}")

    asyncio.run(test())
