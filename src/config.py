"""
Configuration loader for the observability agent.

This module reads required environment variables, validates them, and
exposes a cached `get_config()` function so the configuration is only
read/validated once per process.
"""

from functools import lru_cache
import os
from typing import Optional, Literal


class Config:
    def __init__(
        self,
        mcp_grafana_host: str,
        mcp_grafana_port: int,
        llm_source: Literal["openai", "ollama"],
        openai_api_key: Optional[str],
        ollama_base_url: str,
        gradio_server_port: int,
    ) -> None:
        self.mcp_grafana_host = mcp_grafana_host
        self.mcp_grafana_port = mcp_grafana_port
        self.llm_source = llm_source
        self.openai_api_key = openai_api_key
        self.ollama_base_url = ollama_base_url
        self.gradio_server_port = gradio_server_port

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return (
            f"Config(mcp_grafana_host={self.mcp_grafana_host!r}, mcp_grafana_port={self.mcp_grafana_port!r},"
            f" llm_source={self.llm_source!r}, ollama_base_url={self.ollama_base_url!r},"
            f" gradio_server_port={self.gradio_server_port!r})"
        )


def _get_env_int(name: str, default: Optional[int] = None) -> int:
    val = os.getenv(name)
    if val is None:
        if default is None:
            raise ValueError(f"Environment variable {name} is required")
        return default
    try:
        return int(val)
    except Exception as e:
        raise ValueError(f"Environment variable {name} must be an integer: {e}")


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Read environment variables, validate them, and return a `Config`.

    Raises:
        ValueError: if required variables are missing or invalid.
    """
    mcp_grafana_host = os.getenv("MCP_GRAFANA_HOST", "localhost")
    mcp_grafana_port = _get_env_int("MCP_GRAFANA_PORT", 8000)

    llm_source = os.getenv("LLM_SOURCE", "openai").lower()
    if llm_source not in ("openai", "ollama"):
        raise ValueError("LLM_SOURCE must be either 'openai' or 'ollama'")

    openai_api_key = os.getenv("OPENAI_API_KEY")
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    if llm_source == "openai" and not openai_api_key:
        raise ValueError("OPENAI_API_KEY is required when LLM_SOURCE=openai")

    gradio_server_port = _get_env_int("GRADIO_SERVER_PORT", 7860)

    return Config(
        mcp_grafana_host=mcp_grafana_host,
        mcp_grafana_port=mcp_grafana_port,
        llm_source=llm_source, 
        openai_api_key=openai_api_key,
        ollama_base_url=ollama_base_url,
        gradio_server_port=gradio_server_port,
    )
