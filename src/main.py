"""Main entry point for the Natural Language Metrics Query application.

Loads configuration, initializes the Gradio UI, and launches the web server.
"""

import sys
import os

# Load environment variables (including LangSmith config)
from dotenv import load_dotenv
load_dotenv()

from src.config import get_config
from src.ui import create_interface


def main():
    """
    Main entry point: Load config, create UI, and launch server.
    
    Loads configuration from environment variables, creates the Gradio
    chat interface, and launches the web server on the configured port.
    """
    try:
        # Load configuration
        config = get_config()
        
        print("=" * 60)
        print("Natural Language Metrics Query Agent")
        print("=" * 60)
        print(f"Configuration loaded successfully")
        print(f"  LLM Source: {config.llm_source}")
        print(f"  MCP Grafana: {config.mcp_grafana_host}:{config.mcp_grafana_port}")
        print(f"  Gradio Port: {config.gradio_server_port}")
        print("=" * 60)
        
        # Create the interface
        print("Initializing Gradio interface...")
        interface = create_interface()
        
        # Launch the server
        print(f"Launching server on http://0.0.0.0:{config.gradio_server_port}")
        print("=" * 60)
        
        interface.launch(
            server_name="0.0.0.0",
            server_port=config.gradio_server_port,
            share=False
        )
        
    except ValueError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutdown requested.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
