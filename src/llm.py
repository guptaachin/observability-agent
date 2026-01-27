"""
LLM initialization for Grafana Agent.

Supports OpenAI models: gpt-4-turbo, gpt-3.5-turbo, etc.
"""

import logging
from langchain_openai import ChatOpenAI
from src.config import AppConfig


logger = logging.getLogger(__name__)


def create_llm_from_app_config(app_config: AppConfig) -> ChatOpenAI:
    """
    Create OpenAI LLM from app configuration.

    Args:
        app_config: AppConfig object with OpenAI configuration

    Returns:
        Initialized ChatOpenAI instance

    Raises:
        ValueError: If configuration is invalid or LLM cannot connect
    """
    logger.info(f"Initializing OpenAI LLM: {app_config.openai_model}")
    
    if not app_config.openai_api_key:
        raise ValueError("OpenAI API key not configured")
    
    return ChatOpenAI(
        model=app_config.openai_model,
        api_key=app_config.openai_api_key,
        temperature=0.0,  # Deterministic responses for dashboard retrieval
        max_tokens=1024,
    )


if __name__ == "__main__":
    # Test LLM initialization
    from src.config import load_config
    
    config = load_config()
    llm = create_llm_from_app_config(config)
    print(f"LLM initialized: {config.openai_model}")
    
    # Test basic invocation
    try:
        response = llm.invoke("What is Grafana?")
        print(f"LLM response: {response.content[:100]}...")
    except Exception as e:
        logger.warning(f"Could not test LLM: {e}")
