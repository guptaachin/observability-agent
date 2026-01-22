"""Gradio UI for natural language metrics querying.

Provides a chat interface for users to ask natural language questions
about system metrics and receive formatted responses with statistics
and data points.
"""

from typing import Generator, List, Tuple
import asyncio

import gradio as gr

from src.agent import create_agent, MetricsQueryState
from src.models import QueryError


async def answer_question_async(message: str, history: List[Tuple[str, str]]) -> Generator[str, None, None]:
    """
    Answer a natural language question about metrics (async implementation).
    
    Initializes the agent and processes the user's question through the
    parse → execute → format workflow, yielding the response progressively.
    
    Args:
        message: User's natural language question
        history: Chat history (list of [user_message, assistant_response] pairs)
        
    Yields:
        Response text (single yield for MVP, can be extended for streaming)
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
        
        # Yield the final response
        response = result.get("final_response", "No response generated")
        yield response
        
    except Exception as e:
        # Handle unexpected errors
        error_msg = f"❌ Error: System Error\n\nMessage:\nUnexpected error: {str(e)}\n\n💡 Suggestion:\nPlease try again or rephrase your question."
        yield error_msg


def answer_question(message: str, history: List[Tuple[str, str]]) -> str:
    """
    Answer a natural language question about metrics (sync wrapper).
    
    This wrapper converts the async function to sync for use with Gradio.
    
    Args:
        message: User's natural language question
        history: Chat history
        
    Returns:
        Response text
    """
    # Create event loop and run async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # Convert async generator to sync by consuming all yields
        async_gen = answer_question_async(message, history)
        result = ""
        async def run_gen():
            nonlocal result
            async for chunk in async_gen:
                result = chunk
        loop.run_until_complete(run_gen())
        return result
    finally:
        loop.close()


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
        description="Ask about system metrics in plain English. The agent will fetch and format the results for you.",
        type="messages"
    )
    
    return interface
