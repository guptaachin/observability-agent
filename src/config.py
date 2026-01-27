"""
Configuration management for Grafana Agent.

Loads configuration from environment variables and .env file.
"""

import os
import logging
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv


logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """Application configuration."""
    # Grafana
    grafana_url: str
    grafana_username: str
    grafana_password: str
    grafana_org_id: int
    
    # LLM
    openai_api_key: str
    openai_model: str
    
    # Agent
    agent_timeout: int
    max_results: int
    
    # Logging
    log_level: str


def load_config() -> AppConfig:
    """Load configuration from environment variables and .env file."""
    # Load .env file if it exists
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)

    # Load from environment variables
    openai_api_key = os.getenv("OPENAI_API_KEY", "")
    
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable required")
    
    logger.info(f"Loaded API key: {openai_api_key[:10]}...{openai_api_key[-4:] if len(openai_api_key) > 14 else ''}")
    
    return AppConfig(
        grafana_url=os.getenv("GRAFANA_URL", "http://localhost:3000"),
        grafana_username=os.getenv("GRAFANA_USERNAME", "mopadmin"),
        grafana_password=os.getenv("GRAFANA_PASSWORD", "moppassword"),
        grafana_org_id=int(os.getenv("GRAFANA_ORG_ID", "1")),
        openai_api_key=openai_api_key,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4-turbo"),
        agent_timeout=int(os.getenv("AGENT_TIMEOUT", "30")),
        max_results=int(os.getenv("MAX_RESULTS", "100")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )


def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration."""
    level = getattr(logging, log_level, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


if __name__ == "__main__":
    # Test configuration loading
    config = load_config()
    print(f"Grafana: {config.grafana_url}")
    print(f"LLM Model: {config.openai_model}")
    print(f"Agent Timeout: {config.agent_timeout}s")
    print(f"Agent Timeout: {config.agent.timeout}s")
