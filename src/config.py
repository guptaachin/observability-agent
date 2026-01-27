"""
Configuration management for Grafana Agent.

Loads configuration from multiple sources (in order of precedence):
1. Environment variables
2. .env file (via python-dotenv)
3. config/config.yaml (if exists)
4. Hardcoded defaults

All configuration uses pydantic for validation and type safety.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator
import yaml
from dotenv import load_dotenv


logger = logging.getLogger(__name__)


class GrafanaConfig(BaseModel):
    """Grafana connection configuration."""

    url: str = Field(default="http://localhost:3000", description="Grafana URL")
    username: str = Field(default="mopadmin", description="Grafana username")
    password: str = Field(default="moppassword", description="Grafana password")
    org_id: int = Field(default=1, description="Grafana organization ID")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator("org_id")
    @classmethod
    def validate_org_id(cls, v: int) -> int:
        """Validate org ID is positive."""
        if v <= 0:
            raise ValueError("org_id must be positive integer")
        return v


class LLMConfig(BaseModel):
    """OpenAI LLM configuration."""

    api_key: str = Field(description="OpenAI API key")
    model: str = Field(default="gpt-4-turbo", description="Model name")


class AgentConfig(BaseModel):
    """Agent runtime configuration."""

    timeout: int = Field(default=30, description="Query timeout in seconds")
    max_results: int = Field(default=100, description="Maximum dashboards to return")

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        """Validate timeout is positive."""
        if v <= 0:
            raise ValueError("timeout must be positive integer")
        return v


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Log level")
    format: Literal["plain", "json"] = Field(default="plain", description="Log format")


class AppConfig(BaseModel):
    """Complete application configuration."""

    grafana: GrafanaConfig = Field(default_factory=GrafanaConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def load_config(config_file: Optional[str] = None) -> AppConfig:
    """
    Load configuration from all sources.

    Priority (highest to lowest):
    1. Environment variables
    2. .env file
    3. config/config.yaml file
    4. Hardcoded defaults

    Args:
        config_file: Optional path to YAML config file. If not provided,
                    looks for config/config.yaml relative to repo root.

    Returns:
        AppConfig: Validated configuration object

    Raises:
        FileNotFoundError: If config_file specified but not found
        ValueError: If configuration validation fails
    """
    # Load .env file if it exists
    env_file = Path(".env")
    if env_file.exists():
        logger.info(f"Loading environment from {env_file}")
        load_dotenv(env_file)

    # Start with defaults
    config_dict = {
        "grafana": {
            "url": os.getenv("GRAFANA_URL", "http://localhost:3000"),
            "username": os.getenv("GRAFANA_USERNAME", "mopadmin"),
            "password": os.getenv("GRAFANA_PASSWORD", "moppassword"),
            "org_id": int(os.getenv("GRAFANA_ORG_ID", "1")),
        },
        "llm": {
            "api_key": os.getenv("OPENAI_API_KEY", ""),
            "model": os.getenv("OPENAI_MODEL", "gpt-4-turbo"),
        },
        "agent": {
            "timeout": int(os.getenv("AGENT_TIMEOUT", "30")),
            "max_results": int(os.getenv("MAX_RESULTS", "100")),
        },
        "logging": {
            "level": os.getenv("LOG_LEVEL", "INFO"),
        },
    }

    # Validate OpenAI API key
    if not config_dict["llm"]["api_key"]:
        raise ValueError(
            "OPENAI_API_KEY environment variable required"
        )

    # Try to load from YAML config file if provided or exists
    if config_file is None:
        config_file = "config/config.yaml"

    if config_file and Path(config_file).exists():
        logger.info(f"Loading YAML configuration from {config_file}")
        with open(config_file, "r") as f:
            yaml_config = yaml.safe_load(f)
            if yaml_config:
                # Merge YAML config (only override if keys exist in YAML)
                if "grafana" in yaml_config:
                    config_dict["grafana"].update(yaml_config["grafana"])
                if "llm" in yaml_config:
                    config_dict["llm"].update(yaml_config["llm"])
                if "agent" in yaml_config:
                    config_dict["agent"].update(yaml_config["agent"])
                if "logging" in yaml_config:
                    config_dict["logging"].update(yaml_config["logging"])

    # Validate and create config object
    try:
        config = AppConfig(**config_dict)
        logger.info(f"Configuration loaded successfully (model: {config.llm.model})")
        return config
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        raise


def setup_logging(config: AppConfig) -> None:
    """
    Setup logging based on configuration.

    Args:
        config: AppConfig object with logging configuration
    """
    log_level = getattr(logging, config.logging.level, logging.INFO)
    
    if config.logging.format == "json":
        # JSON format (future: use python-json-logger)
        formatter = logging.Formatter("%(message)s")
    else:
        # Plain text format
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Add console handler if not already present
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)


if __name__ == "__main__":
    # Test configuration loading
    config = load_config()
    print(f"Grafana: {config.grafana.url}")
    print(f"LLM Model: {config.llm.model}")
    print(f"Agent Timeout: {config.agent.timeout}s")
