"""
Single-node LangGraph agent for Grafana dashboard discovery.

This agent implements a simple query → LLM → response pattern:
1. Receives user query in natural language
2. Invokes LLM with system prompt constraining scope
3. LLM decides which tool to call (list_dashboards, search_dashboards)
4. Tool returns results
5. LLM formats response for user

The agent is a single-node graph (no branching, looping, or multi-hop reasoning).
"""

import logging
from typing import Union, Any, Dict
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from src.config import AppConfig
from src.tools import GrafanaMCPTool, GrafanaConnectionError, GrafanaDataError


logger = logging.getLogger(__name__)


# System prompt that constrains LLM behavior
SYSTEM_PROMPT = """You are an assistant that helps engineers retrieve information about Grafana dashboards.

YOUR CAPABILITIES:
- List all available dashboards in the organization
- Search/filter dashboards by name or tags
- Retrieve dashboard metadata (title, last updated, tags, folder)

YOUR CONSTRAINTS:
- You CANNOT analyze metrics, detect anomalies, or explain metric behavior
- You CANNOT make recommendations or provide predictions
- You CANNOT modify dashboards or create new ones
- You only retrieve and display data exactly as stored in Grafana
- You do not make inferences or add context beyond the data

RESPONSE FORMAT:
- Use plain text (no JSON, no markdown code blocks)
- Use bullet points or numbered lists for dashboard lists
- Be concise and clear
- If results are empty, say "No dashboards found"

USER QUERY:
{query}

TASK:
1. Understand what the user is asking
2. Determine if the request is within your capabilities
3. If YES: Describe what dashboards you would retrieve and format them clearly
4. If NO: Explain what you can do instead

Return ONLY the response for the user (no reasoning, no markdown formatting)."""


class AgentState(dict):
    """State dictionary for LangGraph agent."""

    def __init__(self):
        super().__init__(
            query="",  # User's natural language query
            intent="",  # Parsed intent: list, filter, get_info, invalid, out_of_scope
            response="",  # Formatted response for user
            status="pending",  # pending, success, error, out_of_scope
            error_code=None,  # Machine-readable error identifier
            data=None,  # Retrieved dashboard data
        )


async def agent_node(
    state: Dict[str, Any],
    llm: Union[ChatOpenAI, ChatOllama],
    grafana_tool: GrafanaMCPTool,
    timeout: int = 30,
) -> Dict[str, Any]:
    """
    Single-node agent that processes queries.

    Args:
        state: Agent state dictionary with 'query' field
        llm: Initialized LLM instance
        grafana_tool: GrafanaMCPTool instance
        timeout: Query timeout in seconds

    Returns:
        Updated state with 'response', 'status', and optional 'data' fields
    """
    query = state.get("query", "").strip()

    # Validate input
    if not query:
        logger.warning("Empty query received")
        return {
            **state,
            "response": "Please provide a query about dashboards (e.g., 'Show me all dashboards').",
            "status": "invalid",
            "error_code": "empty_query",
        }

    logger.info(f"Processing query: {query}")

    try:
        # Invoke LLM to interpret query and decide action
        messages = [
            SystemMessage(content=SYSTEM_PROMPT.format(query=query)),
            HumanMessage(content=query),
        ]

        llm_response = await llm.ainvoke(messages)
        response_text = llm_response.content

        # Check if response indicates out-of-scope request
        if _is_out_of_scope(response_text, query):
            logger.info(f"Out-of-scope request: {query}")
            return {
                **state,
                "response": response_text,
                "status": "out_of_scope",
                "error_code": "out_of_scope",
                "intent": "out_of_scope",
            }

        # Determine intent and fetch data
        intent = _extract_intent(query)
        logger.info(f"Extracted intent: {intent}")

        try:
            if intent == "list" or intent == "unknown":
                # Default to listing all dashboards
                dashboards = await grafana_tool.list_dashboards()
                
                if not dashboards:
                    formatted_response = "No dashboards found in Grafana."
                else:
                    formatted_response = _format_dashboard_list(dashboards)
                
                return {
                    **state,
                    "response": formatted_response,
                    "status": "success",
                    "intent": intent,
                    "data": [d.to_dict() for d in dashboards],
                }

            elif intent == "filter":
                # Extract filter term from query
                filter_term = _extract_filter_term(query)
                dashboards = await grafana_tool.search_dashboards(filter_term)
                
                if not dashboards:
                    formatted_response = f"No dashboards match your criteria: '{filter_term}'"
                else:
                    formatted_response = _format_dashboard_list(dashboards)
                
                return {
                    **state,
                    "response": formatted_response,
                    "status": "success",
                    "intent": intent,
                    "data": [d.to_dict() for d in dashboards],
                }

            else:
                # Unknown intent, provide guidance
                return {
                    **state,
                    "response": "I didn't understand your request. Please ask about dashboards, e.g., 'Show me all dashboards' or 'List dashboards with prod in the name'.",
                    "status": "invalid",
                    "intent": "unknown",
                    "error_code": "invalid_query",
                }

        except GrafanaConnectionError as e:
            logger.error(f"Grafana connection error: {e}")
            return {
                **state,
                "response": "Unable to connect to Grafana. Please check your configuration and ensure the MCP server is running.",
                "status": "error",
                "error_code": "grafana_connection_error",
                "intent": intent,
            }

        except GrafanaDataError as e:
            logger.error(f"Grafana data error: {e}")
            return {
                **state,
                "response": "Grafana returned incomplete data. Please try again or contact your administrator.",
                "status": "error",
                "error_code": "grafana_data_error",
                "intent": intent,
            }

    except asyncio.TimeoutError:
        logger.error("Query timeout")
        return {
            **state,
            "response": "Query took too long to process. Please try again.",
            "status": "error",
            "error_code": "timeout",
        }

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            **state,
            "response": f"An unexpected error occurred. Please try again.",
            "status": "error",
            "error_code": "internal_error",
        }


