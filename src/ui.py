"""Gradio UI for natural language metrics querying.

Provides a chat interface for users to ask natural language questions
about system metrics and receive formatted responses with statistics
and data points.
"""

from typing import List, Tuple

import gradio as gr

from src.agent import create_agent, MetricsQueryState
from src.models import QueryError


def answer_question(message: str, history: List[Tuple[str, str]]) -> str:
    """
    Answer a natural language question about metrics.
    
    Initializes the agent and processes the user's question through the
    parse → execute → format workflow, returning the formatted response.
    
    Args:
        message: User's natural language question
        history: Chat history (list of [user_message, assistant_response] pairs)
        
    Returns:
        Response text with metrics or error message
    """
    try:
        # Create the agent
        agent = create_agent()
        
        # Initialize state
        initial_state = {
            "user_question": message,
            "parsed_query": None,
            "query_result": None,
            "error": None,
            "final_response": ""
        }
        
        # Run the agent
        result = agent.invoke(initial_state)
        
        # Return the final response
        response = result.get("final_response", "No response generated")
        return response
        
    except Exception as e:
        # Handle unexpected errors
        error_msg = f"❌ Error: System Error\n\nMessage:\nUnexpected error: {str(e)}\n\n💡 Suggestion:\nPlease try again or rephrase your question."
        return error_msg


def create_interface() -> gr.ChatInterface:
    """
    Create and configure the Gradio chat interface.
    
    Returns:
        Configured ChatInterface ready for launch
    """
    interface = gr.ChatInterface(
        fn=answer_question,
        examples=[
            "Show CPU usage for the last hour",
            "Memory utilization in the last 24 hours",
            "Average request latency today"
        ],
        title="Natural Language Metrics Query",
        description="Ask about system metrics in plain English. The agent will fetch and format the results for you."
    )
    
    return interface
