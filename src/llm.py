"""
LLM provider initialization for Grafana Agent.

Supports:
- OpenAI (cloud-based): gpt-4-turbo, gpt-3.5-turbo, etc.
- Ollama (local): llama2, mistral, neural-chat, etc.

Abstracts provider differences via LangChain's consistent interface.
"""

import logging
from typing import Union
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from src.config import AppConfig, LLMConfig


logger = logging.getLogger(__name__)


def create_llm(config: LLMConfig) -> Union[ChatOpenAI, ChatOllama]:
    """
    Create and initialize LLM based on configuration.

    Args:
        config: LLMConfig object with provider and credentials

    Returns:
        Initialized LLM instance (ChatOpenAI or ChatOllama)

    Raises:
        ValueError: If configuration is invalid or LLM cannot connect
    """
    if config.provider == "openai":
        logger.info(f"Initializing OpenAI LLM: {config.openai.model}")
        
        if not config.openai or not config.openai.api_key:
            raise ValueError("OpenAI API key not configured")
        
        return ChatOpenAI(
            model=config.openai.model,
            api_key=config.openai.api_key,
            temperature=0.0,  # Deterministic responses for dashboard retrieval
            max_tokens=1024,
        )
    
    elif config.provider == "ollama":
        logger.info(f"Initializing Ollama LLM: {config.ollama.model} at {config.ollama.base_url}")
        
        if not config.ollama:
            raise ValueError("Ollama configuration not found")
        
        return ChatOllama(
            model=config.ollama.model,
            base_url=config.ollama.base_url,
            temperature=0.0,  # Deterministic responses for dashboard retrieval
        )
    
    else:
        raise ValueError(f"Unsupported LLM provider: {config.provider}")


def create_llm_from_app_config(app_config: AppConfig) -> Union[ChatOpenAI, ChatOllama]:
    """
    Create LLM from complete app configuration.

    Convenience function that extracts LLM config from AppConfig.

    Args:
        app_config: Complete AppConfig object

    Returns:
        Initialized LLM instance
    """
    return create_llm(app_config.llm)


if __name__ == "__main__":
    # Test LLM initialization
    from src.config import load_config
    
    config = load_config()
    llm = create_llm_from_app_config(config)
    print(f"LLM initialized: {config.llm.provider}")
    
    # Test basic invocation
    try:
        response = llm.invoke("What is Grafana?")
        print(f"LLM response: {response.content[:100]}...")
    except Exception as e:
        logger.warning(f"Could not test LLM: {e}")
