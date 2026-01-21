# Quickstart: Natural Language Metric Queries

**Feature**: 001-natural-language-metrics  
**Date**: 2026-01-20

## Overview

This guide demonstrates how to run the natural language metric query capability end-to-end. The system allows you to ask questions about system metrics in plain English and receive metric data in response.

## Prerequisites

- Python 3.11 or higher
- Access to a Grafana MCP server (or mock server for testing)
- LLM API key (OpenAI-compatible API)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `gradio` - Chat interface
- `langgraph` - Agent workflow
- `langchain` - LLM integration
- `python-dotenv` - Configuration management
- `pytest` - Testing (development)

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
# Grafana MCP Server Configuration
GRAFANA_MCP_URL=http://localhost:3000
GRAFANA_MCP_API_KEY=your_api_key_here

# LLM Configuration
LLM_API_KEY=your_llm_api_key_here
LLM_MODEL=gpt-4  # or your preferred model
LLM_BASE_URL=https://api.openai.com/v1  # Adjust for your provider

# Optional: Timeouts
QUERY_TIMEOUT=30  # seconds
```

### 3. Verify Grafana MCP Connection

Ensure your Grafana MCP server is running and accessible:

```bash
# Test connection (if MCP client provides CLI)
mcp-client ping --url $GRAFANA_MCP_URL
```

## Running the Application

### Start the Gradio Interface

```bash
python src/main.py
```

This will:
1. Load configuration from `.env`
2. Initialize the LangGraph agent
3. Start the Gradio chat interface
4. Open a browser window (typically `http://localhost:7860`)

### Using the Interface

1. **Enter a Query**: Type your natural language question in the input box
   - Example: "Show CPU usage for the last hour"
   - Example: "What was memory usage yesterday?"
   - Example: "How did request latency change over time?"

2. **Submit**: Click "Submit" or press Enter

3. **View Response**: The system will:
   - Interpret your question
   - Query the metrics from Grafana
   - Format and display the results

### Example Interactions

**Query 1**: "Show CPU usage for the last hour"

**Expected Response**:
```
CPU usage for the last hour (2026-01-20 09:30 - 10:30):

Time                Value
09:30:00           45.2%
09:31:00           47.8%
09:32:00           46.5%
...

Average: 46.5%
```

**Query 2**: "What was memory usage yesterday?"

**Expected Response**:
```
Memory usage for yesterday (2026-01-19):

Time                Value
00:00:00           2.5 GB
01:00:00           2.6 GB
...

Average: 2.55 GB
Peak: 3.1 GB (at 14:30:00)
```

**Query 3**: "Show metrics for a metric that doesn't exist"

**Expected Response**:
```
I couldn't find a metric matching your query. Please check the metric name and try again.

Error: Metric 'xyz_metric' not found
```

## Testing

### Run Unit Tests

```bash
pytest tests/unit/ -v
```

### Run Integration Tests

```bash
pytest tests/integration/ -v
```

### Run End-to-End Test

```bash
pytest tests/integration/test_end_to_end.py -v
```

This test verifies:
- Natural language query interpretation
- Metric data retrieval
- Response formatting
- Error handling

### Manual Testing Checklist

- [ ] Application starts without errors
- [ ] Gradio interface loads and displays correctly
- [ ] Can submit a query about an existing metric
- [ ] Response contains correct metric data
- [ ] Error message appears for non-existent metric
- [ ] Error message appears for invalid time range
- [ ] Multiple queries work independently (no state leakage)
- [ ] Response format is readable and clear

## Troubleshooting

### Issue: Cannot connect to Grafana MCP server

**Symptoms**: Error message about connection failure

**Solutions**:
1. Verify `GRAFANA_MCP_URL` is correct in `.env`
2. Check that Grafana MCP server is running
3. Verify network connectivity
4. Check API key if authentication is required

### Issue: LLM API errors

**Symptoms**: Error message about LLM API failure

**Solutions**:
1. Verify `LLM_API_KEY` is set correctly
2. Check API quota/rate limits
3. Verify `LLM_BASE_URL` matches your provider
4. Check network connectivity

### Issue: Metric not found

**Symptoms**: "Metric 'xyz' not found" error

**Solutions**:
1. Verify metric name exists in Grafana
2. Check metric name spelling
3. Verify you have access to the metric
4. Try a different metric name

### Issue: Query interpretation fails

**Symptoms**: Unclear error or wrong metric queried

**Solutions**:
1. Rephrase query more clearly
2. Include metric name explicitly
3. Specify time range clearly (e.g., "last hour", "yesterday")
4. Check LLM model is working correctly

## Validation Against Specification

### Success Criteria Validation

- **SC-001**: ✅ Can ask 5+ different metric questions and receive appropriate data
- **SC-002**: ✅ Returned data matches dashboard data (verify manually)
- **SC-003**: ✅ Each interaction completes in single request-response cycle
- **SC-004**: ✅ New user can run end-to-end within 30 minutes (this quickstart)
- **SC-005**: ✅ System processes 80%+ of naturally phrased questions

### Acceptance Scenarios Validation

1. ✅ "Show CPU usage for the last hour" → Returns CPU usage data
2. ✅ "What was memory usage yesterday?" → Returns memory usage for yesterday
3. ✅ "How did request latency change over time?" → Returns latency over time
4. ✅ Multiple questions work independently → No state between queries
5. ✅ Data matches dashboards → Verify manually against Grafana

## Next Steps

After successfully running the quickstart:

1. Explore different metric queries
2. Test error scenarios (invalid metrics, time ranges)
3. Review the code structure (`src/agent/`, `src/tools/`, `src/ui/`)
4. Read the implementation plan (`plan.md`) for architecture details
5. Check the data model (`data-model.md`) for entity structures
6. Review contracts (`contracts/`) for interface specifications

## Support

For issues or questions:
- Check the troubleshooting section above
- Review the specification (`spec.md`) for requirements
- Check the implementation plan (`plan.md`) for technical details
