# Gradio UI Contract

**Feature**: Natural Language Metrics Querying  
**Version**: 1.0  
**Date**: January 21, 2026

---

## Purpose

This contract defines the interface and behavior of the Gradio chat interface for user interaction with the metrics querying agent.

---

## Interface Overview

### Component Type
```
gr.ChatInterface
```

### Interface Purpose
Provide a simple, conversational interface for users to ask natural language questions about system metrics.

---

## Input Specification

### User Message Format

**Type**: Text string

**Constraints**:
- Non-empty (Gradio enforces)
- No maximum length (but recommend < 500 characters for clarity)
- Plain text only (no special formatting)

**Examples**:
```
"Show CPU usage for the last hour"
"What was memory usage yesterday?"
"How did request latency change over time?"
"CPU for the past 24 hours"
"Memory - last week"
```

---

## Output Specification

### Response Format

**Type**: Streamed text (yielded line-by-line)

**Format Options**:

#### Option 1: Success Response

```
[Metric Name]
═══════════════════════════════════════

Time Period: [start] to [end]
Data Points: [count]

📊 Statistics:
  Min:    [value] [unit]
  Max:    [value] [unit]
  Mean:   [value] [unit]
  Median: [value] [unit]

📈 Time-Series Data:
  [timestamp] - [value] [unit]
  [timestamp] - [value] [unit]
  [timestamp] - [value] [unit]
  ... (showing first 20 points, total: [count])
```

#### Option 2: Error Response

```
❌ Error: [error_type]

Message:
[Clear, user-friendly error description]

💡 Suggestion:
[How to fix or what to try instead]
```

#### Option 3: Empty Result

```
📭 No Data Available

Metric: [metric_name]
Time Period: [start] to [end]

No data was recorded for this metric during the specified time range.

💡 Suggestion:
Try a different time range or metric.
Available metrics: [list]
```

### Streaming Behavior

Responses are yielded progressively:

```python
async def stream_response():
    yield f"[Metric Name]\n"
    yield f"═══════════════════════════════════════\n\n"
    yield f"Time Period: {start} to {end}\n"
    yield f"Data Points: {count}\n\n"
    yield f"📊 Statistics:\n"
    yield f"  Min:    {min_val}\n"
    yield f"  Max:    {max_val}\n"
    # ... yields continue
```

**Benefits**:
- User sees response appearing in real-time
- Perceived faster response
- Better for long responses

---

## Conversational Behavior

### Single-Query Model

**Important**: Each query is processed **independently** (stateless)

```
User: "Show CPU usage for the last hour"
Agent: [Queries metrics, returns result]

User: "What about memory?"  ← NEW query, no context
Agent: [Does NOT remember "last hour", asks for clarification OR assumes reasonable default]
```

### History Display

Chat history is **displayed** for user reference but **not sent** to agent:

```
┌─────────────────────────────────────┐
│ Previous Query: "Show CPU for..."    │ ← User sees previous messages
│ Agent Response: "CPU Usage: ..."     │
├─────────────────────────────────────┤
│ New Query: "What about memory?"      │ ← Only this goes to agent
│ Agent Response: [processing...]      │
└─────────────────────────────────────┘
```

**Rationale**: Supports education goals (learn stateless agents) and minimalism (no state management).

---

## Configuration

### Launch Parameters

```python
demo = gr.ChatInterface(
    chat_with_agent,
    examples=[
        "Show CPU usage for the last hour",
        "What was memory usage yesterday?",
        "How did request latency change over time?",
        "Memory utilization for the past week",
        "Request latency - last 24 hours"
    ],
    title="Metrics Query Agent",
    description="Ask questions about your system metrics in natural language. Each query is processed independently.",
    theme=gr.themes.Soft(),
    analytics_enabled=False,
    show_progress=True
)

# Launch
demo.launch(
    server_name="0.0.0.0",
    server_port=7860,
    share=False,
    show_error=True
)
```

### Configuration via Environment Variables

```env
GRADIO_HOST=0.0.0.0
GRADIO_PORT=7860
GRADIO_SHOW_ERROR=true
```

---

## User Interaction Flow

### Flow Diagram

```
User Types Question
         │
         ▼
┌─────────────────────┐
│ Send to Agent       │
│ (single query,      │
│  no history)        │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Agent Processing    │
│ - Parse query       │
│ - Query Grafana     │
│ - Format result     │
└────────┬────────────┘
         │
         ├─ Success ──────┐
         │                │
         └─ Error ────┐   │
                      │   ▼
                      │ Stream Result
                      │ to Gradio
                      │   │
                      └───┤
                          ▼
                  Display in Chat
```

### Example Interaction Session

```
User: "Show CPU usage for the last hour"

Agent: CPU Usage
       Time: 2026-01-21 10:00:00 to 2026-01-21 11:00:00
       Data Points: 60
       
       Min:  5.2%
       Max:  45.8%
       Mean: 22.1%
       
       [time series data...]

User: "What about memory?"
      ↑ This is a NEW independent query

Agent: I need to know which time period you'd like.
       Try rephrasing like: "Show memory usage for the last hour"
       
       OR if you meant the same time period as CPU:
       "Show memory usage for the last hour"

User: "Memory for the last hour"

Agent: Memory Utilization
       Time: 2026-01-21 10:00:00 to 2026-01-21 11:00:00
       ...
```

