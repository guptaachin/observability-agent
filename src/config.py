"""Configuration management for the observability agent."""

import os
from functools import lru_cache
from dotenv import load_dotenv
from pydantic import BaseModel, field_validator

# Load .env file from project root
load_dotenv()


class Config(BaseModel):
    """Application configuration loaded from environment variables."""

    mcp_grafana_host: str
    mcp_grafana_port: int
    llm_source: str
    openai_api_key: str | None = None
    ollama_base_url: str | None = None
    gradio_server_port: int

    @field_validator("llm_source")
    @classmethod
    def validate_llm_source(cls, v: str) -> str:
        """Ensure LLM source is valid."""
        if v not in ("openai", "ollama"):
            raise ValueError(f"LLM_SOURCE must be 'openai' or 'ollama', got '{v}'")
        return v

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v: str | None, info) -> str | None:
        """Ensure OpenAI key is provided when using OpenAI."""
        llm_source = info.data.get("llm_source")
        if llm_source == "openai" and not v:
            raise ValueError("OPENAI_API_KEY is required when LLM_SOURCE=openai")
        return v.strip() if v else None

    @field_validator("ollama_base_url")
    @classmethod
    def validate_ollama_url(cls, v: str | None, info) -> str | None:
        """Ensure Ollama URL is provided when using Ollama."""
        llm_source = info.data.get("llm_source")
        if llm_source == "ollama" and not v:
            raise ValueError("OLLAMA_BASE_URL is required when LLM_SOURCE=ollama")
        return v


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Load and cache configuration from environment variables."""
    return Config(
        mcp_grafana_host=os.getenv("MCP_GRAFANA_HOST", "localhost"),
        mcp_grafana_port=int(os.getenv("MCP_GRAFANA_PORT", "8000")),
        llm_source=os.getenv("LLM_SOURCE", "openai"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL"),
        gradio_server_port=int(os.getenv("GRADIO_SERVER_PORT", "7860")),
    )