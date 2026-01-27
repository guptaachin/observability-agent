"""Configuration and LLM setup."""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


@dataclass
class Config:
    """Application configuration."""
    mcp_server_url: str = "http://localhost:8001"
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo"
    

def load_config() -> Config:
    """Load config from environment."""
    if Path(".env").exists():
        load_dotenv()
    
    return Config(
        mcp_server_url=os.getenv("MCP_SERVER_URL", "http://localhost:8001"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4-turbo"),
    )


def create_llm(config: Config) -> ChatOpenAI:
    """Create OpenAI LLM from config."""
    if not config.openai_api_key:
        raise ValueError("OPENAI_API_KEY not set")
    
    return ChatOpenAI(
        model=config.openai_model,
        api_key=config.openai_api_key,
        temperature=0,
    )
