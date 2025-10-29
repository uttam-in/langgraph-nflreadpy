"""
Query Parser Node for NFL Player Performance Chatbot.

This module implements the Query Parser Node that converts natural language
questions into structured queries using OpenAI function calling.

Requirements addressed:
- 6.1: Extract player names, statistical categories, and time periods
- 6.2: Convert natural language queries into structured filters
- 6.3: Select most likely interpretation based on context
- 6.4: Handle common variations in player name spelling and team references
- 6.5: Request clarification for ambiguous queries
"""

from typing import Any, Dict, List, Optional
import json
import re
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from models.models import ChatbotState
from error_handler import ChatbotError, ErrorType, log_error


# Define structured output schema for parsed queries
class TimePeriod(BaseModel):
    """Time period specification for the query."""
    season: Optional[int] = Field(None, description="NFL season year (e.g., 2023)")
    start_week: Optional[int] = Field(None, description="Starting week number (1-18)")
    end_week: Optional[int] = Field(None, description="Ending week number (1-18)")
    specific_weeks: Optional[List[int]] = Field(None, description="Specific week numbers")
    career: bool = Field(False, description="Whether to query career statistics")


class QueryFilters(BaseModel):
    """Additional filters for the query."""
    situation: Optional[str] = Field(None, description="Game situation (e.g., 'under_pressure', 'red_zone')")
    opponent: Optional[str] = Field(None, description="Opponent team")
    home_away: Optional[str] = Field(None, description="'home', 'away', or None")
    min_value: Optional[float] = Field(None, description="Minimum value for statistics")
    max_value: Optional[float] = Field(None, description="Maximum value for statistics")


class ParsedQuery(BaseModel):
    """Structured representation of a parsed user query."""
    players: List[str] = Field(default_factory=list, description="List of player names mentioned")
    teams: List[str] = Field(default_factory=list, description="List of team names mentioned")
    statistics: List[str] = Field(
        default_factory=list,
        description="Statistical categories requested (e.g., 'passing_yards', 'touchdowns', 'completion_rate')"
    )
    time_period: TimePeriod = Field(default_factory=TimePeriod, description="Time period for the query")
    filters: QueryFilters = Field(default_factory=QueryFilters, description="Additional query filters")
    comparison: bool = Field(False, description="Whether this is a comparison query")
    aggregation: Optional[str] = Field(None, description="Aggregation type: 'sum', 'average', 'max', 'min'")
    needs_clarification: bool = Field(False, description="Whether the query is ambiguous and needs clarification")
    clarification_question: Optional[str] = Field(None, description="Question to ask user for clarification")
    query_intent: str = Field(
        default="player_stats",
        description="Intent: 'player_stats', 'comparison', 'ranking', 'trend_analysis'"
    )


# Mapping of common stat name variations to standardized names
STAT_MAPPINGS = {
    # Passing stats
    "passing yards": "passing_yards",
    "pass yards": "passing_yards",
    "yards": "passing_yards",  # Default to passing if ambiguous
    "completions": "completions",
    "attempts": "attempts",
    "completion percentage": "completion_rate",
    "completion rate": "completion_rate",
    "comp %": "completion_rate",
    "touchdowns": "passing_touchdowns",
    "tds": "passing_touchdowns",
    "passing tds": "passing_touchdowns",
    "interceptions": "interceptions",
    "ints": "interceptions",
    "picks": "interceptions",
    "sacks": "sacks",
    "yards per attempt": "yards_per_attempt",
    "ypa": "yards_per_attempt",
    
    # Rushing stats
    "rushing yards": "rushing_yards",
    "rush yards": "rushing_yards",
    "carries": "rushing_attempts",
    "rushing attempts": "rushing_attempts",
    "rushing touchdowns": "rushing_touchdowns",
    "rushing tds": "rushing_touchdowns",
    "yards per carry": "yards_per_carry",
    "ypc": "yards_per_carry",
    
    # Receiving stats
    "receiving yards": "receiving_yards",
    "rec yards": "receiving_yards",
    "receptions": "receptions",
    "catches": "receptions",
    "targets": "targets",
    "receiving touchdowns": "receiving_touchdowns",
    "receiving tds": "receiving_touchdowns",
    "yards per reception": "yards_per_reception",
    "ypr": "yards_per_reception",
    
    # Advanced metrics
    "epa": "epa",
    "expected points added": "epa",
}


# Common team name variations
TEAM_MAPPINGS = {
    "chiefs": "Kansas City Chiefs",
    "kc": "Kansas City Chiefs",
    "kansas city": "Kansas City Chiefs",
    "bills": "Buffalo Bills",
    "buffalo": "Buffalo Bills",
    "bengals": "Cincinnati Bengals",
    "cincinnati": "Cincinnati Bengals",
    "49ers": "San Francisco 49ers",
    "niners": "San Francisco 49ers",
    "san francisco": "San Francisco 49ers",
    "cowboys": "Dallas Cowboys",
    "dallas": "Dallas Cowboys",
    "eagles": "Philadelphia Eagles",
    "philadelphia": "Philadelphia Eagles",
    "philly": "Philadelphia Eagles",
    # Add more as needed
}


def normalize_stat_names(stats: List[str]) -> List[str]:
    """
    Normalize statistical category names to standardized format.
    
    Args:
        stats: List of stat names in various formats
        
    Returns:
        List of normalized stat names
    """
    normalized = []
    for stat in stats:
        stat_lower = stat.lower().strip()
        normalized_stat = STAT_MAPPINGS.get(stat_lower, stat_lower.replace(" ", "_"))
        normalized.append(normalized_stat)
    return normalized


