"""
Gradio chat interface for Grafana Agent.

Provides a lightweight, local chat UI for interacting with the agent.
Stateless (no conversation persistence between sessions).
"""

import logging
import asyncio
from typing import Any, Generator
import gradio as gr
from src.config import load_config, setup_logging
from src.llm import create_llm_from_app_config
from src.tools import create_grafana_tool
from src.agent import create_agent


logger = logging.getLogger(__name__)


class GrafanaAgentUI:
    """Wrapper for Gradio chat interface."""

    def __init__(self, config_file: str = None):
        """
        Initialize agent UI.

        Args:
            config_file: Optional path to config YAML file
        """
        # Load configuration
        self.config = load_config(config_file)
        setup_logging(self.config)

        logger.info("Initializing Grafana Agent UI...")

        # Initialize components
        self.llm = None
        self.grafana_tool = None
        self.agent = None
        self._init_components()

    def _init_components(self) -> None:
        """Initialize LLM, tools, and agent."""
        try:
            # Create LLM
            self.llm = create_llm_from_app_config(self.config)
            logger.info(f"LLM initialized: {self.config.llm.provider}")

            # Create Grafana tool (sync wrapper)
            self.grafana_tool = asyncio.run(
                create_grafana_tool(self.config.grafana)
            )
            logger.info("Grafana tool initialized")

            # Create agent
            self.agent = asyncio.run(
                create_agent(self.config, self.llm, self.grafana_tool)
            )
            logger.info("Agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise

    def process_message(self, message: str, history: list) -> str:
        """
        Process user message and return agent response.

        Args:
            message: User query
            history: Chat history (unused in stateless implementation)

        Returns:
            Agent response text
        """
        logger.info(f"Processing query: {message[:100]}...")

        try:
            # Invoke agent
            state = {"query": message}
            result = asyncio.run(self.agent.ainvoke(state))

            response = result.get("response", "No response generated")
            status = result.get("status", "unknown")

            logger.info(f"Agent response status: {status}")
            return response

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"An error occurred: {str(e)}"

    def launch(self, share: bool = False, server_name: str = "localhost", server_port: int = 7860):
        """
        Launch Gradio chat interface.

        Args:
            share: Whether to create public link
            server_name: Server hostname
            server_port: Server port
        """
        logger.info(f"Launching Gradio interface at {server_name}:{server_port}")

        # Create interface
        interface = gr.ChatInterface(
            fn=self.process_message,
            title="Grafana Agent",
            description="Ask me about your Grafana dashboards",
            examples=[
                "Show me all dashboards",
                "List dashboards with prod in the name",
                "When was the API dashboard last updated?",
                "What dashboards are available?",
            ],
        )

        # Launch
        interface.launch(
            share=share,
            server_name=server_name,
            server_port=server_port,
            show_error=True,
        )


def main(config_file: str = None):
    """
    Main entry point for Gradio UI.

    Args:
        config_file: Optional path to config YAML file
    """
    ui = GrafanaAgentUI(config_file)
    ui.launch()


if __name__ == "__main__":
    main()
