"""Simple LangGraph agent for Grafana dashboard queries."""

import asyncio
import logging
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, SystemMessage

from config import Config, create_llm
from mcp_client import GrafanaMCP, Dashboard


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a Grafana dashboard assistant. You can ONLY:
- List all dashboards
- Search dashboards by name/tag/topic

You CANNOT analyze metrics, make predictions, or modify dashboards.

When the user asks about dashboards, extract search keywords.
Think about what dashboard NAMES might match the user's intent:
- "system health" -> node, exporter, system, health, cpu, memory
- "API monitoring" -> api, service, http, request
- "database" -> db, postgres, mysql, redis, database

Respond with ONE of these formats:

1. For searching (provide multiple keywords separated by |):
SEARCH: keyword1|keyword2|keyword3

2. For listing all:
SEARCH:

3. For out-of-scope requests:
OUT_OF_SCOPE: <brief explanation>

Examples:
- "Show me all dashboards" -> SEARCH:
- "Find dashboards with metrics" -> SEARCH: metrics
- "Is there a dashboard named node?" -> SEARCH: node
- "Do we have dashboards to check system health?" -> SEARCH: node|system|health|exporter|cpu|memory
- "Dashboards for API monitoring" -> SEARCH: api|service|http
- "What dashboards are available?" -> SEARCH:"""


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
            search_terms = response_text.split(":", 1)[1].strip()
        else:
            search_terms = ""
        
        # Query Grafana - try multiple keywords if provided
        try:
            all_dashboards = []
            seen_uids = set()
            
            if "|" in search_terms:
                # Multiple keywords - search each
                for term in search_terms.split("|"):
                    term = term.strip()
                    if term:
                        dashboards = await mcp.list_dashboards(term)
                        for d in dashboards:
                            if d.uid not in seen_uids:
                                all_dashboards.append(d)
                                seen_uids.add(d.uid)
            else:
                # Single term or empty (list all)
                all_dashboards = await mcp.list_dashboards(search_terms)
            
            response = format_dashboards(all_dashboards)
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