def normalize_team_names(teams: List[str]) -> List[str]:
    """
    Normalize team names to full official names.
    
    Args:
        teams: List of team names in various formats
        
    Returns:
        List of normalized team names
    """
    normalized = []
    for team in teams:
        team_lower = team.lower().strip()
        normalized_team = TEAM_MAPPINGS.get(team_lower, team)
        normalized.append(normalized_team)
    return normalized


def extract_context_from_history(conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract relevant context from conversation history for reference resolution.
    
    Args:
        conversation_history: List of previous conversation turns
        
    Returns:
        Dictionary with recently mentioned players and statistics
    """
    context = {
        "recent_players": [],
        "recent_stats": [],
        "recent_teams": []
    }
    
    # Look at last 3 turns for context
    recent_turns = conversation_history[-3:] if len(conversation_history) >= 3 else conversation_history
    
    for turn in recent_turns:
        if "mentioned_players" in turn:
            context["recent_players"].extend(turn["mentioned_players"])
        if "mentioned_stats" in turn:
            context["recent_stats"].extend(turn["mentioned_stats"])
    
    # Remove duplicates while preserving order
    context["recent_players"] = list(dict.fromkeys(context["recent_players"]))
    context["recent_stats"] = list(dict.fromkeys(context["recent_stats"]))
    
    return context


def build_parsing_prompt(user_query: str, context: Dict[str, Any]) -> str:
    """
    Build the system prompt for query parsing with context.
    
    Args:
        user_query: The user's natural language query
        context: Context from conversation history
        
    Returns:
        Formatted prompt string
    """
    current_year = datetime.now().year
    current_season = current_year if datetime.now().month >= 9 else current_year - 1
    
    prompt = f"""You are a query parser for an NFL statistics chatbot. Your job is to extract structured information from natural language queries about NFL player statistics.

Current NFL Season: {current_season}

Parse the following user query and extract:
1. Player names (handle spelling variations)
2. Team names
3. Statistical categories (passing_yards, touchdowns, completion_rate, etc.)
4. Time period (season, weeks, or career)
5. Any filters or conditions
6. Whether this is a comparison between players
7. The query intent (player_stats, comparison, ranking, trend_analysis)

IMPORTANT CONTEXT RESOLUTION:
- If the query uses pronouns (he, his, him, they) or references like "that player", "same stat", resolve them using the conversation context below.
- If the query says "compare them" or "how about", it likely refers to previously mentioned players.
"""

    if context["recent_players"]:
        prompt += f"\n\nRecently mentioned players: {', '.join(context['recent_players'])}"
    
    if context["recent_stats"]:
        prompt += f"\nRecently mentioned statistics: {', '.join(context['recent_stats'])}"
    
    prompt += f"""

AMBIGUITY HANDLING:
- If the query is ambiguous (e.g., multiple players with similar names, unclear time period), set needs_clarification=True
- Provide a specific clarification_question to ask the user
- If you can make a reasonable assumption based on context, do so and set needs_clarification=False

STATISTICAL CATEGORIES:
Common stats include: passing_yards, rushing_yards, receiving_yards, touchdowns, completions, attempts, 
completion_rate, interceptions, receptions, targets, yards_per_attempt, yards_per_reception, epa

User Query: {user_query}
"""
    
    return prompt


async def parse_query(state: ChatbotState) -> ChatbotState:
    """
    Parse natural language query into structured format using OpenAI function calling.
    
    This is the main entry point for the Query Parser Node in the LangGraph workflow.
    
    Args:
        state: Current chatbot state containing user query and conversation history
        
    Returns:
        Updated state with parsed_query field populated
        
    Requirements:
        - 6.1: Extracts player names, statistical categories, and time periods
        - 6.2: Converts to structured filters for Retriever Node
        - 6.3: Uses context to select most likely interpretation
        - 6.4: Handles player name and team variations
        - 6.5: Requests clarification for ambiguous queries
    """
    try:
        user_query = state.get("user_query", "")
        conversation_history = state.get("conversation_history", [])
        
        # Extract context from conversation history
        context = extract_context_from_history(conversation_history)
        
        # Build prompt with context
        system_prompt = build_parsing_prompt(user_query, context)
        
        # Initialize OpenAI with structured output
        llm = ChatOpenAI(
            model="gpt-4",
            temperature=0,  # Deterministic parsing
        )
        
        # Use structured output with Pydantic model
        structured_llm = llm.with_structured_output(ParsedQuery)
        
        # Create messages
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_query)
        ]
        
        # Parse the query
        parsed_result: ParsedQuery = structured_llm.invoke(messages)
        
        # Normalize stat names and team names
        parsed_result.statistics = normalize_stat_names(parsed_result.statistics)
        parsed_result.teams = normalize_team_names(parsed_result.teams)
        
        # Convert to dictionary for state
        parsed_query_dict = parsed_result.model_dump()
        
        # Store parsed query in state
        state["parsed_query"] = parsed_query_dict
        
        # If clarification is needed, set error to signal workflow
        if parsed_result.needs_clarification:
            state["error"] = "clarification_needed"
            state["generated_response"] = parsed_result.clarification_question or \
                "I need more information to answer your question. Could you please clarify?"
        
        return state
        
    except Exception as e:
        # Handle parsing errors
        log_error(
            e,
            context={"user_query": user_query[:100]},
            level="warning"
        )
        
        raise ChatbotError(
            error_type=ErrorType.QUERY_PARSING_ERROR,
            message=f"Failed to parse query: {str(e)}",
            details={"user_query": user_query[:200]},
            recoverable=True
        )


# Synchronous version for non-async contexts
def parse_query_sync(state: ChatbotState) -> ChatbotState:
    """
    Synchronous version of parse_query for compatibility.
    
    Args:
        state: Current chatbot state
        
    Returns:
        Updated state with parsed query
    """
    import asyncio
    
    # Run async function in sync context
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(parse_query(state))
