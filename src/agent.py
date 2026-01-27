"""Simple LangGraph agent for Grafana dashboard queries."""

import asyncio
import logging
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import Config, create_llm
from src.tools import GrafanaMCP, Dashboard


logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a Grafana dashboard assistant. You can ONLY:
- List dashboards
- Search dashboards by name/tag

You CANNOT analyze metrics, make predictions, or modify dashboards.
Be concise. Use plain text, no markdown."""


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


async def process_query(query: str, mcp: GrafanaMCP) -> str:
    """Process a dashboard query."""
    if not query.strip():
        return "Please ask about dashboards."
    
    q = query.lower()
    
    # Simple intent detection
    if any(w in q for w in ["search", "filter", "with", "find", "matching"]):
        # Extract search term (after "with", in quotes, or last word)
        term = ""
        if "'" in query:
            term = query.split("'")[1]
        elif '"' in query:
            term = query.split('"')[1]
        elif "with" in q:
            term = q.split("with", 1)[1].replace("in the name", "").strip()
        else:
            term = query.split()[-1]
        
        dashboards = await mcp.list_dashboards(term)
    else:
        dashboards = await mcp.list_dashboards()
    
    return format_dashboards(dashboards)


def create_agent(config: Config, mcp: GrafanaMCP):
    """Create LangGraph agent."""
    llm = create_llm(config)
    
    async def agent_node(state: dict) -> dict:
        query = state.get("query", "")
        
        if not query.strip():
            return {**state, "response": "Please provide a query about dashboards."}
        
        # Check with LLM if request is in scope
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Is this request in scope? Answer YES or NO, then respond appropriately: {query}"),
        ]
        llm_response = await llm.ainvoke(messages)
        
        if "cannot" in llm_response.content.lower() or "no" in llm_response.content.lower()[:10]:
            return {**state, "response": "I can only list or search dashboards. I cannot analyze metrics or make predictions."}
        
        # Process the query
        try:
            response = await process_query(query, mcp)
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