def _is_out_of_scope(response: str, query: str) -> bool:
    """
    Detect if LLM response indicates out-of-scope request.

    Args:
        response: LLM response text
        query: Original user query

    Returns:
        True if request is out of scope
    """
    out_of_scope_keywords = [
        "cannot",
        "can't",
        "not able to",
        "not able",
        "out of scope",
        "i cannot",
        "i can't",
    ]

    response_lower = response.lower()
    return any(keyword in response_lower for keyword in out_of_scope_keywords)


def _extract_intent(query: str) -> str:
    """
    Extract user intent from query.

    Args:
        query: User query string

    Returns:
        Intent: "list", "filter", "get_info", "unknown"
    """
    query_lower = query.lower()

    # List intent keywords
    if any(
        keyword in query_lower
        for keyword in ["show all", "list", "give me", "what dashboards", "all dashboards"]
    ):
        return "list"

    # Filter intent keywords
    if any(
        keyword in query_lower
        for keyword in ["with", "where", "filter", "search", "matching", "related"]
    ):
        return "filter"

    # Get info intent keywords (must be about dashboards/metrics)
    has_dashboard_context = any(
        term in query_lower
        for term in ["dashboard", "updated", "last", "created", "database", "service", "api", "performance", "health"]
    )
    has_info_keyword = any(
        keyword in query_lower
        for keyword in ["when", "what", "tell me", "info", "about", "time", "update"]
    )
    if has_dashboard_context and has_info_keyword:
        return "get_info"

    return "unknown"


def _extract_filter_term(query: str) -> str:
    """
    Extract filter term from filter query.

    Args:
        query: User query containing filter term

    Returns:
        Filter term (substring to search for)
    """
    # Simple extraction: look for quoted strings or common patterns
    if "'" in query:
        parts = query.split("'")
        if len(parts) >= 2:
            return parts[1]
    
    if '"' in query:
        parts = query.split('"')
        if len(parts) >= 2:
            return parts[1]

    # Look for "dashboards with X in the name"
    if "with" in query.lower():
        parts = query.lower().split("with", 1)
        if len(parts) > 1:
            term = parts[1].strip()
            # Remove common suffixes
            term = term.replace(" in the name", "").replace(" in name", "").strip()
            return term

    # Default to last word or phrase
    words = query.split()
    if len(words) > 2:
        return " ".join(words[-2:]).strip("'\"")

    return query.strip()


def _format_dashboard_list(dashboards: list) -> str:
    """
    Format list of dashboards for user display.

    Args:
        dashboards: List of DashboardMetadata objects

    Returns:
        Formatted text response
    """
    if not dashboards:
        return "No dashboards found."

    lines = [f"Found {len(dashboards)} dashboard(s):\n"]

    for i, dashboard in enumerate(dashboards, 1):
        lines.append(f"{i}. {dashboard.title}")
        if dashboard.folder_title:
            lines.append(f"   Folder: {dashboard.folder_title}")
        lines.append(f"   Last updated: {dashboard.updated}")
        if dashboard.tags:
            lines.append(f"   Tags: {', '.join(dashboard.tags)}")
        lines.append("")

    return "\n".join(lines).strip()


async def create_agent(
    config: AppConfig,
    llm: Union[ChatOpenAI, ChatOllama],
    grafana_tool: GrafanaMCPTool,
) -> Any:
    """
    Create and compile single-node LangGraph agent.

    Args:
        config: AppConfig with agent configuration
        llm: Initialized LLM instance
        grafana_tool: Initialized GrafanaMCPTool instance

    Returns:
        Compiled LangGraph graph ready for invocation
    """
    # Create graph
    graph = StateGraph(dict)

    # Define the single agent node
    async def agent_wrapper(state):
        return await agent_node(
            state,
            llm=llm,
            grafana_tool=grafana_tool,
            timeout=config.agent.timeout,
        )

    graph.add_node("agent", agent_wrapper)
    graph.add_edge(START, "agent")
    graph.add_edge("agent", END)

    # Compile and return
    compiled_graph = graph.compile()
    logger.info("Agent graph compiled successfully")
    return compiled_graph


# For backwards compatibility with sync code
import asyncio


def agent_invoke(state: Dict[str, Any], agent) -> Dict[str, Any]:
    """
    Synchronously invoke agent (wrapper for async agent).

    Args:
        state: Agent state
        agent: Compiled graph

    Returns:
        Updated state with response
    """
    return asyncio.run(agent.ainvoke(state))
