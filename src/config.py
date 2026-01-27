"""
Configuration management for Grafana Agent.

Loads configuration from environment variables, .env file, and YAML.
Provides Pydantic models for type-safe configuration.
"""

import os
import logging
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv
import yaml


logger = logging.getLogger(__name__)


class GrafanaConfig(BaseModel):
    """Grafana connection configuration."""
    url: str = Field(default="http://localhost:3000", description="Grafana base URL")
    username: str = Field(default="admin", description="Grafana username")
    password: str = Field(default="admin", description="Grafana password")
    org_id: int = Field(default=1, ge=1, description="Grafana organization ID")
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure URL doesn't end with slash."""
        return v.rstrip('/')


class LLMConfig(BaseModel):
    """LLM provider configuration."""
    provider: str = Field(default="openai", description="LLM provider (openai or ollama)")
    api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    model: str = Field(default="gpt-4-turbo", description="Model name")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="Temperature for generation")
    base_url: Optional[str] = Field(default=None, description="Base URL for Ollama or custom endpoint")


class AgentConfig(BaseModel):
    """Agent behavior configuration."""
    timeout: int = Field(default=30, ge=1, description="Query timeout in seconds")
    max_results: int = Field(default=100, ge=1, description="Maximum dashboards to return")


class MCPConfig(BaseModel):
    """MCP Server configuration."""
    server_url: str = Field(default="http://localhost:8001", description="MCP server URL (SSE transport)")
    
    @field_validator('server_url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure URL doesn't end with slash."""
        return v.rstrip('/')


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO", description="Log level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )


class AppConfig(BaseModel):
    """Complete application configuration."""
    grafana: GrafanaConfig = Field(default_factory=GrafanaConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    
    # Convenience properties for backward compatibility
    @property
    def grafana_url(self) -> str:
        return self.grafana.url
    
    @property
    def grafana_username(self) -> str:
        return self.grafana.username
    
    @property
    def grafana_password(self) -> str:
        return self.grafana.password
    
    @property
    def grafana_org_id(self) -> int:
        return self.grafana.org_id
    
    @property
    def agent_timeout(self) -> int:
        return self.agent.timeout
    
    @property
    def max_results(self) -> int:
        return self.agent.max_results
    
    @property
    def mcp_server_url(self) -> str:
        return self.mcp.server_url


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """
    Load configuration from multiple sources with priority:
    1. Environment variables (highest priority)
    2. .env file
    3. YAML config file
    4. Defaults (lowest priority)
    
    Args:
        config_path: Optional path to YAML config file
        
    Returns:
        AppConfig instance with merged configuration
    """
    # Load .env file if it exists
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)
        logger.debug(f"Loaded configuration from {env_file}")
    
    # Load YAML config if provided or default exists
    yaml_config = {}
    if config_path is None:
        config_path = Path("config/config.yaml")
    
    if config_path.exists():
        try:
            with open(config_path) as f:
                yaml_config = yaml.safe_load(f) or {}
            logger.debug(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.warning(f"Failed to load YAML config: {e}")
    
    # Build configuration with environment variable overrides
    config_dict = {
        "grafana": {
            "url": os.getenv("GRAFANA_URL", yaml_config.get("grafana", {}).get("url", "http://localhost:3000")),
            "username": os.getenv("GRAFANA_USERNAME", yaml_config.get("grafana", {}).get("username", "admin")),
            "password": os.getenv("GRAFANA_PASSWORD", yaml_config.get("grafana", {}).get("password", "admin")),
            "org_id": int(os.getenv("GRAFANA_ORG_ID", yaml_config.get("grafana", {}).get("org_id", 1))),
        },
        "llm": {
            "provider": os.getenv("LLM_PROVIDER", yaml_config.get("llm", {}).get("provider", "openai")),
            "api_key": os.getenv("OPENAI_API_KEY", yaml_config.get("llm", {}).get("api_key")),
            "model": os.getenv("OPENAI_MODEL", yaml_config.get("llm", {}).get("model", "gpt-4-turbo")),
            "temperature": float(os.getenv("LLM_TEMPERATURE", yaml_config.get("llm", {}).get("temperature", 0.0))),
            "base_url": os.getenv("OLLAMA_BASE_URL", yaml_config.get("llm", {}).get("base_url")),
        },
        "agent": {
            "timeout": int(os.getenv("AGENT_TIMEOUT", yaml_config.get("agent", {}).get("timeout", 30))),
            "max_results": int(os.getenv("MAX_RESULTS", yaml_config.get("agent", {}).get("max_results", 100))),
        },
        "logging": {
            "level": os.getenv("LOG_LEVEL", yaml_config.get("logging", {}).get("level", "INFO")),
            "format": yaml_config.get("logging", {}).get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
        },
        "mcp": {
            "server_url": os.getenv("MCP_SERVER_URL", yaml_config.get("mcp", {}).get("server_url", "http://localhost:8001")),
        },
    }
    
    return AppConfig(**config_dict)


def setup_logging(config: Optional[AppConfig] = None, log_level: Optional[str] = None) -> None:
    """
    Setup logging configuration.
    
    Args:
        config: Optional AppConfig with logging settings
        log_level: Override log level (e.g., "DEBUG", "INFO")
    """
    if config:
        level_str = log_level or config.logging.level
        format_str = config.logging.format
    else:
        level_str = log_level or "INFO"
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    level = getattr(logging, level_str.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format=format_str,
        force=True  # Override any existing configuration
    )


if __name__ == "__main__":
    # Test configuration loading
    config = load_config()
    print(f"Grafana: {config.grafana.url}")
    print(f"LLM Model: {config.llm.model}")
    print(f"Agent Timeout: {config.agent.timeout}s")
