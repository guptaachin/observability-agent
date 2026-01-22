"""
Simple MCP client for calling tools on a Grafana MCP server.

This client uses HTTP POST to call named tools on the MCP server. It is
minimal and focused on the needs of the exercise (timeouts, JSON requests,
and clear error wrapping).
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Optional

import aiohttp


class MCPClientError(RuntimeError):
    pass


class MCPClient:
    def __init__(self, host: str = "localhost", port: int = 8000, *, timeout: float = 5.0) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    async def connect(self) -> None:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)

    async def disconnect(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the MCP server and return the parsed JSON response.

        Args:
            tool_name: Name of the tool to invoke (e.g., 'query_grafana_metrics')
            arguments: JSON-serializable arguments for the tool

        Returns:
            Parsed JSON response (as dict)

        Raises:
            MCPClientError on network errors, timeouts, or non-JSON responses
        """
        await self.connect()
        assert self._session is not None

        url = f"{self.base_url}/tools/{tool_name}"
        try:
            async with self._session.post(url, json=arguments) as resp:
                text = await resp.text()
                if resp.status >= 400:
                    raise MCPClientError(f"MCP server returned status {resp.status}: {text}")
                try:
                    return json.loads(text)
                except Exception as e:
                    raise MCPClientError(f"Failed to parse MCP response as JSON: {e}; body={text}") from e
        except asyncio.TimeoutError as e:
            raise MCPClientError("MCP server call timed out") from e
        except aiohttp.ClientError as e:
            raise MCPClientError(f"Network error when calling MCP server: {e}") from e
