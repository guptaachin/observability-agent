"""
LLM factory utilities.

Provides `get_llm()` which returns a configured LLM instance based on
environment configuration. Supports OpenAI and Ollama backends.
"""

from typing import Any

from src.config import get_config


def get_llm() -> Any:
    """Return a configured LLM/chat model instance.

    Attempts to import the relevant LangChain model class and instantiate
    it with conservative defaults for deterministic parsing (low temperature).
    If the required LangChain model class is not available, raises ImportError
    with a helpful message.
    """
    cfg = get_config()

    if cfg.llm_source == "openai":
        try:
            from langchain.chat_models import ChatOpenAI

            return ChatOpenAI(model="gpt-4-turbo", temperature=0.3, openai_api_key=cfg.openai_api_key)
        except Exception as e:  # ImportError or runtime error
            raise ImportError(
                "ChatOpenAI is not available. Ensure 'langchain' is installed and up-to-date."
            ) from e

    if cfg.llm_source == "ollama":
        # Try a few possible import locations for Ollama support in LangChain
        try:
            from langchain.chat_models import Ollama

            return Ollama(base_url=cfg.ollama_base_url, temperature=0.3)
        except Exception:
            try:
                from langchain.llms import Ollama

                return Ollama(base_url=cfg.ollama_base_url, temperature=0.3)
            except Exception as e:
                raise ImportError(
                    "Ollama client is not available. Ensure 'langchain' with Ollama support is installed."
                ) from e

    raise RuntimeError(f"Unsupported llm_source: {cfg.llm_source}")
