"""
Integration tests for agent query processing.

Tests user story 1: List All Dashboards
Tests user story 2a: Filter dashboards
Tests user story 2b: Error handling
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

from src.agent import (
    create_agent,
    agent_node,
    _extract_intent,
    _extract_filter_term,
    _is_out_of_scope,
    _format_dashboard_list,
)
from src.tools import DashboardMetadata
from src.config import AppConfig, GrafanaConfig, LLMConfig, AgentConfig


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_dashboards():
    """Sample dashboards for testing."""
    now = datetime.now()
    return [
        DashboardMetadata(
            id=1,
            uid="prod-api",
            title="Prod API Dashboard",
            updated=now - timedelta(hours=2),
            folder_title="Production",
            tags=["production", "api"],
            org_id=1,
            starred=True,
        ),
        DashboardMetadata(
            id=2,
            uid="db-perf",
            title="Database Performance",
            updated=now - timedelta(days=1),
            folder_title="Infrastructure",
            tags=["database", "performance"],
            org_id=1,
            starred=False,
        ),
        DashboardMetadata(
            id=3,
            uid="service-health",
            title="Service Health",
            updated=now - timedelta(hours=24),
            folder_title="Monitoring",
            tags=["services", "health"],
            org_id=1,
            starred=True,
        ),
    ]


@pytest.fixture
def empty_dashboards():
    """Empty dashboard list for testing."""
    return []


@pytest.fixture
def mock_grafana_tool_instance(sample_dashboards):
    """Mock Grafana tool."""
    tool = AsyncMock()
    tool.list_dashboards = AsyncMock(return_value=sample_dashboards)
    tool.search_dashboards = AsyncMock(return_value=sample_dashboards[:1])  # Return only first
    tool.get_dashboard = AsyncMock(return_value=sample_dashboards[0])
    return tool


@pytest.fixture
def mock_llm_instance():
    """Mock LLM."""
    llm = AsyncMock()
    
    # Default response for "show all dashboards"
    response = MagicMock()
    response.content = "Here are all available dashboards in the system."
    llm.ainvoke = AsyncMock(return_value=response)
    
    return llm


@pytest.fixture
def test_agent_config():
    """Test agent configuration."""
    return AppConfig(
        grafana=GrafanaConfig(
            url="http://localhost:3000",
            username="admin",
            password="admin",
            org_id=1,
        ),
        llm=LLMConfig(provider="openai"),
        agent=AgentConfig(timeout=30, max_results=100),
    )


# ============================================================================
# Test Intent Extraction (US1 - List, US2a - Filter)
# ============================================================================


class TestIntentExtraction:
    """Tests for query intent detection."""

    def test_extract_intent_list_all(self):
        """Test intent extraction for 'show all dashboards'."""
        queries = [
            "show me all dashboards",
            "list all dashboards",
            "what dashboards are available",
            "show all dashboards",
        ]
        for query in queries:
            assert _extract_intent(query) == "list", f"Failed for query: {query}"

    def test_extract_intent_filter(self):
        """Test intent extraction for filtering queries."""
        queries = [
            "show dashboards with prod in the name",
            "dashboards with database",
            "filter dashboards with api",
        ]
        for query in queries:
            assert _extract_intent(query) == "filter", f"Failed for query: {query}"

    def test_extract_intent_get_info(self):
        """Test intent extraction for info queries."""
        queries = [
            "when was the prod api dashboard updated",
            "when is the service health dashboard updated",
            "last update time for database performance",
        ]
        for query in queries:
            assert _extract_intent(query) == "get_info", f"Failed for query: {query}"

    def test_extract_intent_unknown(self):
        """Test intent extraction for unknown queries."""
        queries = [
            "what is the meaning of life",
            "tell me a joke",
            "explain machine learning",
        ]
        for query in queries:
            assert _extract_intent(query) == "unknown", f"Failed for query: {query}"


# ============================================================================
# Test Filter Term Extraction (US2a - Filter)
# ============================================================================


class TestFilterTermExtraction:
    """Tests for extracting filter terms from queries."""

    def test_extract_filter_term_quoted(self):
        """Test extraction with quoted filter term."""
        query = 'show dashboards with "prod api" in the name'
        term = _extract_filter_term(query)
        assert term == "prod api"

    def test_extract_filter_term_unquoted(self):
        """Test extraction with unquoted filter term."""
        query = "show dashboards with prod in the name"
        term = _extract_filter_term(query)
        assert "prod" in term.lower()

    def test_extract_filter_term_simple(self):
        """Test extraction from simple filter query."""
        query = "dashboards with database"
        term = _extract_filter_term(query)
        assert "database" in term.lower()


# ============================================================================
# Test Out-of-Scope Detection (US2b - Error Handling)
# ============================================================================


class TestOutOfScopeDetection:
    """Tests for detecting out-of-scope requests."""

    def test_out_of_scope_cannot(self):
        """Test detection of 'cannot' in response."""
        responses = [
            "I cannot analyze dashboards for anomalies",
            "I can't recommend dashboard changes",
            "Cannot detect issues in your data",
        ]
        for response in responses:
            assert _is_out_of_scope(response, "any query")

    def test_not_out_of_scope(self):
        """Test that valid responses are not marked as out-of-scope."""
        responses = [
            "Here are all available dashboards",
            "The following dashboards match your criteria",
            "Dashboard was updated 2 hours ago",
        ]
        for response in responses:
            assert not _is_out_of_scope(response, "any query")


# ============================================================================
# Test Response Formatting (US1 - List)
# ============================================================================


class TestResponseFormatting:
    """Tests for dashboard list formatting."""

    def test_format_dashboard_list(self, sample_dashboards):
        """Test dashboard list formatting."""
        formatted = _format_dashboard_list(sample_dashboards)
        
        # Check that formatting includes key information
        assert "Prod API Dashboard" in formatted
        assert "Database Performance" in formatted
        assert "Service Health" in formatted
        assert "Production" in formatted
        assert "Infrastructure" in formatted
        assert "Monitoring" in formatted

    def test_format_empty_dashboard_list(self, empty_dashboards):
        """Test formatting empty dashboard list."""
        formatted = _format_dashboard_list(empty_dashboards)
        assert isinstance(formatted, str)
        assert len(formatted) > 0  # Should have some message


# ============================================================================
# Test Agent Node Processing (US1 + US2 Integration)
# ============================================================================


class TestAgentNodeProcessing:
    """Tests for agent node processing logic."""

    @pytest.mark.asyncio
    async def test_agent_process_list_all_dashboards(
        self, mock_llm_instance, mock_grafana_tool_instance
    ):
        """Test agent processing for 'list all dashboards' query (US1)."""
        state = {"query": "show me all dashboards"}
        
        result = await agent_node(
            state,
            llm=mock_llm_instance,
            grafana_tool=mock_grafana_tool_instance,
            timeout=30,
        )
        
        # Verify result structure
        assert "response" in result
        assert "status" in result
        assert result["status"] in ["success", "out_of_scope", "invalid", "error"]
        
        # Should have called list_dashboards
        mock_grafana_tool_instance.list_dashboards.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_process_filter_dashboards(
        self, mock_llm_instance, mock_grafana_tool_instance
    ):
        """Test agent processing for filter query (US2a)."""
        # Mock LLM to recognize filter intent
        response = MagicMock()
        response.content = "Here are dashboards matching your filter"
        mock_llm_instance.ainvoke = AsyncMock(return_value=response)
        
        state = {"query": "show dashboards with prod in the name"}
        
        result = await agent_node(
            state,
            llm=mock_llm_instance,
            grafana_tool=mock_grafana_tool_instance,
            timeout=30,
        )
        
        # Verify result
        assert "response" in result
        assert "status" in result

    @pytest.mark.asyncio
    async def test_agent_process_empty_query(
        self, mock_llm_instance, mock_grafana_tool_instance
    ):
        """Test agent handling of empty query."""
        state = {"query": ""}
        
        result = await agent_node(
            state,
            llm=mock_llm_instance,
            grafana_tool=mock_grafana_tool_instance,
            timeout=30,
        )
        
        # Should reject empty query
        assert result["status"] == "invalid"
        assert "Please provide a query" in result["response"]

    @pytest.mark.asyncio
    async def test_agent_process_invalid_whitespace_query(
        self, mock_llm_instance, mock_grafana_tool_instance
    ):
        """Test agent handling of whitespace-only query."""
        state = {"query": "   \n\t   "}
        
        result = await agent_node(
            state,
            llm=mock_llm_instance,
            grafana_tool=mock_grafana_tool_instance,
            timeout=30,
        )
        
        # Should reject whitespace-only query
        assert result["status"] == "invalid"


# ============================================================================
# Test Complete Agent (US1 - MVP)
# ============================================================================


class TestCompleteAgent:
    """Tests for complete agent with graph compilation."""

    @pytest.mark.asyncio
    async def test_create_agent_graph(
        self, test_agent_config, mock_llm_instance, mock_grafana_tool_instance
    ):
        """Test creating compiled agent graph."""
        agent = await create_agent(
            test_agent_config, mock_llm_instance, mock_grafana_tool_instance
        )
        
        # Verify agent is created
        assert agent is not None
        assert hasattr(agent, "ainvoke")

    @pytest.mark.asyncio
    async def test_agent_end_to_end_list_all(
        self, test_agent_config, mock_llm_instance, mock_grafana_tool_instance
    ):
        """Test end-to-end agent for listing all dashboards (US1)."""
        agent = await create_agent(
            test_agent_config, mock_llm_instance, mock_grafana_tool_instance
        )
        
        result = await agent.ainvoke({"query": "show me all dashboards"})
        
        # Verify result
        assert "response" in result
        assert isinstance(result["response"], str)
        assert len(result["response"]) > 0

    @pytest.mark.asyncio
    async def test_agent_handles_missing_required_fields(
        self, test_agent_config, mock_llm_instance, mock_grafana_tool_instance
    ):
        """Test agent handles state without required fields."""
        agent = await create_agent(
            test_agent_config, mock_llm_instance, mock_grafana_tool_instance
        )
        
        # State without 'query' field
        result = await agent.ainvoke({})
        
        assert "response" in result


# ============================================================================
# Test Acceptance Scenarios (from specification)
# ============================================================================


class TestAcceptanceScenarios:
    """Tests for acceptance scenarios from spec."""

    @pytest.mark.asyncio
    async def test_scenario_list_all_dashboards_success(
        self, mock_llm_instance, mock_grafana_tool_instance, sample_dashboards
    ):
        """
        Acceptance Scenario S1.1: List All Dashboards
        Given: User queries "show me all dashboards"
        When: Agent receives the query
        Then: Agent returns numbered list with dashboard names and metadata
        """
        # Setup mock LLM to recognize list intent
        response = MagicMock()
        response.content = "Here are all available dashboards"
        mock_llm_instance.ainvoke = AsyncMock(return_value=response)
        
        state = {"query": "show me all dashboards"}
        
        result = await agent_node(
            state,
            llm=mock_llm_instance,
            grafana_tool=mock_grafana_tool_instance,
            timeout=30,
        )
        
        # Verify response includes dashboard information
        assert "response" in result
        assert "Prod API Dashboard" in result.get("response", "")

    @pytest.mark.asyncio
    async def test_scenario_empty_dashboard_list(
        self, mock_llm_instance, mock_grafana_tool_instance
    ):
        """
        Acceptance Scenario S1.2: Empty Dashboard List
        Given: User queries for dashboards, but none exist
        When: Agent receives the query
        Then: Agent returns clear message indicating no dashboards found
        """
        # Mock tool to return empty list
        mock_grafana_tool_instance.list_dashboards = AsyncMock(return_value=[])
        
        response = MagicMock()
        response.content = "No dashboards found"
        mock_llm_instance.ainvoke = AsyncMock(return_value=response)
        
        state = {"query": "show me all dashboards"}
        
        result = await agent_node(
            state,
            llm=mock_llm_instance,
            grafana_tool=mock_grafana_tool_instance,
            timeout=30,
        )
        
        # Verify response handles empty case
        assert "response" in result

    @pytest.mark.asyncio
    async def test_scenario_out_of_scope_request(
        self, mock_llm_instance, mock_grafana_tool_instance
    ):
        """
        Acceptance Scenario S2.1: Out-of-Scope Request
        Given: User requests analysis/anomaly detection
        When: Agent detects out-of-scope request
        Then: Agent returns error message explaining scope limitations
        """
        response = MagicMock()
        response.content = "I cannot perform anomaly detection or analysis"
        mock_llm_instance.ainvoke = AsyncMock(return_value=response)
        
        state = {"query": "analyze the trends in database performance"}
        
        result = await agent_node(
            state,
            llm=mock_llm_instance,
            grafana_tool=mock_grafana_tool_instance,
            timeout=30,
        )
        
        # Should detect as out-of-scope
        assert result["status"] == "out_of_scope"
