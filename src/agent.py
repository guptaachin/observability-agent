"""Simple LangGraph agent for Grafana dashboard queries."""

import asyncio
import logging
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

from src.config import Config, create_llm, load_config
from src.mcp_client import GrafanaMCP, Dashboard


logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State schema for the Grafana agent graph."""
    messages: Annotated[list, add_messages]


SYSTEM_PROMPT = """You are a Grafana dashboard assistant. You can ONLY:
- List all dashboards
- Search dashboards by name/tag/topic

You CANNOT analyze metrics, make predictions, or modify dashboards.

You have access to a tool called 'search_dashboards' that searches Grafana dashboards.
Use this tool to answer user queries about dashboards.

When searching:
- Use multiple keywords separated by | for better results
- Think about what dashboard NAMES might match the user's intent:
  * "system health" -> node|exporter|system|health|cpu|memory
  * "API monitoring" -> api|service|http|request
  * "database" -> db|postgres|mysql|redis|database
- Leave query empty to list all dashboards

For out-of-scope requests, politely explain you can only help with dashboard listing/searching."""


def format_dashboards(dashboards: list[Dashboard]) -> str:
    """Format dashboard list for display."""
    if not dashboards:
        return "No dashboards found."
    
    lines = [f"Found {len(dashboards)} dashboard(s):\n"]
    for i, d in enumerate(dashboards, 1):
        lines.append(f"{i}. {d.title}")
        if d.folder:
            lines.append(f"   Folder: {d.folder}")
        if d.tags:
            lines.append(f"   Tags: {', '.join(d.tags)}")
    return "\n".join(lines)


def create_agent(config: Config, mcp: GrafanaMCP):
    """Create LangGraph agent with MCP tool."""
    llm = create_llm(config)
    
    # Define the MCP tool
    @tool
    async def search_dashboards(query: str = "") -> str:
        """Search Grafana dashboards by keywords. Use multiple keywords separated by | for better results. Leave empty to list all dashboards.
        
        Args:
            query: Search terms separated by |, or empty string to list all
        
        Returns:
            Formatted list of matching dashboards
        """
        try:
            all_dashboards = []
            seen_uids = set()
            
            if "|" in query:
                # Multiple keywords - search each
                for term in query.split("|"):
                    term = term.strip()
                    if term:
                        dashboards = await mcp.list_dashboards(term)
                        for d in dashboards:
                            if d.uid not in seen_uids:
                                all_dashboards.append(d)
                                seen_uids.add(d.uid)
            else:
                # Single term or empty (list all)
                all_dashboards = await mcp.list_dashboards(query.strip())
            
            return format_dashboards(all_dashboards)
        except Exception as e:
            logger.error(f"Error searching dashboards: {e}")
            return f"Error connecting to Grafana: {e}"
    
    # Bind tool to LLM
    llm_with_tools = llm.bind_tools([search_dashboards])
    
    async def agent_node(state: dict) -> dict:
        """Agent decides whether to use tools."""
        messages = state.get("messages", [])
        
        # Add system prompt if this is the first message
        if len(messages) == 1:
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        
        response = await llm_with_tools.ainvoke(messages)
        return {**state, "messages": messages + [response]}
    
    async def tool_node(state: dict) -> dict:
        """Execute tool calls."""
        messages = state["messages"]
        last_message = messages[-1]
        
        tool_results = []
        for tool_call in last_message.tool_calls:
            if tool_call["name"] == "search_dashboards":
                result = await search_dashboards.ainvoke(tool_call["args"])
                tool_results.append(
                    ToolMessage(
                        content=result,
                        tool_call_id=tool_call["id"]
                    )
                )
        
        return {**state, "messages": messages + tool_results}
    
    def should_continue(state: dict) -> str:
        """Route to tools or end based on last message."""
        messages = state["messages"]
        last_message = messages[-1]
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END
    
    # Build graph
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    
    return graph.compile()

# Entry point for langgraph dev
def build_agent():
    """Build agent for LangGraph CLI."""
    config = load_config()
    mcp = GrafanaMCP(config)
    return create_agent(config, mcp)
