"""
LangGraph agent for natural language metrics querying.

Defines a single-node agent that parses natural language queries,
executes them against Grafana via MCP, and formats results for display.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional
from typing_extensions import TypedDict

from langgraph.graph import StateGraph
from langchain_core.prompts import PromptTemplate

from src.llm import get_llm
from src.models import MetricsQuery, MetricsQueryResult, QueryError, TimeRange
from src.tools import query_grafana_metrics


class MetricsQueryState(TypedDict):
    """
    Complete state for a metrics query in the agent workflow.
    
    Fields:
        user_question: Original natural language question from user
        parsed_query: Parsed MetricsQuery (populated by parse node)
        query_result: Result from Grafana (populated by execute node)
        error: Error if query failed (set in any node)
        final_response: Formatted response for user (populated by format node)
    """
    user_question: str
    parsed_query: Optional[MetricsQuery]
    query_result: Optional[MetricsQueryResult]
    error: Optional[QueryError]
    final_response: str


def parse_question_node(state: MetricsQueryState) -> Dict[str, Any]:
    """
    Parse natural language question into a MetricsQuery.
    
    Uses the LLM to extract metric_name and time_range from the user's
    natural language question. Handles JSON parsing and validation errors.
    
    Args:
        state: Current agent state with user_question populated
        
    Returns:
        Dict with parsed_query or error field updated
    """
    user_question = state["user_question"]
    
    try:
        llm = get_llm()
        
        # Create a prompt for parsing the user's question
        parse_prompt = PromptTemplate(
            input_variables=["question"],
            template="""Extract the metric name and time range from this question. 
            
Question: {question}

Respond with JSON only:
{{
  "metric_name": "the metric to query",
  "time_range": {{
    "relative": "last 24 hours" or similar, OR
    "start": "ISO datetime" and "end": "ISO datetime"
  }},
  "aggregation": "avg|max|min|sum" (optional, default: "avg")
}}"""
        )
        
        # Call LLM
        chain = parse_prompt | llm
        response = chain.invoke({"question": user_question})
        
        # Parse the response
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Extract JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON found in LLM response")
        
        json_str = response_text[json_start:json_end]
        parsed_data = json.loads(json_str)
        
        # Create MetricsQuery with basic time range (24h default)
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        start = now - timedelta(hours=24)
        
        # Check if time_range has relative or specific datetimes
        time_range_data = parsed_data.get("time_range", {})
        if "start" in time_range_data and "end" in time_range_data:
            # Parse ISO datetimes
            start = datetime.fromisoformat(time_range_data["start"].replace('Z', '+00:00'))
            end = datetime.fromisoformat(time_range_data["end"].replace('Z', '+00:00'))
        else:
            # Use relative (or default 24h)
            end = now
        
        time_range = TimeRange(start_time=start, end_time=end)
        
        parsed_query = MetricsQuery(
            metric_name=parsed_data.get("metric_name", ""),
            time_range=time_range,
            aggregation=parsed_data.get("aggregation", "avg"),
            filters={},
            confidence=0.8
        )
        
        return {"parsed_query": parsed_query, "error": None}
    except Exception as e:
        error = QueryError(
            error_type="parsing_error",
            message=f"Could not parse your question: {str(e)}",
            suggestion="Try phrasing as: 'Show [metric_name] for [time_period]'"
        )
        return {"parsed_query": None, "error": error}


def execute_query_node(state: MetricsQueryState) -> Dict[str, Any]:
    """
    Execute the parsed query against Grafana via MCP.
    
    Calls the query_grafana_metrics tool with the parsed query and handles
    errors from MCP server unavailability or invalid responses.
    
    Args:
        state: Current agent state with parsed_query populated
        
    Returns:
        Dict with query_result or error field updated
    """
    # If parse failed, skip execution
    if state.get("error"):
        return {"query_result": None}
    
    parsed_query = state["parsed_query"]
    if not parsed_query:
        return {
            "query_result": None,
            "error": QueryError(
                error_type="invalid_query",
                message="No parsed query available"
            )
        }
    
    try:
        # Call the Grafana metrics tool (async)
        import asyncio
        result = asyncio.run(query_grafana_metrics(parsed_query))
        
        # Check if result is an error
        if isinstance(result, QueryError):
            return {"query_result": None, "error": result}
        
        # Result is a MetricsQueryResult
        return {"query_result": result, "error": None}
    except Exception as e:
        error = QueryError(
            error_type="grafana_unavailable",
            message=f"Error querying Grafana: {str(e)}",
            suggestion="Check that Grafana and the MCP server are running"
        )
        return {"query_result": None, "error": error}


def format_response_node(state: MetricsQueryState) -> Dict[str, Any]:
    """
    Format the query result or error for display to the user.
    
    Produces a human-readable response from either the MetricsQueryResult
    or the QueryError. Uses the summary property for results.
    
    Args:
        state: Current agent state with query_result or error populated
        
    Returns:
        Dict with final_response field updated
    """
    if state.get("error"):
        error = state["error"]
        msg = f"Error: {error.message}"
        if error.suggestion:
            msg += f"\nSuggestion: {error.suggestion}"
        return {"final_response": msg}
    
    if state.get("query_result"):
        result = state["query_result"]
        return {"final_response": result.summary}
    
    return {"final_response": "No result or error available (unexpected state)"}


def create_agent():
    """
    Create and compile the LangGraph agent workflow.
    
    Returns a runnable graph that processes queries through:
    1. parse_question_node: NLP → MetricsQuery
    2. execute_query_node: MetricsQuery → MetricsQueryResult (or error)
    3. format_response_node: Result → human-readable string
    
    Returns:
        Compiled LangGraph StateGraph ready for invoke()
    """
    graph = StateGraph(MetricsQueryState)
    
    # Add nodes
    graph.add_node("parse", parse_question_node)
    graph.add_node("execute", execute_query_node)
    graph.add_node("format", format_response_node)
    
    # Define edges: parse → execute → format
    graph.add_edge("parse", "execute")
    graph.add_edge("execute", "format")
    
    # Set start and end
    graph.set_entry_point("parse")
    graph.set_finish_point("format")
    
    # Compile the graph
    return graph.compile()
