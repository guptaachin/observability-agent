"""Simple LangGraph agent for Grafana dashboard queries."""

import asyncio
import logging
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, SystemMessage

from config import Config, create_llm
from tools import GrafanaMCP, Dashboard


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a Grafana dashboard assistant. You can ONLY:
- List all dashboards
- Search dashboards by name/tag/topic

You CANNOT analyze metrics, make predictions, or modify dashboards.

When the user asks about dashboards, extract the search term if any.
Respond in this exact format:
SEARCH: <term or empty if listing all>

Examples:
- "Show me all dashboards" -> SEARCH:
- "Find dashboards with metrics" -> SEARCH: metrics
- "Is there a dashboard named node?" -> SEARCH: node
- "Do we have dashboards to check system health?" -> SEARCH: system health
- "Dashboards for API monitoring" -> SEARCH: API monitoring
- "What dashboards are available?" -> SEARCH:

If the request is out of scope (analyzing metrics, predictions, etc), respond with:
OUT_OF_SCOPE: <brief explanation>"""


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
    """Create LangGraph agent."""
    llm = create_llm(config)
    
    async def agent_node(state: dict) -> dict:
        query = state.get("query", "")
        
        if not query.strip():
            return {**state, "response": "Please provide a query about dashboards."}
        
        # Let LLM extract search intent
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=query),
        ]
        llm_response = await llm.ainvoke(messages)
        response_text = llm_response.content.strip()
        
        # Parse LLM response
        if response_text.startswith("OUT_OF_SCOPE:"):
            return {**state, "response": "I can only list or search dashboards. " + response_text.split(":", 1)[1].strip()}
        
        if response_text.startswith("SEARCH:"):
            search_term = response_text.split(":", 1)[1].strip()
        else:
            # Fallback: treat whole response as search term or empty
            search_term = ""
        
        # Query Grafana
        try:
            dashboards = await mcp.list_dashboards(search_term)
            response = format_dashboards(dashboards)
            return {**state, "response": response}
        except Exception as e:
            logger.error(f"Error: {e}")
            return {**state, "response": f"Error connecting to Grafana: {e}"}
    
    graph = StateGraph(dict)
    graph.add_node("agent", agent_node)
    graph.add_edge(START, "agent")
    graph.add_edge("agent", END)
    
    return graph.compile()


# Entry point for langgraph dev
async def build_agent():
    """Build agent for LangGraph CLI."""
    from src.config import load_config
    config = load_config()
    mcp = GrafanaMCP(config)
    return create_agent(config, mcp)


if __name__ == "__main__":
    from src.config import load_config
    
    async def test():
        config = load_config()
        mcp = GrafanaMCP(config)
        agent = create_agent(config, mcp)
        
        queries = [
            "Show me all dashboards",
            "Find dashboards with 'metrics' in the name",
            "Analyze my CPU usage trends",
        ]
        
        for q in queries:
            print(f"\nQ: {q}")
            result = await agent.ainvoke({"query": q})
            print(f"A: {result['response'][:200]}...")
    
    asyncio.run(test())