---

## Error Handling in UI

### Client-Side Validation

Gradio provides:
- Non-empty input validation (required)
- No automatic suggestions (intentional - let agent handle)

### Display of Agent Errors

Agent returns error strings formatted for user:

```
❌ Error: metric_not_found

Message:
Metric 'disk_io' not found in Grafana

💡 Suggestion:
Available metrics: cpu_usage, memory_utilization, disk_usage, disk_read_rate, disk_write_rate
Try one of these instead.
```

### Handling of LLM Failures

If LLM cannot parse query:

```
❌ Error: parsing_error

Message:
I couldn't understand your query

💡 Suggestion:
Try phrasing it like:
- "Show [metric_name] for the [time_period]"
- Examples: "Show CPU usage for the last hour"
                "What was memory usage yesterday?"
                "Memory for the past 24 hours?"
```

### Handling of Grafana Unavailability

If Grafana is not running:

```
❌ Error: grafana_unavailable

Message:
Cannot reach the metrics system at http://localhost:3000

💡 Suggestion:
Verify Grafana is running:
  docker ps | grep grafana

If not running, start it:
  docker-compose up grafana
```

---

## User Experience Details

### Loading Indicator

Gradio shows spinner while agent is processing. No need to implement.

### Response Time

Target: < 6 seconds per query

- If exceeds 10 seconds: Display message "This is taking longer than expected..."
- If exceeds 30 seconds: Allow user to cancel

### Example Queries

Prominently display examples to guide new users:

```
"Show CPU usage for the last hour"
"What was memory usage yesterday?"
"How did request latency change over time?"
"Memory utilization for the past week"
"Request latency - last 24 hours"
```

These examples are clickable and pre-fill the input field.

---

## Responsive Design

### Desktop View

```
┌──────────────────────────────────────┐
│    Metrics Query Agent               │
│    [description]                     │
├──────────────────────────────────────┤
│ Previous Message                     │
│ Agent Response                       │
│ ─────────────────────────────────── │
│ [New user message input field]       │
│ [Examples: CPU... Memory... Latency]│
└──────────────────────────────────────┘
```

### Mobile View

Gradio handles automatically - maintains chat format on mobile.

---

## Advanced UI Features (Optional, Phase 2)

### Planned Enhancements

1. **Metric Autocomplete**
   - User starts typing metric name
   - Suggestions appear
   - User selects from list

2. **Time Range Quick Buttons**
   - "Last Hour", "Last Day", "Last Week"
   - Buttons appear after first query
   - Preset the time range

3. **Result Export**
   - Export as CSV
   - Export as JSON
   - Copy to clipboard

4. **Metric History**
   - Show list of previously queried metrics
   - Click to re-query
   - ⚠️ Does NOT persist state - just convenience

### Design Principle

All enhancements must:
- Remain stateless (no context carried between queries)
- Enhance usability without changing core behavior
- Be strictly optional (work without them)

---

## Configuration Examples

### Minimal Configuration

```python
import gradio as gr

async def chat_fn(message, history):
    # Call agent
    return agent_response

demo = gr.ChatInterface(chat_fn)
demo.launch()
```

### Full Configuration

```python
import gradio as gr
from src.agent.metrics_agent import create_agent

# Initialize agent
agent = create_agent()

async def chat_with_agent(message: str, history: List[tuple]):
    """Conversational interface to metrics agent."""
    try:
        result = await agent.ainvoke({"user_query": message})
        
        if result.get("error"):
            yield format_error(result["error"])
        else:
            # Stream formatted result
            formatted = format_result(result["result"])
            for line in formatted.split("\n"):
                yield line + "\n"
    except Exception as e:
        yield f"An error occurred: {str(e)}"

# Create interface
demo = gr.ChatInterface(
    chat_with_agent,
    examples=[
        "Show CPU usage for the last hour",
        "What was memory usage yesterday?",
        "How did request latency change over time?",
    ],
    title="Metrics Query Agent",
    description="Ask questions about system metrics in natural language.",
    theme=gr.themes.Soft(),
    show_progress=True,
)

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )
```

---

## Testing Requirements

### Functional Tests

UI must be tested for:

1. **Input Acceptance**
   - Various query formats
   - Special characters
   - Very long queries
   - Empty input (should be rejected)

2. **Output Display**
   - Success responses formatted correctly
   - Error messages displayed clearly
   - Streaming works smoothly
   - Markdown/Unicode renders correctly

3. **Conversation Flow**
   - History displays correctly
   - Multiple queries work
   - No state carries between queries

### Integration Tests

UI must be tested with:

1. **Real Agent**
   - End-to-end with actual agent
   - Error scenarios
   - Long-running queries

2. **Various Browsers**
   - Chrome, Firefox, Safari
   - Mobile browsers

---

## Accessibility

### Requirements

- Text-to-speech friendly (semantic HTML)
- Keyboard navigable (Tab through buttons)
- Color contrast > 4.5:1 (WCAG AA)
- Error messages in plain language (no codes)

### Gradio Built-in Support

Gradio provides:
- Semantic HTML
- ARIA labels
- Keyboard navigation
- High contrast themes

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-21 | Initial UI contract |
