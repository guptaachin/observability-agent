"""LangGraph visualization app for local development.

This module exports the compiled agent graph for the LangGraph CLI to discover and visualize.
Run with: langgraph watch
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from src.agent import create_agent

# Export the compiled graph for LangGraph CLI
graph = create_agent()

# Also export the create_agent function for dynamic reloading
__all__ = ["graph", "create_agent"]
