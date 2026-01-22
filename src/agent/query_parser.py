"""Query parsing utilities for natural language metrics questions.

Orchestrates LLM calls to extract metric names and time ranges from
natural language user questions, converting relative time expressions
to absolute datetime ranges.
"""

import json
from datetime import datetime, timedelta
from typing import Optional

from src.models import MetricsQuery, TimeRange, QueryError
from src.agent.prompts import QUERY_PARSING_PROMPT, TIME_RANGE_CONVERSION_PROMPT


class QueryParsingError(Exception):
    """Raised when query parsing fails (will be converted to QueryError by agent)."""
    pass


def parse_user_question(question: str, llm) -> MetricsQuery:
    """
    Parse a natural language question into a MetricsQuery.
    
    Orchestrates two LLM calls:
    1. Extract metric_name and relative_time_range from question
    2. Convert relative_time_range to absolute start/end datetimes
    
    Args:
        question: Natural language question from user
        llm: LangChain LLM instance (e.g., ChatOpenAI, Ollama)
        
    Returns:
        MetricsQuery with parsed metric_name and time_range
        
    Raises:
        QueryParsingError: If LLM output cannot be parsed as JSON or is invalid
    """
    try:
        # Step 1: Extract metric and relative time range
        from langchain_core.prompts import PromptTemplate
        
        parse_template = PromptTemplate(
            input_variables=["question"],
            template=QUERY_PARSING_PROMPT
        )
        chain = parse_template | llm
        response = chain.invoke({"question": question})
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Extract JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON found in LLM response for query parsing")
        
        parsed_data = json.loads(response_text[json_start:json_end])
        metric_name = parsed_data.get("metric_name", "").strip()
        relative_time_range = parsed_data.get("relative_time_range", "").strip()
        
        if not metric_name:
            raise ValueError("metric_name not extracted from LLM response")
        if not relative_time_range:
            raise ValueError("relative_time_range not extracted from LLM response")
        
        # Step 2: Convert relative time range to absolute times
        time_range = convert_relative_time(relative_time_range, llm)
        
        # Create and return MetricsQuery
        return MetricsQuery(
            metric_name=metric_name,
            time_range=time_range,
            aggregation="avg",
            filters={},
            confidence=0.8
        )
    
    except json.JSONDecodeError as e:
        raise QueryParsingError(f"Failed to parse LLM response as JSON: {str(e)}")
    except ValueError as e:
        raise QueryParsingError(f"Could not extract metric information: {str(e)}")
    except Exception as e:
        raise QueryParsingError(f"Error parsing question: {str(e)}")


def convert_relative_time(relative_expr: str, llm) -> TimeRange:
    """
    Convert a relative time expression to absolute start/end datetimes.
    
    Uses LLM to interpret relative expressions like "last 1 hour",
    "yesterday", "past 7 days" and convert to ISO datetime strings,
    then parses them into a TimeRange object.
    
    Args:
        relative_expr: Relative time expression (e.g., "last 1 hour")
        llm: LangChain LLM instance
        
    Returns:
        TimeRange with absolute start_time and end_time
        
    Raises:
        QueryParsingError: If LLM output cannot be parsed or time range is invalid
    """
    try:
        from langchain_core.prompts import PromptTemplate
        
        current_time = datetime.utcnow().isoformat() + "Z"
        
        time_template = PromptTemplate(
            input_variables=["current_time", "relative_expr"],
            template=TIME_RANGE_CONVERSION_PROMPT
        )
        chain = time_template | llm
        response = chain.invoke({
            "current_time": current_time,
            "relative_expr": relative_expr
        })
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Extract JSON from response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON found in LLM response for time conversion")
        
        time_data = json.loads(response_text[json_start:json_end])
        start_str = time_data.get("start_time", "").strip()
        end_str = time_data.get("end_time", "").strip()
        
        if not start_str or not end_str:
            raise ValueError("start_time or end_time not found in LLM response")
        
        # Parse ISO datetime strings
        # Handle both 'Z' suffix and '+00:00' format
        start_str = start_str.replace('Z', '+00:00')
        end_str = end_str.replace('Z', '+00:00')
        
        start_time = datetime.fromisoformat(start_str)
        end_time = datetime.fromisoformat(end_str)
        
        return TimeRange(start_time=start_time, end_time=end_time)
    
    except json.JSONDecodeError as e:
        raise QueryParsingError(f"Failed to parse time conversion response: {str(e)}")
    except ValueError as e:
        raise QueryParsingError(f"Could not convert time range: {str(e)}")
    except Exception as e:
        raise QueryParsingError(f"Error converting time range: {str(e)}")
