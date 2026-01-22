"""LLM prompt templates for metrics query parsing.

This module defines the prompts used to instruct the LLM to extract
structured information from natural language queries about metrics.
"""

QUERY_PARSING_PROMPT = """You are a metrics query parser. Extract the metric name and time range from a user question.

User Question: {question}

Respond with ONLY a JSON object (no markdown, no explanations), with exactly these fields:
- metric_name: The name of the metric to query (string, lowercase with underscores)
- relative_time_range: How far back to look (string like "last 1 hour", "yesterday", "past 7 days")

Examples:
- "Show CPU usage for the last hour" -> {{"metric_name": "cpu_usage", "relative_time_range": "last 1 hour"}}
- "Memory utilization yesterday" -> {{"metric_name": "memory_usage", "relative_time_range": "yesterday"}}
- "Request latency today" -> {{"metric_name": "request_latency", "relative_time_range": "today"}}

JSON:"""

TIME_RANGE_CONVERSION_PROMPT = """You are a time range converter. Convert a relative time expression to absolute ISO datetime range.

Current Time: {current_time}
Relative Expression: {relative_expr}

Respond with ONLY a JSON object (no markdown, no explanations), with exactly these fields:
- start_time: ISO 8601 datetime string (UTC)
- end_time: ISO 8601 datetime string (UTC)

Examples:
- Current: 2026-01-21 14:30:00 UTC, Expression: "last 1 hour" -> {{"start_time": "2026-01-21T13:30:00Z", "end_time": "2026-01-21T14:30:00Z"}}
- Current: 2026-01-21 14:30:00 UTC, Expression: "today" -> {{"start_time": "2026-01-21T00:00:00Z", "end_time": "2026-01-21T23:59:59Z"}}
- Current: 2026-01-21 14:30:00 UTC, Expression: "yesterday" -> {{"start_time": "2026-01-20T00:00:00Z", "end_time": "2026-01-20T23:59:59Z"}}
- Current: 2026-01-21 14:30:00 UTC, Expression: "past 7 days" -> {{"start_time": "2026-01-14T14:30:00Z", "end_time": "2026-01-21T14:30:00Z"}}

JSON:"""

QUERY_INTENT_MATCHING_PROMPT = """You are a metrics query intent matcher. Handle variations of metric names and normalize them.

Known metrics (with aliases):
- cpu_usage: ["cpu", "cpu usage", "cpu load", "cpu utilization", "processor usage"]
- memory_usage: ["memory", "memory usage", "memory utilization", "RAM", "ram usage"]
- request_latency: ["latency", "request latency", "response time", "lag"]
- disk_usage: ["disk", "disk usage", "disk space", "storage"]
- network_throughput: ["network", "throughput", "bandwidth", "network traffic"]

User Question: {question}

Extract the user's intent and respond with ONLY a JSON object (no markdown, no explanations):
- metric_name: Canonical metric name from the list above (string, lowercase with underscores)
- relative_time_range: How far back to look (string like "last 1 hour", "yesterday", "past 7 days")

Examples:
- "What's the CPU doing?" -> {{"metric_name": "cpu_usage", "relative_time_range": "last 1 hour"}}
- "Show me RAM usage for the past day" -> {{"metric_name": "memory_usage", "relative_time_range": "past 24 hours"}}
- "How's the network looking?" -> {{"metric_name": "network_throughput", "relative_time_range": "last 1 hour"}}

JSON:"""
