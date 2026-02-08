"""Gradio chat UI for Grafana Agent."""

import asyncio
import logging
import gradio as gr
from langchain_core.messages import HumanMessage

from src.config import load_config
from src.mcp_client import GrafanaMCP
from src.agent import create_agent


logging.basicConfig(level=logging.INFO)


def main():
    config = load_config()
    mcp = GrafanaMCP(config)
    agent = create_agent(config, mcp)
    
    def chat(message: str, history: list) -> str:
        result = asyncio.run(
            agent.ainvoke({"messages": [HumanMessage(content=message)]})
        )
        return result["messages"][-1].content
    
    gr.ChatInterface(
        fn=chat,
        title="Grafana Agent",
        description="Ask about your Grafana dashboards",
        examples=[
            "Show me all dashboards",
            "Find dashboards with prod in the name",
        ],
    ).launch()


if __name__ == "__main__":
    main()
